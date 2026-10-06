import logging

from utils.errors import ConflictError, ForbiddenError, NotFoundError
from utils.helpers import utcnow

logger = logging.getLogger(__name__)

ADMIN_ONLY_FIELDS = ('role', 'active')


class UserService:
    def __init__(self, users, tasks):
        self.users = users
        self.tasks = tasks

    def _get_or_404(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    @staticmethod
    def _ensure_owner_or_admin(actor, user_id):
        if actor.id != user_id and not actor.is_admin():
            raise ForbiddenError('Sem permissão para acessar este usuário')

    def _ensure_email_free(self, email, user_id=None):
        existing = self.users.get_by_email(email)
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')

    def list_users(self):
        task_counts = self.tasks.count_by_user()
        result = []
        for user in self.users.list_all():
            data = user.to_dict()
            data['task_count'] = task_counts.get(user.id, (0, 0))[0]
            result.append(data)
        return result

    def get_user(self, user_id, actor):
        self._ensure_owner_or_admin(actor, user_id)
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in self.tasks.list_by_user(user_id)]
        return data

    def create_user(self, fields):
        self._ensure_email_free(fields['email'])
        user = self.users(name=fields['name'], email=fields['email'], role=fields['role'])
        user.set_password(fields['password'])
        user.save()
        logger.info('User created: id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, changes, actor):
        self._ensure_owner_or_admin(actor, user_id)
        user = self._get_or_404(user_id)
        if not actor.is_admin() and any(field in changes for field in ADMIN_ONLY_FIELDS):
            raise ForbiddenError('Apenas administradores podem alterar role ou status')
        if 'email' in changes:
            self._ensure_email_free(changes['email'], user_id)
        for field, value in changes.items():
            if field == 'password':
                user.set_password(value)
            else:
                setattr(user, field, value)
        user.save()
        logger.info('User updated: id=%s by=%s', user_id, actor.id)
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        user.delete_with_tasks()
        logger.info('User deleted: id=%s', user_id)

    def list_user_tasks(self, user_id):
        self._get_or_404(user_id)
        now = utcnow()
        return [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': str(task.created_at),
                'due_date': str(task.due_date) if task.due_date else None,
                'overdue': task.is_overdue(now),
            }
            for task in self.tasks.list_by_user(user_id)
        ]
