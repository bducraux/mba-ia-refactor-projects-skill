from flask import Blueprint


def build_user_blueprint(controller, require_admin):
    bp = Blueprint('users', __name__)
    bp.add_url_rule('/users', view_func=controller.list_users, methods=['GET'])
    bp.add_url_rule('/users', view_func=controller.create_user, methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', view_func=controller.get_user, methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', view_func=controller.update_user, methods=['PUT'])
    bp.add_url_rule(
        '/users/<int:user_id>', view_func=require_admin(controller.delete_user), methods=['DELETE']
    )
    bp.add_url_rule('/users/<int:user_id>/tasks', view_func=controller.user_tasks, methods=['GET'])
    bp.add_url_rule('/login', view_func=controller.login, methods=['POST'])
    return bp
