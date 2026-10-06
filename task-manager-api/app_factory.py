"""Composition root: config -> db -> models -> services -> controllers -> routes -> app."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import DEV_SECRET_KEY, settings as default_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.system_controller import SystemController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.auth import build_auth_guards
from middlewares.error_handler import register_error_handlers
from models import Category, Task, User
from routes.category_routes import build_category_blueprint
from routes.report_routes import build_report_blueprint
from routes.system_routes import build_system_blueprint
from routes.task_routes import build_task_blueprint
from routes.user_routes import build_user_blueprint
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.notification_service import NotificationService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService
from utils.logger import configure_logging
from utils.security import TokenSigner

logger = logging.getLogger(__name__)


def create_app(settings=default_settings):
    configure_logging(settings.LOG_LEVEL)
    if settings.SECRET_KEY == DEV_SECRET_KEY:
        logger.warning('SECRET_KEY not set; using the development default (do not use in production)')

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=settings.DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    CORS(app, origins=settings.CORS_ORIGINS)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    notifier = NotificationService(
        settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_SENDER,
    )
    auth_service = AuthService(User, TokenSigner(settings.SECRET_KEY, settings.TOKEN_MAX_AGE_SECONDS))
    task_service = TaskService(Task, User, Category, notifier)
    user_service = UserService(User, Task)
    category_service = CategoryService(Category, Task)
    report_service = ReportService(Task, User, Category)

    guards = build_auth_guards(auth_service)
    app.register_blueprint(build_system_blueprint(SystemController()))
    app.register_blueprint(build_task_blueprint(TaskController(task_service)))
    app.register_blueprint(build_user_blueprint(UserController(user_service, auth_service), guards))
    app.register_blueprint(build_report_blueprint(ReportController(report_service)))
    app.register_blueprint(build_category_blueprint(CategoryController(category_service)))

    register_error_handlers(app)
    return app
