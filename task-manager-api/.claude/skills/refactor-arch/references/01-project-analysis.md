# 01 — Project Analysis Heuristics

Use these heuristics to fill the Phase 1 block. Always confirm with file contents; never infer the stack from the folder name.

## 1. List the source files

Exclude dependency/generated folders and non-source files:

```bash
# Python
find . -name "*.py" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "./.claude/*" | sort
# JavaScript / TypeScript
find . \( -name "*.js" -o -name "*.ts" -o -name "*.mjs" -o -name "*.cjs" \) -not -path "*/node_modules/*" -not -path "*/dist/*" -not -path "./.claude/*" | sort
# Lines of code of the listed files
<same find> | xargs wc -l | tail -1
```

Report the number of files and the total lines. Count scripts that are part of the app (seed/migration scripts) and say so.

## 2. Detect language and framework

| Evidence | Language | Framework signal | Where the version is |
| --- | --- | --- | --- |
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python | `flask` → Flask; `django` → Django; `fastapi` → FastAPI | pinned version in `requirements.txt` (`flask==3.1.1`) or `pyproject.toml` |
| `package.json`, `*.js`/`*.ts` | JavaScript / TypeScript (TS if `typescript` dep or `tsconfig.json`) | `express` → Express; `@nestjs/core` → NestJS; `fastify` → Fastify; `koa` → Koa | `dependencies` in `package.json` (range, e.g. `^4.18.2`) and the resolved version in `package-lock.json` |
| `go.mod` | Go | `gin`, `echo`, `chi` | `go.mod` |
| `pom.xml` / `build.gradle` | Java/Kotlin | Spring Boot | parent/plugin version |

Confirm with imports in the code: `from flask import Flask`, `require('express')`, `import express from 'express'`.

**Dependencies:** list runtime dependencies other than the framework (e.g. ORM, CORS, DB driver, HTTP client, validation libs). Skip dev/test tooling.

## 3. Detect database and data model

| Signal | Engine / access style |
| --- | --- |
| `import sqlite3`, `sqlite3.connect(`, `require('sqlite3')`, `new sqlite3.Database(` | SQLite, raw driver |
| `':memory:'` | SQLite in-memory (data is recreated at every boot) |
| `flask_sqlalchemy`, `SQLAlchemy(`, `db.Model` | SQLAlchemy ORM |
| `SQLALCHEMY_DATABASE_URI = 'sqlite:///x.db'` | SQLite via ORM (Flask-SQLAlchemy 3 stores relative files under `instance/`) |
| `psycopg2`, `pg`, `mysql2`, `pymysql`, `mongoose`, `prisma` | PostgreSQL / MySQL / MongoDB / Prisma |

Tables/models: collect from `CREATE TABLE <name>`, `__tablename__ = '<name>'`, `class X(db.Model)`, `sequelize.define('<name>'`, schema files. Note where seed data lives (inline inserts at boot, `seed.py`, migrations).

## 4. Infer the domain

Combine route prefixes, table/model names, seed data and the README. Route and table names may be in any language — translate the concept, not the word. Typical mappings: products/orders/cart/payments → e-commerce; tickets/tasks/boards/assignees → work/task management; courses/students/enrollments → learning platform (LMS); patients/appointments → healthcare scheduling. Write one line: `<Domain> API (<main entities as named in the code>)`.

## 5. Map the current architecture

| Pattern found | Classify as |
| --- | --- |
| Routes, SQL, business rules and formatting in the same file or class (one "manager"/"app" file with everything) | **Monolithic** (God file/class) |
| Files split by technical role (`models.py`, `controllers.py`) but SQL in "models" mixed with rules, rules in controllers, no config/error layer | **Monolithic with superficial split** |
| Folders `models/`, `routes/`, `services/`, `utils/` exist but routes contain business logic/queries, services unused, no config/error modules | **Partially layered** |
| Clear config, models/repositories, services, controllers, routes, error middleware, composition root | **Layered (MVC)** |

Justify in one line (e.g. "routes and SQL mixed in `controllers.py`; no config or error layer").

## 6. Entry point, start command and port

- Python: file with `app.run(` or `if __name__ == "__main__"`; the README "how to run" section; port from `app.run(port=...)` (Flask default 5000).
- Node: `scripts.start` and `main` in `package.json`; `app.listen(<port>)`; port from config/env (Express apps usually 3000).
- Note pre-boot steps (seed scripts, migrations, `npm install`).

## 7. Endpoint inventory

Collect every route; this list is the contract to preserve in Phase 3.

| Stack | grep pattern |
| --- | --- |
| Flask | `grep -rn "@.*route(\|add_url_rule(\|Blueprint(" --include=*.py .` (resolve blueprint `url_prefix`) |
| Express | `grep -rn "\.\(get\|post\|put\|patch\|delete\)(\s*['\"]/" --include=*.js .` and `app.use('/prefix', router)` |
| FastAPI | `grep -rn "@\(app\|router\)\.\(get\|post\|put\|patch\|delete\)(" --include=*.py .` |

Also read example request files (`*.http`, Postman collections, README) for sample payloads; use them in Phase 3 validation.
