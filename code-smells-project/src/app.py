from flask import Flask
from flask_cors import CORS

from src.config.settings import settings as default_settings
from src.controllers import PedidoController, ProdutoController, SistemaController, UsuarioController
from src.database import Database, init_schema_and_seed
from src.middlewares.error_handler import register_error_handlers
from src.models import AdminModel, PedidoModel, ProdutoModel, UsuarioModel
from src.routes import build_pedido_routes, build_produto_routes, build_sistema_routes, build_usuario_routes
from src.services.admin_service import AdminService
from src.services.health_service import HealthService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.utils.logger import configurar_logging


def create_app(settings=default_settings):
    """Composition root: config → db → models → services → controllers → rotas → app."""
    configurar_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    db = Database(settings.DATABASE_PATH)
    db.init_app(app)
    init_schema_and_seed(db)

    produtos = ProdutoModel(db)
    usuarios = UsuarioModel(db)
    pedidos = PedidoModel(db)
    admin = AdminModel(db)

    produto_service = ProdutoService(produtos)
    usuario_service = UsuarioService(usuarios)
    pedido_service = PedidoService(pedidos, produtos, NotificacaoService())
    relatorio_service = RelatorioService(pedidos)
    health_service = HealthService(produtos, usuarios, pedidos)
    admin_service = AdminService(admin)

    app.register_blueprint(build_produto_routes(ProdutoController(produto_service)))
    app.register_blueprint(build_usuario_routes(UsuarioController(usuario_service)))
    app.register_blueprint(build_pedido_routes(PedidoController(pedido_service)))
    app.register_blueprint(build_sistema_routes(
        SistemaController(health_service, relatorio_service, admin_service, settings.APP_ENV),
        settings.ADMIN_TOKEN,
    ))

    register_error_handlers(app)
    return app
