from flask import jsonify, request

from validators.task_validator import validate_search_filters, validate_task_create, validate_task_update


class TaskController:
    def __init__(self, task_service):
        self.service = task_service

    def list_tasks(self):
        return jsonify(self.service.list_tasks()), 200

    def get_task(self, task_id):
        return jsonify(self.service.get_task(task_id)), 200

    def create_task(self):
        fields = validate_task_create(request.get_json())
        return jsonify(self.service.create_task(fields)), 201

    def update_task(self, task_id):
        self.service.get_task(task_id)  # 404 takes precedence over payload errors
        changes = validate_task_update(request.get_json())
        return jsonify(self.service.update_task(task_id, changes)), 200

    def delete_task(self, task_id):
        self.service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search_tasks(self):
        filters = validate_search_filters(request.args)
        return jsonify(self.service.search_tasks(filters)), 200

    def task_stats(self):
        return jsonify(self.service.stats()), 200
