# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=change-me npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

As variáveis de ambiente estão documentadas em `.env.example`. Os endpoints administrativos
(`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header `X-Admin-Token`
igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` configurado eles respondem `403`.

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── server.js        # composition root: config → db → models → services → controllers → app.listen
├── app.js           # monta o Express (rotas + middleware de erro)
├── config/          # variáveis de ambiente com defaults de desenvolvimento
├── database/        # wrapper com Promises sobre sqlite3, schema e seed
├── models/          # acesso a dados (SQL parametrizado)
├── services/        # regras de negócio (checkout, relatório, usuários, gateway de pagamento)
├── controllers/     # fluxo da requisição: valida → chama service → responde
├── validators/      # validação de entrada
├── routes/          # METHOD /path → controller
├── middlewares/     # erro centralizado, auth admin, asyncHandler
└── utils/           # constantes, erros de domínio, logger, hash de senha
```
