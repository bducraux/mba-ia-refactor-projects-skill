# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as configurações vêm de variáveis de ambiente (ou de um arquivo `.env`, carregado via python-dotenv). Veja `.env.example`. Em produção defina pelo menos `SECRET_KEY`. O modo debug fica desligado por padrão (`FLASK_DEBUG=false`).

## Arquitetura

```
app.py            # entry point (python app.py)
app_factory.py    # composition root: config → db → models → services → controllers → routes
config/           # Settings lidas do ambiente
models/           # entidades SQLAlchemy + todo o acesso a dados
services/         # regras de negócio (tasks, users, auth, reports, categories, notificações)
controllers/      # fluxo da requisição: valida → chama service → resposta JSON
routes/           # blueprints: METHOD /path → controller
validators/       # validação de entrada reutilizável
middlewares/      # tratamento central de erros e guarda de admin
utils/            # constantes, erros de domínio, helpers
```

## Autenticação

`POST /login` retorna um token assinado (expira em `TOKEN_MAX_AGE_SECONDS`). Envie-o como `Authorization: Bearer <token>` para:

- `DELETE /users/<id>` (somente admin);
- criar usuário com `role` diferente de `user` ou alterar o `role` de um usuário (somente admin).

As demais rotas continuam abertas, como na versão original. Senhas são armazenadas com `werkzeug.security` (hashes MD5 antigos não são mais aceitos: rode `python seed.py` para recriar os dados).
