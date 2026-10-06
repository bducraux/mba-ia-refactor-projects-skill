================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 2 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Insecure Password Storage and Sensitive Data Exposure
File: models/user.py:27-32, models/user.py:16-25, routes/user_routes.py:33, routes/user_routes.py:85-86, routes/user_routes.py:129, routes/user_routes.py:209, routes/user_routes.py:64, routes/user_routes.py:115
Description: Passwords are hashed with unsalted `hashlib.md5(pwd.encode()).hexdigest()` and compared by plain string equality; `User.to_dict()` includes `'password': self.password`, so the hash is returned by `GET /users/<id>`, `POST /users`, `PUT /users/<id>` and `POST /login`. Minimum password length is 4.
Impact: Anyone calling these endpoints obtains password hashes that are trivially reversible (rainbow tables for unsalted MD5), leading to account takeover (including the seeded admin `joao@email.com`/`1234`).
Recommendation: Hash with `werkzeug.security.generate_password_hash`/`check_password_hash` (transparently upgrading legacy MD5 hashes on login) (PB-10) and remove `password` from every response DTO (PB-11).

### [CRITICAL] Hardcoded Credentials and Environment Config
File: app.py:11-13, app.py:15, app.py:34, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` and DB URI `'sqlite:///tasks.db'` are literals; `app.run(debug=True, host='0.0.0.0', port=5000)` enables the Werkzeug debugger on all interfaces; `CORS(app)` allows any origin; SMTP account `'taskmanager@gmail.com'` / `'senha123'` is hardcoded in `NotificationService`.
Impact: Secrets leak through the source repository; debug mode on a public interface allows remote code execution through the debugger console; config cannot vary per environment.
Recommendation: Config module reading environment variables with safe dev defaults, debug off unless set, `.env.example` (PB-01).

### [HIGH] Missing or Fake Authentication/Authorization
File: routes/user_routes.py:210, routes/user_routes.py:42, routes/user_routes.py:92, routes/user_routes.py:134, routes/user_routes.py:27
Description: `POST /login` returns a predictable token `'fake-jwt-token-' + str(user.id)` that is never verified anywhere. Sensitive routes are anonymous: `POST /users` (creates accounts with any `role`, including `'admin'`, line 52), `PUT /users/<id>` (changes anyone's `password`, `email`, `role`, `active`), `DELETE /users/<id>` (deletes any user and all their tasks), `GET /users/<id>` (returns another user's email, password hash and tasks).
Impact: Account takeover without credentials (e.g. `PUT /users/1 {"password":"x"}` then log in as admin), privilege escalation, account deletion and private-data disclosure.
Recommendation: Issue a signed token (`itsdangerous` with SECRET_KEY, already shipped with Flask) and add a `@require_auth` decorator on every listed route, with an ownership rule (self or admin) and admin-only for role changes, account creation with a role and deletions (PB-12).

### [HIGH] Business Logic in Controllers/Routes (Fat Controllers)
File: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:42-90, routes/user_routes.py:92-132, routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/report_routes.py:157-223
Description: Route handlers do validation, existence checks, string/date parsing, tag normalization, persistence, logging and response formatting; report routes compute all aggregations (status/priority counts, overdue list, per-user productivity) inline; category CRUD lives in `report_routes.py`. `services/` only contains an unused `NotificationService`.
Impact: 50–90-line handlers that cannot be unit-tested without HTTP; rules re-implemented in different handlers drift apart; mixed responsibilities.
Recommendation: Move rules to `TaskService`, `UserService`, `CategoryService`, `ReportService`; controllers only parse/validate/call/respond; routes only map; categories get their own controller/routes (PB-03).

### [HIGH] Tight Coupling Without Dependency Injection
File: app.py:9-31, seed.py:2, services/notification_service.py:5-10, services/notification_service.py:15, services/notification_service.py:6, services/notification_service.py:31, routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5
Description: The app, its config, extensions and `db.create_all()` are built as import side effects of `app.py`; `seed.py` imports that module-level `app`; `NotificationService` builds `smtplib.SMTP(...)` inside a method from hardcoded settings and keeps an in-memory `self.notifications` list; every route module imports the global `db` and concrete models directly.
Impact: No composition root: the app cannot be created with a different config (tests/production), infrastructure cannot be replaced or mocked, in-memory state is lost/not shared across workers.
Recommendation: App factory (`create_app(config)`) as composition root wiring config → db → services → controllers → blueprints; `app.py` as thin bootstrap; inject SMTP settings from config (PB-05, PB-07).

### [HIGH] Deprecated API: hashlib.md5 for passwords
File: models/user.py:29, models/user.py:32
Description: Password hashing uses `hashlib.md5`, a fast unsalted hash obsolete for credentials.
Impact: Passwords can be brute-forced or looked up in rainbow tables (security-relevant → HIGH).
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash` (PB-10).

### [MEDIUM] N+1 Queries
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:53-68, routes/report_routes.py:159-164, routes/report_routes.py:15-28, routes/task_routes.py:275-281
Description: `GET /tasks` runs `User.query.get` and `Category.query.get` per task; `GET /users` lazy-loads `len(u.tasks)` per user; summary report runs `Task.query.filter_by(user_id=u.id).all()` per user; `GET /categories` runs `Task.query.filter_by(category_id=c.id).count()` per category; summary/stats issue 9 and 5 separate `count()` queries plus a full table scan.
Impact: Query count grows linearly with data; slow list/report endpoints as data grows.
Recommendation: Eager loading (`selectinload`/`joinedload`) and `GROUP BY` aggregate queries inside the model/repository (PB-08).

### [MEDIUM] Missing or Inconsistent Input Validation
File: routes/task_routes.py:113, routes/task_routes.py:166-170, routes/task_routes.py:182, routes/task_routes.py:260-264, routes/user_routes.py:102-103, routes/user_routes.py:114-125, routes/report_routes.py:196-202, routes/report_routes.py:173-180
Description: `priority < 1` raises TypeError when priority is a string; `len(data['title'])` crashes on null; `int(request.args['priority'])`/`int(user_id)` raise ValueError → 500; `PUT /categories/<id>` does `'name' in data` with `data` possibly `None`; user `name` can be set empty, `active` is not type-checked; category `color` never validated although `is_valid_color` exists.
Impact: Malformed input produces 500s instead of 400s and invalid data is persisted.
Recommendation: Validators module reused by controllers raising `ValidationError` → 400 (PB-06).

### [MEDIUM] Scattered Error Handling
File: routes/task_routes.py:62-63, routes/task_routes.py:137-138, routes/task_routes.py:151-154, routes/task_routes.py:204-205, routes/task_routes.py:221-223, routes/task_routes.py:236-238, routes/user_routes.py:87-90, routes/user_routes.py:130-132, routes/user_routes.py:149-151, routes/report_routes.py:186-188, routes/report_routes.py:207-209, routes/report_routes.py:221-223
Description: Bare `except:` and `except Exception as e: print(str(e))` blocks are copied into every handler, each building its own `{'error': ...}, 500`; some handlers have none; no app-level error handler (unhandled errors return Flask HTML pages).
Impact: Swallowed errors, inconsistent error format (JSON vs HTML), duplicated code.
Recommendation: Domain error classes (`NotFoundError`, `ValidationError`, `ConflictError`…) and one registered error handler producing the existing `{'error': msg}` envelope (PB-04).

### [MEDIUM] Duplicated Logic and Unused Abstractions
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:34-36, routes/report_routes.py:132-135, models/task.py:38-60, routes/task_routes.py:17-28, routes/task_routes.py:110, routes/task_routes.py:177, routes/user_routes.py:61, routes/user_routes.py:106, routes/user_routes.py:71, routes/user_routes.py:120, utils/helpers.py:9-116, models/user.py:34-38
Description: The overdue rule is re-implemented 6 times while `Task.is_overdue()` is unused; `GET /tasks` hand-builds a dict duplicating `Task.to_dict()`; status list, role list and email regex are copied inline; `validate_status`, `validate_priority`, `is_admin` are never called; all of `utils/helpers.py` (`process_task_data`, `validate_email`, `parse_date`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, constants `VALID_STATUSES`, `VALID_ROLES`…) is unused.
Impact: Rules diverge (e.g. `PUT` vs `POST` error messages already differ); dead code misleads readers.
Recommendation: Single source in model/service/validators and a constants module; delete dead helpers (PB-03, PB-06, PB-09).

### [MEDIUM] Non-Atomic Writes and Broken Data Integrity
File: routes/report_routes.py:211-223
Description: `DELETE /categories/<id>` deletes the category but leaves its tasks pointing to the removed `category_id` (SQLite does not enforce FKs here; no cascade or cleanup).
Impact: Orphaned references: tasks keep a `category_id` that no longer exists; inconsistent counts.
Recommendation: In the service, null `category_id` of affected tasks and delete the category in the same transaction (PB-13).

### [MEDIUM] Deprecated API: datetime.utcnow()
File: models/user.py:14, models/category.py:11, models/task.py:15-16, models/task.py:52, routes/task_routes.py:31, routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: `datetime.utcnow()` is deprecated since Python 3.12 (the runtime in `.venv`).
Impact: Deprecation warnings now and removal in a future version; naive datetimes are error-prone.
Recommendation: A single `utcnow()` helper based on `datetime.now(timezone.utc)` (stored naive-UTC for SQLite compatibility) and callables for column defaults.

### [MEDIUM] Deprecated API: Model.query.get()
File: routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213
Description: Legacy `Query.get()` is deprecated in SQLAlchemy 2.x / Flask-SQLAlchemy 3.x.
Impact: `LegacyAPIWarning` and future removal.
Recommendation: `db.session.get(Model, id)` inside the model/repository layer.

### [LOW] Print Logging Instead of a Logger
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41
Description: `print(f"Usuário criado: ...")`, `print(f"ERRO: {str(e)}")` etc. used as logging in application code.
Impact: No levels, no configurable output, user data mixed into stdout.
Recommendation: Standard `logging` configured once (PB-15).

### [LOW] Magic Numbers and Magic Strings
File: routes/task_routes.py:96-100, routes/task_routes.py:113, routes/task_routes.py:167-169, routes/task_routes.py:182, routes/user_routes.py:64, routes/user_routes.py:115, routes/report_routes.py:24-28, routes/report_routes.py:45, routes/report_routes.py:129, routes/report_routes.py:180, app.py:34
Description: Title limits `3`/`200`, priority range `1..5`, password minimum `4`, `7`-day window, `priority <= 2` meaning "high priority", priority→label mapping, default color `'#000000'` and port `5000` are inline literals.
Impact: Rules are hard to change consistently.
Recommendation: Named constants in one module (PB-09).

### [LOW] Unused Imports, Poor Naming and Dead Code
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, utils/helpers.py:57, routes/report_routes.py:24-28, routes/task_routes.py:141, routes/task_routes.py:210
Description: `import os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `json` (models/task.py), `os, json, sys, math, hashlib` (helpers) are unused; `existing_task` parameter unused; names like `p1`..`p5`, `t`, `u`, `c`; `type(tags) == list` type checks.
Impact: Noise and reduced readability.
Recommendation: Remove unused imports/dead code and rename while moving files (PB-03).

### [LOW] Deprecated API: legacy Query API (Model.query.filter_by)
File: routes/task_routes.py:247-266, routes/task_routes.py:275-281, routes/user_routes.py:35, routes/user_routes.py:67, routes/user_routes.py:197, routes/report_routes.py:19-30, seed.py:11-13
Description: Data access uses the legacy `Model.query.*` API scattered across route modules.
Impact: Legacy style in SQLAlchemy 2.x and queries spread outside the model layer.
Recommendation: Encapsulate queries in model/repository methods using `db.select(...)` (or consistent legacy style inside models only).

================================
Total: 17 findings
================================
