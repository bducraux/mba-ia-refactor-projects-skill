from flask import Blueprint


def build_task_blueprint(controller):
    bp = Blueprint('tasks', __name__)
    bp.add_url_rule('/tasks', view_func=controller.list_tasks, methods=['GET'])
    bp.add_url_rule('/tasks', view_func=controller.create_task, methods=['POST'])
    bp.add_url_rule('/tasks/search', view_func=controller.search_tasks, methods=['GET'])
    bp.add_url_rule('/tasks/stats', view_func=controller.task_stats, methods=['GET'])
    bp.add_url_rule('/tasks/<int:task_id>', view_func=controller.get_task, methods=['GET'])
    bp.add_url_rule('/tasks/<int:task_id>', view_func=controller.update_task, methods=['PUT'])
    bp.add_url_rule('/tasks/<int:task_id>', view_func=controller.delete_task, methods=['DELETE'])
    return bp
