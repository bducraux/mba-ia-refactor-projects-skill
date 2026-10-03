from utils.errors import NotFoundError

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryService:
    def __init__(self, category_model, task_model):
        self.categories = category_model
        self.tasks = task_model

    def _get_or_404(self, category_id):
        category = self.categories.find(category_id)
        if not category:
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category

    def list_categories(self):
        task_counts = self.tasks.count_by_category()
        result = []
        for category in self.categories.list_all():
            data = category.to_dict()
            data['task_count'] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def create_category(self, fields):
        return self.categories(**fields).save().to_dict()

    def update_category(self, category_id, changes):
        category = self._get_or_404(category_id)
        for name, value in changes.items():
            setattr(category, name, value)
        return category.save().to_dict()

    def delete_category(self, category_id):
        self._get_or_404(category_id).delete_detaching_tasks()
