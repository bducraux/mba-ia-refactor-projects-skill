from flask import Blueprint


def build_system_blueprint(controller):
    bp = Blueprint('system', __name__)
    bp.add_url_rule('/', view_func=controller.index, methods=['GET'])
    bp.add_url_rule('/health', view_func=controller.health, methods=['GET'])
    return bp
