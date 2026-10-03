================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
File: src/utils.js:1-7
Description: The `config` object hardcodes production secrets and environment config: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser: "admin_master"`, `smtpUser`, and `port: 3000`. No environment variables are read.
Impact: Anyone with access to the repository gets the live payment gateway key and the DB credentials. Secrets can't be rotated or changed per environment without a code change.
Recommendation: Add a config module that reads environment variables with safe development defaults (no real secrets), plus a `.env.example` (PB-01).

### [CRITICAL] Insecure Password Storage and Sensitive Data Exposure
File: src/utils.js:17-23, src/AppManager.js:18, src/AppManager.js:68, src/AppManager.js:45
Description: `badCrypto` "hashes" passwords by repeating the first 2 chars of `Buffer.from(pwd).toString('base64')` and truncating the result to 10 chars. That is reversible, unsalted and collides heavily. The seed inserts the plaintext password `'123'`. When `pwd` is missing, checkout silently assigns the default password `"123456"`. The checkout logs the full card number and the gateway key: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`.
Impact: Stored passwords can be recovered trivially, and accounts get a guessable default password. Card numbers (PCI data) and the live gateway key end up in the logs.
Recommendation: Use secure hashing with `crypto.scrypt` and a random salt (PB-10). Never log card data or secrets, and mask the card if anything must be logged (PB-11).

### [CRITICAL] Unprotected Dangerous Endpoints
File: src/AppManager.js:80-129, src/AppManager.js:131-137
Description: `GET /api/admin/financial-report` returns every student's name and amount paid with no auth check. `DELETE /api/users/:id` deletes any user without authentication or authorization.
Impact: Anyone can read other customers' financial data and delete any account.
Recommendation: Require an admin token from config (e.g. an `X-Admin-Token` header) on both routes. List this as an intentional contract change (PB-12).

### [CRITICAL] God Class / God File
File: src/AppManager.js:4-139
Description: `AppManager` opens the SQLite connection (:7), creates the schema and seeds (`initDb`, :10-23), declares every route (`setupRoutes`, :25-138) and holds all business rules: payment approval, user creation, enrollment, audit, and the revenue aggregation for the report.
Impact: Every change touches the same class. You can't test or reuse data access, rules or HTTP handling in isolation.
Recommendation: Split into config, db, models, services, controllers and routes, wired by a composition root (PB-03, PB-05).

### [HIGH] Business Logic in Controllers (Fat Controllers)
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: The checkout handler (~50 lines) does presence validation, course lookup, find-or-create user, password hashing, the payment approval rule (`cc.startsWith("4") ? "PAID" : "DENIED"`), the enrollment insert, the payment insert, the audit insert and cache writes. The report handler computes revenue and student lists inside the route.
Impact: The business rules can't be unit-tested or reused, and HTTP concerns are mixed with domain logic.
Recommendation: Move the checkout and report rules into services and keep controllers as parse → validate → call service → respond (PB-03).

### [HIGH] Global Mutable State
File: src/utils.js:9-15, src/utils.js:25, src/AppManager.js:59
Description: Module-level `let globalCache = {}` is mutated by `logAndCache` (called from checkout at AppManager.js:59). Module-level `let totalRevenue = 0` is exported as mutable state. Both are exported from `utils`.
Impact: Hidden shared state grows without bounds (memory leak), is invisible to tests and is shared across requests.
Recommendation: Remove the unused globals. If a cache is needed, it should be an injected, scoped instance (PB-05, PB-07).

### [HIGH] Tight Coupling Without Dependency Injection
File: src/AppManager.js:7, src/app.js:8-10
Description: The `AppManager` constructor instantiates its own `new sqlite3.Database(':memory:')`. `app.js` only calls `new AppManager()`, `initDb()` and `setupRoutes(app)`, so no single place builds and injects config → db → models → controllers.
Impact: The DB can't be swapped (file DB, test DB) or the layers mocked. Config and infrastructure are bound to the class.
Recommendation: Add a composition root that creates the DB from config and injects it into models, services and controllers (PB-05).

### [MEDIUM] N+1 Queries
File: src/AppManager.js:89-127
Description: For each course (`courses.forEach`, :89), the report runs `SELECT * FROM enrollments WHERE course_id = ?` (:92). For each enrollment (:102) it then runs `SELECT ... FROM users` (:104) and `SELECT ... FROM payments` (:106).
Impact: The query count grows as 1 + C + 2E, so the report gets slower as enrollments grow.
Recommendation: Use a single LEFT JOIN query (courses ⟕ enrollments ⟕ users ⟕ payments) ordered by course and aggregate in the service (PB-08).

### [MEDIUM] Non-Atomic Writes and Broken Data Integrity
File: src/AppManager.js:50-61, src/AppManager.js:69-71, src/AppManager.js:133-135
Description: Checkout inserts the user, enrollment, payment and audit log as separate statements with no transaction. `DELETE /api/users/:id` deletes only the user row and leaves its enrollments and payments orphaned; the response text even admits it ("as matrículas e pagamentos ficaram sujos no banco").
Impact: A failure midway leaves enrollments without payments, or users without enrollments. Deleting a user corrupts the report, which then shows 'Unknown' students.
Recommendation: Wrap checkout in a transaction inside the service/model, and delete the user's payments, enrollments and user row in one transaction (PB-13).

### [MEDIUM] Scattered Error Handling
File: src/AppManager.js:35, src/AppManager.js:38, src/AppManager.js:41, src/AppManager.js:48, src/AppManager.js:51, src/AppManager.js:55, src/AppManager.js:57, src/AppManager.js:70, src/AppManager.js:84, src/AppManager.js:92, src/AppManager.js:104-106, src/AppManager.js:133-135
Description: Each callback formats its own plain-text error (`"Erro DB"`, `"Erro Matrícula"`, ...) while successes are JSON. A DB error on the course lookup is reported as 404 (:38). `err` is ignored at :57, :92, :104, :106 and :133. At :92 a DB error leaves `enrollments` undefined and `.length` throws. DELETE reports success even on error. There is no error middleware.
Impact: Behavior is inconsistent and errors are swallowed. Exceptions thrown inside sqlite callbacks bypass Express and crash the process.
Recommendation: Add domain error classes and one Express error middleware. Controllers throw/forward errors instead of formatting them (PB-04).

### [MEDIUM] Missing Input Validation
File: src/AppManager.js:29-35, src/AppManager.js:132
Description: Checkout only checks presence (`if (!u || !e || !cid || !cc)`). `card` is not checked to be a string, so a numeric `card` makes `cc.startsWith` throw inside an async callback and crash the server. `c_id` is not checked to be an integer, the email format is not validated, and `pwd` is optional. `:id` on DELETE is not validated.
Impact: Malformed input can crash the whole process (DoS) or store invalid data.
Recommendation: Add a small validation module used by the controllers. Keep the 400 "Bad Request" contract for missing fields and reject wrong types (PB-06).

### [MEDIUM] Callback Hell
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Description: Checkout nests 6 levels of callbacks (course → user → insert user → enrollment → payment → audit). The report coordinates parallel callbacks with manual counters (`coursesPending`, :86/:97/:120, and `enrPending`, :93/:117).
Impact: The code is hard to read, errors are easy to drop, and the counters are a source of race and double-response bugs.
Recommendation: Use promisified data access with `async/await` in models and services (PB-14).

### [MEDIUM] Deprecated API: sqlite3 callback-style data access
File: src/AppManager.js:37, src/AppManager.js:40, src/AppManager.js:50, src/AppManager.js:54, src/AppManager.js:57, src/AppManager.js:69, src/AppManager.js:83, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133
Description: All data access uses the callback API (`db.get/run/all(sql, params, function(err, ...))`), including `function` callbacks that rely on `this.lastID` together with a `self` alias.
Impact: This is an obsolete style that can't be used with `async/await` or try/catch error flow.
Recommendation: Wrap `run/get/all` once with Promises (`util.promisify` or a small adapter that returns `lastID`) and use `async/await` (PB-14).

### [LOW] Console Logging Instead of a Logger
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Description: `console.log` is used for payment processing, which includes card and key data, for cache writes and for startup.
Impact: There are no log levels or central control, and sensitive data is logged.
Recommendation: Add a small logger module with levels and never log sensitive data (PB-15).

### [LOW] Magic Numbers and Magic Strings
File: src/AppManager.js:46, src/AppManager.js:48, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:6, src/utils.js:19, src/utils.js:22
Description: The payment rule is `cc.startsWith("4")`. The statuses `"PAID"`/`"DENIED"` are written inline. The default password is `"123456"`, the port is the literal `3000`, and the "hash" uses `10000` iterations and a `10` char cut.
Impact: Business rules are hidden in literals and easy to change inconsistently.
Recommendation: Move them to named constants (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) and config (PB-09).

### [LOW] Poor Naming, Unused Imports and Dead Code
File: src/AppManager.js:2, src/AppManager.js:26, src/AppManager.js:29-33, src/utils.js:2-5, src/utils.js:10, src/utils.js:25
Description: Request fields use one- or two-letter names (`u`, `e`, `p`, `cid`, `cc`). `totalRevenue` is imported but never used, and in utils it is never updated. `globalCache` is exported but never imported. The `config.dbUser`, `dbPass` and `smtpUser` keys are never used. There is a `self = this` alias.
Impact: The code is harder to read, and dead code suggests features that don't exist.
Recommendation: Rename to domain names and remove unused imports, exports and config keys while splitting files (PB-03).

================================
Total: 16 findings
================================
