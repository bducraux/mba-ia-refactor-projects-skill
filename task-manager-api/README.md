# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para uma arquitetura MVC em camadas.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste SECRET_KEY etc.
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as configurações vêm de variáveis de ambiente (ou de um `.env`), com defaults seguros para desenvolvimento — veja `.env.example`. Em produção defina sempre `SECRET_KEY`.

## Autenticação

`POST /login` retorna um token assinado (`token`). Envie-o como `Authorization: Bearer <token>` nas rotas protegidas:

| Rota | Regra |
| --- | --- |
| `GET /users/<id>` | o próprio usuário ou admin |
| `PUT /users/<id>` | o próprio usuário ou admin; `role` e `active` só admin |
| `POST /users` | apenas admin |
| `DELETE /users/<id>` | apenas admin |

Sem token → `401`; token de outro usuário sem permissão → `403`.

## Estrutura

```
app.py              # entry point (python app.py)
app_factory.py      # create_app(): composition root
config/             # settings a partir de variáveis de ambiente
models/             # entidades SQLAlchemy + todo o acesso a dados
services/           # regras de negócio (tasks, users, auth, categories, reports, notificações)
controllers/        # fluxo da requisição: valida -> chama service -> resposta
routes/             # blueprints: METHOD /path -> controller
validators/         # validação de entrada
middlewares/        # auth (Bearer token) e tratamento centralizado de erros
utils/              # constantes, erros de domínio, segurança, logger, helpers
seed.py             # dados iniciais
```
