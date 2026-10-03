from datetime import timedelta

from utils.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage


class ReportService:
    def __init__(self, task_model, user_model, category_model, clock):
        self.tasks = task_model
        self.users = user_model
        self.categories = category_model
        self.clock = clock

    def summary(self):
        now = self.clock()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()
        overdue_tasks = self.tasks.list_overdue(now)
        counts_by_user = self.tasks.count_by_user()

        user_productivity = []
        for user in self.users.list_all():
            total, completed = counts_by_user.get(user.id, (0, 0))
            user_productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self.tasks.count_all(),
                'total_users': self.users.count_all(),
                'total_categories': self.categories.count_all(),
            },
            'tasks_by_status': {
                status: by_status.get(status, 0)
                for status in (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
            },
            'tasks_by_priority': {
                label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self.tasks.count_created_since(since),
                'tasks_completed_last_7_days': self.tasks.count_completed_since(since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id):
        user = self.users.find(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        now = self.clock()
        tasks = self.tasks.find_by_user(user_id)
        by_status = {status: 0 for status in (STATUS_DONE, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_CANCELLED)}
        for task in tasks:
            if task.status in by_status:
                by_status[task.status] += 1

        total = len(tasks)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': by_status[STATUS_DONE],
                'pending': by_status[STATUS_PENDING],
                'in_progress': by_status[STATUS_IN_PROGRESS],
                'cancelled': by_status[STATUS_CANCELLED],
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
            },
        }
