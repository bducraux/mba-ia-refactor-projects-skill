# 02 — Anti-Patterns Catalog

Severity scale (use exactly these definitions):

- **CRITICAL** — serious architecture or security failure: exposes sensitive data or allows takeover (hardcoded credentials, SQL injection, unauthenticated arbitrary execution, plaintext/reversible passwords) or completely violates separation of concerns (God Class/File with database + business logic + routing together).
- **HIGH** — strong MVC/SOLID violation that makes maintenance and testing very hard: heavy business logic inside controllers/routes, tight coupling without dependency injection, global mutable state, fake authentication.
- **MEDIUM** — standardization, duplication or moderate performance issue: N+1 queries, missing validation, scattered error handling, inadequate middleware use, deprecated APIs, non-atomic writes.
- **LOW** — readability: poor names, magic numbers, print-style logging, unused imports, dead code.

How to use: for each entry run the **detection signals** over the source files (`grep -n -E '<pattern>' <files>`), read the surrounding code to confirm, then report with exact lines. A signal alone is not a finding — confirm it in context.

---

### AP-01 Hardcoded credentials, secrets and environment config — CRITICAL

**Detection signals**
- Literals assigned to secret-like names: `grep -n -i -E "(secret|password|passwd|pass|pwd|token|api_?key|private|gateway|smtp).*[=:]\s*['\"][^'\"]+['\"]"`.
- Framework secret set in code: `SECRET_KEY\s*=\s*['\"]`, `app.config\[['\"]SECRET_KEY['\"]\]\s*=`.
- Debug/production flags fixed in code: `debug=True`, `DEBUG\s*=\s*True`, `"debug": True`.
- Connection strings with credentials: `://[^:/]+:[^@]+@`.
- Secrets or internal config echoed back by any endpoint (status/diagnostic routes returning keys, flags or file paths).

**Example (Python)** `app.config["SECRET_KEY"] = "my-secret-123"` · **(JS)** `const config = { dbPass: "prod_pass", paymentKey: "pk_live_..." }`

**Recommendation:** PB-01 (config module + environment variables + `.env.example`).

---

### AP-02 SQL injection (queries built from strings) — CRITICAL

**Detection signals**
- Concatenation or interpolation inside SQL: `grep -n -E "(SELECT|INSERT|UPDATE|DELETE).*(\" *\+|' *\+|\+ *str\(|f\"|f'|%s\"? *%|\\\$\{)"`.
- `execute(` / `.run(` / `.get(` / `.all(` / `.query(` whose first argument is a variable built earlier (`query += " AND ..."`).
- Search filters assembled with `LIKE '%" + term + "%'`.

**Example (Python)** `cursor.execute("SELECT * FROM accounts WHERE login = '" + login + "'")` · **(JS)** ``db.all(`SELECT * FROM users WHERE id = ${req.params.id}`)``

**Recommendation:** PB-02 (parameterized queries inside the model/repository).

---

### AP-03 God file / God class — CRITICAL

**Detection signals**
- One file or class that simultaneously opens the DB connection or defines schema, declares routes, and contains business rules (`CREATE TABLE` + `app.get(`/`@app.route` + calculations in the same unit).
- A "manager"/"utils"/"models" module that handles several unrelated domains (users + orders + products + reports) — e.g. > ~300 lines or > ~4 domains in one file.
- Classes with methods like `initDb()` and `setupRoutes()` together.

**Example (JS)** `class Server { createSchema() {...CREATE TABLE...}  registerRoutes(app) { app.post('/purchase', ...business rules... ) } }`
**Example (Python)** a single data module with SQL for several domains plus pricing rules and response formatting.

**Recommendation:** PB-03 (split into config, models, services, controllers, routes) and PB-05 (composition root).

---

### AP-04 Unprotected dangerous endpoints — CRITICAL

**Detection signals**
- Endpoint that executes SQL/code received in the request: `execute\(\s*(query|sql|dados|data|req\.body)`, `eval(`, `exec(`, `child_process`, `subprocess` with request data.
- Destructive admin routes (`/admin/*`, `reset`, `drop`, `DELETE FROM` without `WHERE`) with no auth/role check.
- Admin/financial reports exposing other users' data with no authorization.

**Example (Python)** `@app.route("/debug/sql", methods=["POST"]) ... cursor.execute(request.json["statement"])`

**Recommendation:** PB-12 (protect with an admin credential from config, or disable by default). Never delete the route silently — list the change as an intentional contract change.

---

### AP-05 Insecure password storage and sensitive data exposure — CRITICAL

**Detection signals**
- Passwords stored or compared in plaintext: `senha|password|pass` inserted/compared without a hash function; seeds with literal passwords inserted as-is.
- Weak or fake hashing: `md5(`, `sha1(`, `hashlib.md5`, `createHash('md5')`, base64 used as "hash" (`toString('base64')`), custom loops.
- Serializers/`to_dict()`/`SELECT *` responses that include `password`/`senha`/hash fields.
- Secrets or card data in logs: `print(`/`console.log(` with `card`, `cc`, `password`, `token`, `key`.

**Example (Python)** `self.pw = hashlib.md5(raw.encode()).hexdigest()` · **(JS)** `console.log(\`charging ${cardNumber} using ${config.apiKey}\`)`

**Recommendation:** PB-10 (secure password hashing) and PB-11 (response DTO without sensitive fields; never log secrets).

---

### AP-06 Business logic in controllers/routes (fat controllers) — HIGH

**Detection signals**
- Route handlers longer than ~30 lines, or containing calculations, multi-step workflows, loops over query results, status machines, notification side effects.
- Validation + persistence + formatting + side effects in the same handler.
- A `services/` folder that exists but is not imported by routes.

**Example (JS)** an approval rule like `amount > LIMIT ? "REJECTED" : "APPROVED"` plus inserts and notifications inside `app.post('/purchase')`.
**Example (Python)** tiered pricing/discount rules and aggregation loops inside a route or a data-access function.

**Recommendation:** PB-03 (move rules to a service, controller only orchestrates).

---

### AP-07 Global mutable state and hidden singletons — HIGH

**Detection signals**
- Module-level mutable variables written at runtime: `global <name>`, `let cache = {}` / `let total = 0` mutated by functions, lists appended to from handlers.
- Module-level DB connection reused everywhere (`db_connection = None` + `global db_connection`), `check_same_thread=False` shared connection.
- In-memory "caches" or notification lists living in module/instance state of a long-lived object.

**Example (Python)** `_conn = None; def get_conn(): global _conn ...` · **(JS)** `let cache = {}; function remember(k, v) { cache[k] = v }`

**Recommendation:** PB-05 (composition root / dependency injection) and PB-07 (scoped resources instead of globals).

---

### AP-08 Tight coupling without dependency injection — HIGH

**Detection signals**
- Handlers/services instantiating infrastructure directly (`sqlite3.connect(` / `new Database(` / `smtplib.SMTP(` / `new Service()` inside functions).
- Modules importing the concrete DB module everywhere (`from database import get_db` in controllers and models).
- No single place where dependencies are created and wired.

**Recommendation:** PB-05 (composition root that builds and injects dependencies).

---

### AP-09 Missing or fake authentication/authorization — HIGH

**Detection signals**
- Login returning predictable tokens (a fixed prefix + user id, the user id itself) or no token at all while protected-looking routes exist.
- Admin or "other users' data" routes with no auth check.

**Recommendation:** PB-12 (minimum: admin credential/token from config for admin routes; document what remains open). Do not invent a full auth system unless required to fix a CRITICAL finding.

---

### AP-10 N+1 queries — MEDIUM

**Detection signals**
- A query inside a loop over the result of another query: `for ... in rows:` / `.forEach(` / `.map(` followed by `execute(` / `.get(` / `.query.get(` / `.filter_by(` / `db.get(` in the loop body.
- ORM relationship access inside a loop without eager loading (`len(author.posts)` for each author).
- Counting per item in a loop (`Item.query.filter_by(parent_id=p.id).count()` inside `for p in parents`).

**Example (Python)** `for inv in invoices: cursor.execute("SELECT * FROM lines WHERE invoice_id = ?", (inv["id"],))`
**Example (JS)** `groups.forEach(g => db.all("SELECT * FROM members WHERE group_id = ?", [g.id], ...))`

**Recommendation:** PB-08 (JOIN / batch `IN (...)` / eager loading / GROUP BY).

---

### AP-11 Missing or inconsistent input validation — MEDIUM

**Detection signals**
- `request.get_json()` / `req.body` fields used without type/range checks; only presence checks (`if not x`).
- Handlers that crash on missing body (`data.get(...)` when `data` can be `None`).
- Same validation rules copied in several handlers with differences.
- Numeric parsing without error handling (`int(request.args[...])`, `float(...)`).

**Recommendation:** PB-06 (validation layer/schemas reused by controllers).

---

### AP-12 Scattered error handling — MEDIUM

**Detection signals**
- `try/except Exception as e: return jsonify({"erro": str(e)}), 500` repeated in every handler; bare `except:`; errors swallowed.
- Internal exception messages returned to clients (`str(e)`, `err.message`).
- Mixed error formats (plain text in some routes, JSON in others) and callbacks that ignore `err`.

**Recommendation:** PB-04 (centralized error handler + domain error classes).

---

### AP-13 Duplicated logic and unused abstractions — MEDIUM

**Detection signals**
- The same block (validation, row→dict mapping, a date/status rule, status lists) appearing in 3+ places.
- Helpers/constants/model methods defined but never used while the logic is re-implemented inline (`grep -rn "<helper name>"` returns only the definition).

**Recommendation:** PB-03 / PB-06 (single source in model/service/validator), PB-09 (constants).

---

### AP-14 Non-atomic writes and broken data integrity — MEDIUM

**Detection signals**
- Multi-step writes (parent row → child rows → counter/stock update → audit row) without a transaction.
- Deletes of parent rows that leave children orphaned (no cascade, no cleanup) or ignore the error and report success.
- Check-then-act on stock/balance without transaction.

**Recommendation:** PB-13 (transaction in the service/model; explicit cascade or cleanup).

---

### AP-15 Callback hell / blocking style async — MEDIUM

**Detection signals**
- 3+ levels of nested callbacks (`function(err, ...) { ... db.run(..., function(err) { ... }) }`).
- Counters to know when parallel callbacks finished (`pending--; if (pending === 0) res.json(...)`).

**Recommendation:** PB-14 (promisified data access + `async/await`).

---

### AP-16 Print/console logging instead of a logger — LOW

**Detection signals:** `print(` / `console.log(` in application code (not CLI scripts), especially with user data or fake side effects ("SENDING EMAIL ...").

**Recommendation:** PB-15 (standard logger configured once: `logging` in Python, a small logger module in Node; no sensitive data).

---

### AP-17 Magic numbers and magic strings — LOW

**Detection signals:** literal thresholds and rates in business rules (`> 5000`, `* 0.07`), status/role/category lists written inline in several places, literal ports, string prefixes used as business rules (`startsWith("X")`).

**Recommendation:** PB-09 (named constants / enums in one module).

---

### AP-18 Poor naming, unused imports and dead code — LOW

**Detection signals:** one/two-letter names for domain values (`u`, `x`, `v`, `p`), shadowing builtins (`id`, `type`, `list`), imports never used (`import os, sys, json` with no usage), unreachable or commented-out code, unused functions.

**Recommendation:** rename to domain names, remove unused imports/code while moving files (PB-03).

---

## Deprecated APIs

Report each occurrence found as a finding titled **"Deprecated API: <api>"** — severity **MEDIUM** (HIGH when the deprecated API is security-relevant, e.g. weak crypto). Always state the modern equivalent.

| Stack | Deprecated / obsolete | Detection signal | Modern equivalent |
| --- | --- | --- | --- |
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `grep -n "utcnow\|utcfromtimestamp"` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` (for ORM column defaults use a callable, e.g. `default=lambda: datetime.now(timezone.utc)`) |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (legacy Query API) | `grep -n "query.get("` | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Query` API in new code (`Model.query.filter_by(...).all()`) | `grep -n "\.query\."` | `db.session.execute(db.select(Model).filter_by(...)).scalars().all()` (acceptable to keep legacy query style if consistent; report as LOW) |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder` | grep names | app factory startup code; `app.json` provider |
| Python | `hashlib.md5/sha1` for passwords | `grep -n "md5\|sha1"` | `werkzeug.security.generate_password_hash` / `hashlib.scrypt` |
| Python | `pkg_resources`, `imp`, `distutils` | grep imports | `importlib.metadata`, `importlib`, `setuptools`/`packaging` |
| Node ≥ 10 | `new Buffer(...)` | `grep -n "new Buffer("` | `Buffer.from(...)` / `Buffer.alloc(...)` |
| Express ≥ 4.16 | separate `body-parser` for JSON/urlencoded | `grep -n "body-parser"` | `express.json()`, `express.urlencoded()` |
| Node | callback-style data access/IO where promises exist (`fs.readFile(cb)`, `sqlite3` callbacks) | nested `function(err` | `fs/promises`, `util.promisify`, `async/await` |
| Node | `request` / `request-promise` packages | `require('request')` | global `fetch` (Node ≥ 18) / `undici` |
| Node | `url.parse()`, `querystring` | grep | `new URL()`, `URLSearchParams` |
| Node | `crypto.createCipher()` | grep | `crypto.createCipheriv()` |
| Express 5 | `req.param()`, `res.send(<status number>)`, `res.json(status, body)` | grep | `req.params`/`req.query`, `res.sendStatus()`, `res.status().json()` |
