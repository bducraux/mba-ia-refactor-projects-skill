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
File: models/user.py:21, models/user.py:27-32, routes/user_routes.py:33, routes/user_routes.py:85-86, routes/user_routes.py:129, routes/user_routes.py:209
Description: Passwords are hashed with unsalted `hashlib.md5(pwd.encode()).hexdigest()`. `User.to_dict()` includes `'password': self.password`, so the hash comes back from GET /users/<id>, POST /users, PUT /users/<id> and POST /login.
Impact: Anyone who calls these endpoints gets every user's MD5 hash. Unsalted MD5 of short passwords (min. 4 characters) can be cracked almost instantly, which leads to account takeover.
Recommendation: Hash with werkzeug.security.generate_password_hash/check_password_hash (PB-10) and drop `password` from the response DTO (PB-11).

### [CRITICAL] Hardcoded Credentials and Environment Config
File: app.py:11, app.py:13, app.py:34, services/notification_service.py:7-10
Description: `SECRET_KEY = 'super-secret-key-123'`, the DB URI `'sqlite:///tasks.db'`, `debug=True, host='0.0.0.0'`, and the SMTP account `taskmanager@gmail.com` / `'senha123'` are all literals in the code. No environment variable is read, even though python-dotenv is installed.
Impact: The secrets leak with the source code. With debug=True on 0.0.0.0, anyone on the network can reach the Werkzeug interactive debugger, which allows remote code execution on any unhandled exception.
Recommendation: Add a config module that reads environment variables with safe dev defaults (debug off), plus a `.env.example` (PB-01).

### [HIGH] Business Logic in Controllers/Routes (Fat Controllers)
File: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:42-90, routes/user_routes.py:92-132, routes/user_routes.py:153-183, routes/report_routes.py:12-101, routes/report_routes.py:103-155
Description: Each handler parses input, validates it, runs queries, applies business rules (overdue logic, completion rates, per-user productivity, priority buckets), persists and serializes, all inline. summary_report alone is 90 lines. services/ only holds NotificationService, and nothing imports it.
Impact: The rules can't be reused or unit-tested without HTTP and a DB, and any change has to be repeated in several handlers.
Recommendation: Move rules into services (task/user/report/category), have controllers only orchestrate, and keep routes as plain mappings (PB-03).

### [HIGH] Tight Coupling Without Dependency Injection
File: app.py:9-31, routes/task_routes.py:2, routes/user_routes.py:2, routes/report_routes.py:2, services/notification_service.py:15, seed.py:2
Description: The Flask app is built at module import time with hardcoded config, and `db.create_all()` runs as an import side effect (app.py:30-31). Every route module imports the concrete `db` and calls `db.session` directly. NotificationService creates `smtplib.SMTP(...)` inside its method and keeps notifications in an in-memory instance list. seed.py imports the running app module.
Impact: Config, DB and the mail transport can't be swapped for tests or other environments. Importing any module boots the whole app.
Recommendation: Add an app factory / composition root that builds config → db → models/services → controllers → blueprints, and inject dependencies (PB-05, PB-07).

### [HIGH] Missing or Fake Authentication/Authorization
File: routes/user_routes.py:207-211, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/report_routes.py:103-155
Description: POST /login returns the predictable `'fake-jwt-token-' + str(user.id)`, and no route ever checks a token. Anyone can promote a user to `admin` via PUT /users/<id>, delete users together with their tasks, or read any user's report.
Impact: Tokens can be forged trivially and anyone can escalate privileges. The login gives no protection at all.
Recommendation: Issue a signed, expiring token from SECRET_KEY (itsdangerous ships with Flask) and add a reusable auth decorator. Document which routes stay open so the contract is preserved (PB-12).

### [HIGH] Deprecated API: hashlib.md5 for passwords
File: models/user.py:29, models/user.py:32
Description: Passwords are hashed and compared with `hashlib.md5`, an obsolete algorithm that is not suitable for passwords.
Impact: Hashes can be brute-forced quickly, and the plain `==` comparison is not constant-time.
Recommendation: Use `werkzeug.security.generate_password_hash` / `check_password_hash` (PB-10).

### [MEDIUM] N+1 Queries
File: routes/task_routes.py:41-57, routes/user_routes.py:14-22, routes/report_routes.py:53-68, routes/report_routes.py:159-164, routes/report_routes.py:15-30, routes/task_routes.py:275-281
Description: GET /tasks runs `User.query.get` and `Category.query.get` for every task. GET /users lazy-loads `len(u.tasks)` per user. The summary report runs `Task.query.filter_by(user_id=u.id)` per user. GET /categories runs a `count()` per category. The status and priority counts are 9-10 separate COUNT queries, plus a full table scan.
Impact: The number of queries grows with the data, so these endpoints get slower as the tables grow.
Recommendation: Use eager loading (joinedload) and GROUP BY aggregate queries in the model layer (PB-08).

### [MEDIUM] Missing or Inconsistent Input Validation
File: routes/task_routes.py:96-100, routes/task_routes.py:113, routes/task_routes.py:166-170, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/report_routes.py:196-202, routes/report_routes.py:180, routes/user_routes.py:61, routes/user_routes.py:102-103, routes/user_routes.py:124-125
Description: `priority < 1` with a string priority, `len(data['title'])` with a null or numeric title, and `int(request.args.get('priority'))` with non-numeric input all raise uncaught TypeError/ValueError → 500. PUT /categories crashes when the body is missing (`'name' in None`). Category color is never validated even though `is_valid_color` exists. PUT /users accepts an empty name and a non-boolean `active`. The two task handlers check the same rules differently from `utils.helpers.process_task_data`.
Impact: Bad input returns 500s (and, with debug on, the debugger) instead of 400s, and invalid data gets stored.
Recommendation: Add a single validation layer (validators module) reused by the controllers (PB-06).

### [MEDIUM] Scattered Error Handling
File: routes/task_routes.py:62-63, routes/task_routes.py:137, routes/task_routes.py:146-154, routes/task_routes.py:204, routes/task_routes.py:217-223, routes/task_routes.py:236-238, routes/user_routes.py:80-90, routes/user_routes.py:130-132, routes/user_routes.py:149-151, routes/report_routes.py:186-188, routes/report_routes.py:207-209, routes/report_routes.py:221-223, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88
Description: Every handler has its own `try/except` with a bare `except:` that returns a hand-written 500 JSON. GET /tasks swallows every exception. There is no `errorhandler`, so uncaught exceptions skip the JSON envelope entirely.
Impact: Errors are hidden instead of logged, responses are inconsistent, and the same boilerplate is copied everywhere.
Recommendation: Add domain error classes plus one centralized error handler that logs and returns `{'error': ...}` (PB-04).

### [MEDIUM] Duplicated Logic and Unused Abstractions
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:284-287, routes/user_routes.py:171-180, routes/report_routes.py:34-37, routes/report_routes.py:132-135, models/task.py:38-60, routes/task_routes.py:17-28, routes/task_routes.py:110, routes/task_routes.py:177, routes/user_routes.py:61, routes/user_routes.py:71, routes/user_routes.py:106, routes/user_routes.py:120, routes/task_routes.py:296, routes/report_routes.py:67, routes/report_routes.py:151, routes/report_routes.py:7, utils/helpers.py:9-116, services/notification_service.py:4-48
Description: The overdue rule is copied 6 times while `Task.is_overdue()` is never used. Task serialization is re-implemented next to `Task.to_dict()`. The status/role lists and the email regex are inline while `VALID_STATUSES`, `VALID_ROLES` and `validate_email` sit unused in helpers. The completion-rate formula appears 3 times while `calculate_percentage` is imported but never called. `process_task_data`, `validate_status`, `validate_priority`, `is_admin` and NotificationService are dead code.
Impact: The copies drift apart (date formats, error messages already differ), and a rule change has to be made in many places.
Recommendation: Keep a single source in the model/service/validators, centralize constants, and delete dead helpers (PB-03, PB-06, PB-09).

### [MEDIUM] Non-Atomic Writes and Broken Data Integrity
File: routes/report_routes.py:211-223, routes/user_routes.py:67-69
Description: DELETE /categories/<id> deletes the category but leaves its tasks pointing to a `category_id` that no longer exists (SQLite foreign keys are not enforced and there is no cleanup). User creation checks email uniqueness and then inserts, and the IntegrityError from a race ends up as a generic 500.
Impact: Tasks are left with dangling references and duplicate-email races return the wrong status.
Recommendation: Null out the tasks' `category_id` in the same transaction in the service, and map IntegrityError to a 409 (PB-13).

### [MEDIUM] Deprecated API: datetime.utcnow()
File: models/user.py:14, models/category.py:11, models/task.py:15-16, models/task.py:52, routes/task_routes.py:31, routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: `datetime.utcnow()` is used for column defaults, overdue checks and report timestamps. It has been deprecated since Python 3.12.
Impact: It emits DeprecationWarnings now and will break on removal. It also returns naive datetimes.
Recommendation: Add one `utcnow()` helper based on `datetime.now(timezone.utc)` and use callables for column defaults (it can stay naive-UTC so the stored format and JSON output don't change).

### [MEDIUM] Deprecated API: Model.query.get()
File: routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213
Description: The code uses the legacy `Query.get()`, which SQLAlchemy 2.x deprecates (LegacyAPIWarning).
Impact: It emits warnings and will stop working in a future SQLAlchemy release.
Recommendation: Use `db.session.get(Model, id)` inside the model/repository layer.

### [LOW] Print Logging Instead of a Logger
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41
Description: Application events and errors go to `print(...)`, sometimes with user names and emails.
Impact: There are no log levels, no way to configure output, and personal data ends up on stdout.
Recommendation: Use the `logging` module, configured once, and keep personal data out of the logs (PB-15).

### [LOW] Magic Numbers and Magic Strings
File: routes/task_routes.py:96-100, routes/task_routes.py:104, routes/task_routes.py:113, routes/task_routes.py:182, routes/user_routes.py:64, routes/user_routes.py:115, routes/report_routes.py:24-28, routes/report_routes.py:45, routes/report_routes.py:129, routes/report_routes.py:180, app.py:34
Description: Title limits 3/200, priority range 1-5, default priority 3, minimum password length 4, the 7-day window, the "high priority" threshold `<= 2`, the priority→label mapping (critical…minimal), the default color `'#000000'` and port 5000 are all literals.
Impact: The rules are implicit and inconsistent with the unused constants in utils/helpers.py.
Recommendation: Move them into one constants module (PB-09).

### [LOW] Deprecated API: legacy Query API (Model.query.*)
File: routes/task_routes.py:14, routes/task_routes.py:247, routes/task_routes.py:275-281, routes/user_routes.py:12, routes/user_routes.py:35, routes/user_routes.py:67, routes/user_routes.py:109, routes/user_routes.py:140, routes/user_routes.py:159, routes/user_routes.py:197, routes/report_routes.py:15-30, routes/report_routes.py:46-56, routes/report_routes.py:109, routes/report_routes.py:159, routes/report_routes.py:163
Description: Data access uses the legacy `Model.query.filter_by(...).all()/count()` style, spread across the route handlers.
Impact: It's the SQLAlchemy 1.x style, and the query logic is scattered across controllers.
Recommendation: Move data access into the models and use the 2.x `db.select(...)` style (or keep one consistent legacy style there).

### [LOW] Poor Naming, Unused Imports and Dead Code
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, requirements.txt:4-6, models/category.py:14, routes/report_routes.py:24-28
Description: `import os, sys, json`, `json, os, sys, time`, `hashlib, json`, `format_date, calculate_percentage, json`, `json`, and `os, json, sys, math, hashlib` are imported and never used. marshmallow, requests and python-dotenv are never imported. There are single-letter names (`u`, `t`, `c`, `d`) and `p1`..`p5` for counts.
Impact: Noise that hurts readability and adds unnecessary dependencies.
Recommendation: Remove unused imports, dependencies and dead code, and use domain names while moving the code (PB-03).

================================
Total: 17 findings
================================
