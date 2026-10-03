import logging

from utils.constants import DEFAULT_ROLE
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from validators.user_validator import validate_role

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'


class UserService:
    def __init__(self, user_model, task_model, clock):
        self.users = user_model
        self.tasks = task_model
        self.clock = clock

    def _get_or_404(self, user_id):
        user = self.users.find(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    @staticmethod
    def _ensure_can_assign_role(actor, current_role, new_role):
        """Only admins may grant or change roles beyond the default one."""
        if new_role == current_role:
            return
        if actor is None:
            raise UnauthorizedError('Autenticação de administrador necessária para alterar role')
        if not actor.is_admin():
            raise ForbiddenError('Apenas administradores podem alterar role')

    def list_users(self):
        task_counts = self.tasks.count_by_user()
        result = []
        for user in self.users.list_all():
            data = user.to_dict()
            data['task_count'] = task_counts.get(user.id, (0, 0))[0]
            result.append(data)
        return result

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in self.tasks.find_by_user(user_id)]
        return data

    def create_user(self, fields, actor):
        if self.users.find_by_email(fields['email']):
            raise ConflictError(EMAIL_TAKEN)
        role = validate_role(fields['role'])
        self._ensure_can_assign_role(actor, DEFAULT_ROLE, role)

        user = self.users(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        user.save()
        logger.info('User created: id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, changes, actor):
        user = self._get_or_404(user_id)
        if 'email' in changes:
            existing = self.users.find_by_email(changes['email'])
            if existing and existing.id != user_id:
                raise ConflictError(EMAIL_TAKEN)
        if 'role' in changes:
            self._ensure_can_assign_role(actor, user.role, changes['role'])

        password = changes.pop('password', None)
        for name, value in changes.items():
            setattr(user, name, value)
        if password is not None:
            user.set_password(password)
        user.save()
        logger.info('User updated: id=%s', user.id)
        return user.to_dict()

    def delete_user(self, user_id):
        self._get_or_404(user_id).delete_with_tasks()
        logger.info('User deleted: id=%s', user_id)

    def user_tasks(self, user_id):
        self._get_or_404(user_id)
        now = self.clock()
        return [task.to_summary_dict(now) for task in self.tasks.find_by_user(user_id)]
