================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] SQL Injection
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Description: Almost every query is built by string concatenation with request values, e.g. "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" in login_usuario, and "nome LIKE '%" + termo + "%'" in buscar_produtos (built with query += ...).
Impact: An attacker can bypass login (email "' OR 1=1 --"), read any table (including passwords), or change and delete data through any text field (nome, descricao, categoria, q, status).
Recommendation: Use parameterized queries ("?" placeholders) only inside the model layer (PB-02).

### [CRITICAL] Unprotected Dangerous Endpoints
File: app.py:47-57, app.py:59-78
Description: POST /admin/query runs any SQL from the request body (cursor.execute(query) at app.py:69) and POST /admin/reset-db runs "DELETE FROM" on all four tables. Neither route checks authentication.
Impact: Anyone who can reach the API can read every table, change data or wipe the database with one request.
Recommendation: Require an admin token from config (header check) and disable the routes when no token is configured. List this as an intentional contract change (PB-12).

### [CRITICAL] Hardcoded Credentials and Environment Config
File: app.py:7-8, app.py:88, controllers.py:285-289, database.py:5
Description: SECRET_KEY "minha-chave-super-secreta-123" and DEBUG=True are set in code, and app.run(..., debug=True) is fixed. GET /health returns the secret_key, db_path, debug flag and "ambiente": "producao". The DB path "loja.db" is hardcoded.
Impact: The session-signing secret is public (in the repo and in the API). Debug mode exposes the Werkzeug interactive debugger, which allows remote code execution. Config cannot change per environment.
Recommendation: Add a config module that reads environment variables with safe dev defaults, plus .env.example. Stop echoing secrets in /health (PB-01).

### [CRITICAL] Insecure Password Storage and Sensitive Data Exposure
File: database.py:75-83, models.py:126-129, models.py:109-111, models.py:79-86, models.py:95-102
Description: Passwords are seeded ("admin123", "123456"), stored (criar_usuario) and compared (login_usuario) in plaintext. GET /usuarios and GET /usuarios/<id> return the "senha" field of every user.
Impact: Any read access (the public user listing, SQL injection, /admin/query, a DB leak) exposes every user's password, including the admin's.
Recommendation: Hash passwords with werkzeug.security (generate_password_hash / check_password_hash), including the seeds, and serialize users without "senha" (PB-10, PB-11).

### [CRITICAL] God Class / God File
File: models.py:1-314, database.py:7-86
Description: models.py has SQL for four domains (produtos, usuarios, pedidos, relatórios), plus business rules (stock checks and total calculation at 139-146, discount tiers at 256-262) and response formatting (row→dict). database.py mixes connection management, schema DDL and seed data in a single get_db().
Impact: Any change touches one large module with mixed responsibilities. Rules cannot be tested without a real database.
Recommendation: Split into config, db, per-entity models, services, controllers and routes, wired by a composition root (PB-03, PB-05).

### [HIGH] Business Logic in Controllers/Models (Fat Controllers)
File: controllers.py:24-62, controllers.py:64-96, controllers.py:188-220, controllers.py:237-255, models.py:133-169, models.py:235-273
Description: Controllers combine validation, category rules, persistence and fake notification side effects ("ENVIANDO EMAIL/SMS/PUSH", status-change notifications). The order workflow (stock check, total, insert, stock decrement) and the tiered discount report live in the data-access module.
Impact: Business rules are spread across layers and cannot be reused or unit-tested in isolation.
Recommendation: Move rules into services (pedido_service, relatorio_service, produto validation); controllers only orchestrate (PB-03).

### [HIGH] Global Mutable State / Hidden Singleton
File: database.py:4-11
Description: A module-level db_connection is lazily set through "global db_connection" and shared by every request, with check_same_thread=False.
Impact: One sqlite connection is shared across threads without a lock (races, interleaved transactions). State is hidden and hard to replace in tests.
Recommendation: Use per-request connections opened and closed through Flask's app context (g + teardown), created from config (PB-05, PB-07).

### [HIGH] Tight Coupling Without Dependency Injection
File: app.py:4, app.py:49-55, app.py:66-76, controllers.py:3, controllers.py:266-274, models.py:1
Description: Controllers, models and app.py all import the concrete get_db and run SQL directly (health_check counts tables, and the admin routes run DELETEs in app.py). Nothing creates and wires dependencies in one place.
Impact: Layers cannot be swapped or tested in isolation. SQL leaks into routing and controller code.
Recommendation: Add a composition root (create_app) that builds config → db → models → services → controllers → routes. Keep all SQL in models (PB-05).

### [HIGH] Missing Authentication/Authorization
File: controllers.py:167-186, app.py:18-19, app.py:24-28
Description: POST /login returns user data but no token or session, so no route can be protected. User listings, all orders, order status changes and the sales report are open to anyone.
Impact: Any client can read other users' data and orders, and change order status.
Recommendation: At minimum, protect admin routes with an admin token from config and document which routes remain open. Do not invent a full auth system (PB-12).

### [MEDIUM] N+1 Queries
File: models.py:177-200, models.py:209-232, models.py:139-141, models.py:154-156
Description: For each order, the code runs one query for its items (cursor2), then one query per item for the product name (cursor3). criar_pedido also queries each product twice inside loops.
Impact: Listing N orders with M items runs 1 + N + N·M queries, so latency grows with data volume.
Recommendation: Use one query with a LEFT JOIN of itens_pedido and produtos (or a batch IN (...)), grouped in Python (PB-08).

### [MEDIUM] Missing or Inconsistent Input Validation
File: controllers.py:169-170, controllers.py:239-240, app.py:61-62, controllers.py:43-50, controllers.py:81-90, controllers.py:118-121, controllers.py:195-201
Description: request.get_json() results are used without a None check (login, status, admin/query), which raises AttributeError and returns 500. preco/estoque are not type-checked ("abc" < 0 raises TypeError → 500). Update skips the name and category rules that create enforces. float(preco_min) on bad input returns 500. Order items are not checked for produto_id/quantidade (KeyError → 500).
Impact: Malformed client input produces 500s instead of 400s, and invalid data can be stored through PUT.
Recommendation: Add a shared validation module used by controllers that raises ValidationError (→ 400) (PB-06).

### [MEDIUM] Scattered Error Handling
File: controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292, app.py:77-78, models.py:143, models.py:145
Description: Every handler repeats try/except Exception → jsonify({"erro": str(e)}), 500, which returns internal exception text. Models signal business errors by returning {"erro": ...} dicts that the controller inspects.
Impact: Internal details (SQL errors, schema) leak to clients. Error formats are inconsistent and duplicated across 17 places.
Recommendation: Use domain error classes plus one Flask error handler that keeps the {"erro": ...} envelope (PB-04).

### [MEDIUM] Duplicated Logic
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:177-200, models.py:209-232, controllers.py:28-46, controllers.py:72-90
Description: The product row→dict mapping is repeated 3 times and the user mapping 2 times. Order+items assembly is copy-pasted between get_pedidos_usuario and get_todos_pedidos. The required-field and range validation for products is copied between create and update.
Impact: Changing one copy and not the others causes inconsistent behavior.
Recommendation: Use single serializers in the models, a shared order-loading function and a shared validator (PB-03, PB-06).

### [MEDIUM] Non-Atomic Writes
File: models.py:139-168
Description: The order flow checks stock, inserts the order, inserts items and decrements stock as separate statements on a shared connection, with no explicit transaction or rollback. An exception mid-loop leaves a partial order. The stock check is separate from the decrement (check-then-act).
Impact: Concurrent orders can oversell stock, and failures can leave orders without items or with stock already reduced.
Recommendation: Wrap the workflow in one transaction (with conn: …, rollback on error) inside the model/service (PB-13).

### [LOW] Print Logging
File: controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, app.py:56, app.py:83-86
Description: print() is used for logging and for fake side effects ("ENVIANDO EMAIL", "NOTIFICAÇÃO"), including user emails on login attempts.
Impact: There are no log levels or structured output, and personal data ends up in stdout.
Recommendation: Use the standard logging module, configured once, with no sensitive data (PB-15).

### [LOW] Magic Numbers and Strings
File: models.py:257-262, controllers.py:52, controllers.py:242, models.py:247, models.py:250, models.py:253, controllers.py:285-286, app.py:35, app.py:88
Description: Discount thresholds and rates (10000/0.1, 5000/0.05, 1000/0.02), the category list, the status list, status literals in the report, the version "1.0.0" and port 5000 are all written inline.
Impact: Rules are scattered and easy to change in one place but not in another.
Recommendation: Move them into named constants in one module (PB-09).

### [LOW] Poor Naming, Unused Imports and Dead Code
File: models.py:2, database.py:2, controllers.py:14, controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:136, models.py:24, models.py:54, models.py:65, models.py:89, models.py:187, models.py:191, controllers.py:268
Description: import sqlite3 (models.py) and import os (database.py) are unused. Parameters and locals named "id" shadow the builtin. cursor2/cursor3 are meaningless names. A redundant cursor.execute("SELECT 1") runs before the real counts.
Impact: Readability suffers and the code is noisier.
Recommendation: Remove the unused imports and dead statements, and rename to domain names while moving files (PB-03).

================================
Total: 17 findings
================================
