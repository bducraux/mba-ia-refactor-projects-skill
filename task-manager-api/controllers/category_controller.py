from flask import jsonify, request

from validators.category_validator import validate_category_create, validate_category_update


class CategoryController:
    def __init__(self, category_service):
        self.service = category_service

    def list_categories(self):
        return jsonify(self.service.list_categories()), 200

    def create_category(self):
        fields = validate_category_create(request.get_json())
        return jsonify(self.service.create_category(fields)), 201

    def update_category(self, cat_id):
        changes = validate_category_update(request.get_json())
        return jsonify(self.service.update_category(cat_id, changes)), 200

    def delete_category(self, cat_id):
        self.service.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
