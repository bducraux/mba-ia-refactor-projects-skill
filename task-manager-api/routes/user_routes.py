from flask import Blueprint


def build_user_blueprint(controller, guards):
    bp = Blueprint('users', __name__)
    bp.add_url_rule('/users', 'get_users', controller.list_users, methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', 'get_user',
                    guards.require_auth(controller.get_user), methods=['GET'])
    bp.add_url_rule('/users', 'create_user',
                    guards.require_admin(controller.create_user), methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', 'update_user',
                    guards.require_auth(controller.update_user), methods=['PUT'])
    bp.add_url_rule('/users/<int:user_id>', 'delete_user',
                    guards.require_admin(controller.delete_user), methods=['DELETE'])
    bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', controller.get_user_tasks, methods=['GET'])
    bp.add_url_rule('/login', 'login', controller.login, methods=['POST'])
    return bp
