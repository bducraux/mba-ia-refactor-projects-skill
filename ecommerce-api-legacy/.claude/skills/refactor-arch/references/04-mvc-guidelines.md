# 04 — MVC Architecture Guidelines

Target: a layered MVC backend where each layer has one responsibility and dependencies point inward (routes → controllers → services → models → database). In an HTTP API the **View** is the route layer plus the JSON serialization of responses.

## Layers and rules

| Layer | Responsibility | Allowed | Forbidden |
| --- | --- | --- | --- |
| **Config** | Read settings from environment with safe dev defaults; one object/module | env vars, defaults, constants derived from env | secrets as literals, business logic |
| **Models** (data access) | Entities and all persistence: queries, ORM models, row → entity/dict mapping, transactions | parameterized SQL, ORM calls, mapping helpers | HTTP objects (`request`, `req`, `res`), response formatting, business rules beyond data invariants |
| **Services** (business rules) | Use cases: workflows, calculations, rules, side effects (notifications) orchestration | calling models, raising domain errors | SQL strings, HTTP objects, framework imports |
| **Controllers** | Request flow: read/validate input → call service → map result to HTTP status + body | validators, services, response helpers | SQL, business calculations, try/except per handler returning 500 |
| **Routes / Views** | Map `METHOD /path` → controller; mount routers/blueprints; per-route middleware (auth) | router/blueprint declarations | logic of any kind |
| **Validators / Schemas** | Validate and normalize input; one rule definition reused | pure functions or schema objects | DB access (except via an injected checker) |
| **Middlewares / Error handling** | Centralized error → HTTP mapping; auth guards; request logging | domain error classes → `{status, body}` | business logic |
| **Composition root / entry point** | Build config → db → models → services → controllers → routes → app; start server | wiring, startup, graceful shutdown | business logic |

Small projects may merge Services into Controllers only when the logic is trivial (one call + status mapping); anything with rules, loops over data or side effects goes to a service.

## Dependency rules

- Lower layers never import upper layers (models never import controllers/routes).
- Infrastructure (DB connection, mail client, payment client) is created in the composition root and **passed in** (constructor/factory argument), not imported as a global.
- Domain errors are classes (`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`) defined once and mapped to HTTP codes in the error handler, so the original status codes are preserved.
- Response envelopes and status codes stay exactly as the original API (contract preservation); move the formatting, do not change it.

## Target structure — Python / Flask

Keep the original entry file (e.g. `app.py`) as the entry point so the start command does not change.

```
<project>/
├── app.py                      # entry point: from src.app import create_app; create_app().run(...)
├── .env.example
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): composition root (config → db → models → services → controllers → blueprints → error handlers)
    ├── config/
    │   ├── __init__.py
    │   └── settings.py         # Settings from os.environ with defaults
    ├── database/               # (or db.py) connection factory / ORM init, schema + seed
    ├── models/                 # one module per entity: data access only
    ├── services/               # business rules per domain
    ├── controllers/            # one module per domain: request → service → response
    ├── routes/                 # blueprints: METHOD /path → controller
    ├── validators/             # input validation per domain
    ├── middlewares/
    │   └── error_handler.py    # register_error_handlers(app): AppError → JSON with original status
    └── utils/                  # constants, logger, security helpers
```

Flask notes:
- Use an **app factory** (`create_app()`); register blueprints there; no work at import time other than definitions.
- Errors: `@app.errorhandler(AppError)` and a fallback for `Exception` returning the original error envelope; keep 404/405 behavior.
- Per-request DB connection (`flask.g` + `teardown_appcontext`) or a connection factory injected into models, instead of a module-level global.
- If the project already has `models/`, `routes/`, `services/`, `utils/` at the root, you may keep them at the root (do not move folders just to add `src/`); add the missing `config/`, `controllers/`, `middlewares/` next to them and move logic out of routes.
- Paths for SQLite files should come from config and keep the same default file name/location used originally.

## Target structure — Node.js / Express

```
<project>/
├── package.json                # "start" keeps working (point it to the new entry if it moved)
├── .env.example
└── src/
    ├── app.js                  # buildApp(deps): express app, routes, error middleware (no listen)
    ├── server.js               # entry: load config, create db, build app, listen(config.port)
    ├── config/
    │   └── index.js            # config from process.env with defaults
    ├── database/
    │   └── index.js            # connection factory + promisified helpers + schema/seed
    ├── models/                 # one module per entity: parameterized queries, returns plain objects
    ├── services/               # business rules (billing, reports...)
    ├── controllers/            # (req, res, next) → service → res.status(...).json/send(...)
    ├── routes/                 # express.Router() per domain
    ├── middlewares/
    │   └── errorHandler.js     # (err, req, res, next) → original status/body format
    └── utils/                  # constants, logger, crypto helpers
```

Express notes:
- `express.json()` instead of `body-parser`.
- Async controllers must forward errors to the error middleware (`try/catch → next(err)` or an `asyncHandler` wrapper).
- Keep the original response types: if an endpoint answered plain text (`res.send("...")`), keep text; if it answered JSON, keep JSON with the same keys.
- Keep the same port default and the same `npm start` command.

## Already-layered projects

1. Map which layers exist and which are missing; keep the existing folder names when they already fit.
2. Move logic out of routes into controllers/services; make routes thin.
3. Reuse existing helpers/constants instead of inline copies; delete truly unused code.
4. Fix security, N+1, deprecated APIs in place.
5. Add config, centralized errors and a composition root if absent.
