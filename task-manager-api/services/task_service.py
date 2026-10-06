import logging

from utils.constants import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, tasks, users, categories, notifier):
        self.tasks = tasks
        self.users = users
        self.categories = categories
        self.notifier = notifier

    def _get_or_404(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _resolve_user(self, user_id):
        if not user_id:
            return None
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def _ensure_category(self, category_id):
        if category_id and not self.categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')

    def list_tasks(self):
        now = utcnow()
        result = []
        for task in self.tasks.list_with_relations():
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = self._get_or_404(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create_task(self, fields):
        assignee = self._resolve_user(fields['user_id'])
        self._ensure_category(fields['category_id'])
        task = self.tasks(**fields).save()
        logger.info('Task created: id=%s', task.id)
        if assignee:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, changes):
        task = self._get_or_404(task_id)
        if 'user_id' in changes:
            self._resolve_user(changes['user_id'])
        if 'category_id' in changes:
            self._ensure_category(changes['category_id'])
        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = utcnow()
        task.save()
        logger.info('Task updated: id=%s', task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        task.delete()
        logger.info('Task deleted: id=%s', task_id)

    def search_tasks(self, filters):
        return [task.to_dict() for task in self.tasks.search(**filters)]

    def stats(self):
        total = self.tasks.count()
        by_status = self.tasks.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': self.tasks.count_overdue(utcnow()),
            'completion_rate': calculate_percentage(done, total),
        }
