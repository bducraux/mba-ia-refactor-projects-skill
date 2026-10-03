from flask import Blueprint


def build_category_blueprint(controller):
    bp = Blueprint('categories', __name__)
    bp.add_url_rule('/categories', view_func=controller.list_categories, methods=['GET'])
    bp.add_url_rule('/categories', view_func=controller.create_category, methods=['POST'])
    bp.add_url_rule('/categories/<int:cat_id>', view_func=controller.update_category, methods=['PUT'])
    bp.add_url_rule('/categories/<int:cat_id>', view_func=controller.delete_category, methods=['DELETE'])
    return bp
