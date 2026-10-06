"""Script para popular o banco com dados iniciais (CLI: python seed.py)."""
from datetime import timedelta

from app_factory import create_app
from database import db, transaction
from models import Category, Task, User
from utils.helpers import utcnow

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'password': '1234', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'password': 'abcd', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'password': 'pass', 'role': 'manager'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]


def _tasks(users, categories, now):
    joao, maria, pedro = users
    backend, frontend, devops, bug = categories
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': now + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': now - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': now + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
    ]


def seed_data(app=None):
    app = app or create_app()
    with app.app_context():
        with transaction() as session:
            session.execute(db.delete(Task))
            session.execute(db.delete(User))
            session.execute(db.delete(Category))

        with transaction() as session:
            users = []
            for data in USERS:
                user = User(name=data['name'], email=data['email'], role=data['role'])
                user.set_password(data['password'])
                users.append(user)
            categories = [Category(**data) for data in CATEGORIES]
            session.add_all(users + categories)
            session.flush()
            session.add_all(Task(**data) for data in _tasks(users, categories, utcnow()))

        print('Seed concluído com sucesso!')
        print(f'  {User.count()} usuários')
        print(f'  {Category.count()} categorias')
        print(f'  {Task.count()} tasks')


if __name__ == '__main__':
    seed_data()
