from flask import jsonify, request

from middlewares.auth import bearer_token
from validators.user_validator import validate_login, validate_user_create, validate_user_update


class UserController:
    def __init__(self, user_service, auth_service):
        self.service = user_service
        self.auth = auth_service

    def list_users(self):
        return jsonify(self.service.list_users()), 200

    def get_user(self, user_id):
        return jsonify(self.service.get_user(user_id)), 200

    def create_user(self):
        fields = validate_user_create(request.get_json())
        actor = self.auth.resolve_user(bearer_token())
        return jsonify(self.service.create_user(fields, actor)), 201

    def update_user(self, user_id):
        changes = validate_user_update(request.get_json())
        actor = self.auth.resolve_user(bearer_token())
        return jsonify(self.service.update_user(user_id, changes, actor)), 200

    def delete_user(self, user_id):
        self.service.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def user_tasks(self, user_id):
        return jsonify(self.service.user_tasks(user_id)), 200

    def login(self):
        credentials = validate_login(request.get_json())
        return jsonify(self.auth.login(**credentials)), 200
