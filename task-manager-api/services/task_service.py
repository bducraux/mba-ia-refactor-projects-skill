import logging

from utils.constants import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class TaskService:
    def __init__(self, task_model, user_model, category_model, notifier, clock):
        self.tasks = task_model
        self.users = user_model
        self.categories = category_model
        self.notifier = notifier
        self.clock = clock

    def _get_or_404(self, task_id):
        task = self.tasks.find(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def _ensure_user(self, user_id):
        if not user_id:
            return None
        user = self.users.find(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    def _ensure_category(self, category_id):
        if category_id and not self.categories.find(category_id):
            raise NotFoundError(CATEGORY_NOT_FOUND)

    def list_tasks(self):
        now = self.clock()
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
        data['overdue'] = task.is_overdue(self.clock())
        return data

    def create_task(self, fields):
        assignee = self._ensure_user(fields['user_id'])
        self._ensure_category(fields['category_id'])

        task = self.tasks()
        for name, value in fields.items():
            setattr(task, name, value)
        task.save()
        logger.info('Task created: id=%s', task.id)

        if assignee:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, changes):
        task = self._get_or_404(task_id)
        assignee = self._ensure_user(changes['user_id']) if 'user_id' in changes else None
        if 'category_id' in changes:
            self._ensure_category(changes['category_id'])

        previous_user_id = task.user_id
        for name, value in changes.items():
            setattr(task, name, value)
        task.updated_at = self.clock()
        task.save()
        logger.info('Task updated: id=%s', task.id)

        if assignee and assignee.id != previous_user_id:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def delete_task(self, task_id):
        self._get_or_404(task_id).delete()
        logger.info('Task deleted: id=%s', task_id)

    def search_tasks(self, filters):
        return [task.to_dict() for task in self.tasks.search(**filters)]

    def stats(self):
        by_status = self.tasks.count_by_status()
        total = self.tasks.count_all()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': self.tasks.count_overdue(self.clock()),
            'completion_rate': calculate_percentage(done, total),
        }
