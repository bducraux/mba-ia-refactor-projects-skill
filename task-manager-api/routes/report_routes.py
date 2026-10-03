from flask import Blueprint


def build_report_blueprint(controller):
    bp = Blueprint('reports', __name__)
    bp.add_url_rule('/reports/summary', view_func=controller.summary, methods=['GET'])
    bp.add_url_rule('/reports/user/<int:user_id>', view_func=controller.user_report, methods=['GET'])
    return bp
