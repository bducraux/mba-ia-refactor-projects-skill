# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Todas as configurações vêm de variáveis de ambiente (veja `.env.example`), com defaults seguros para desenvolvimento.

- As rotas `/admin/reset-db` e `/admin/query` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` configurado elas respondem `403`. `/admin/query` aceita apenas consultas `SELECT` (somente leitura).
- Senhas são armazenadas com hash (`werkzeug.security`); senhas legadas em texto puro são convertidas no boot.

## Estrutura

```
app.py              # entry point (python app.py)
src/app.py          # create_app(): composition root
src/config/         # settings via variáveis de ambiente
src/database/       # conexão por requisição, schema e seed
src/models/         # acesso a dados (SQL parametrizado)
src/services/       # regras de negócio
src/validators/     # validação de entrada
src/controllers/    # fluxo HTTP: valida → service → resposta
src/routes/         # blueprints: METHOD /path → controller
src/middlewares/    # tratamento centralizado de erros, token de admin
src/utils/          # constantes, erros de domínio, segurança, logging
```
