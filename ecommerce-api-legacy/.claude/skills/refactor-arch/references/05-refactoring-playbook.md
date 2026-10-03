# 05 — Refactoring Playbook

Concrete transformations referenced by the catalog (`PB-xx`). Each one shows **before → after**. Adapt names to the project; keep public behavior (routes, status codes, response shapes) unchanged unless the transformation removes a vulnerability (then list it as an intentional contract change).

Recommended order in Phase 3: PB-01 config → PB-05 composition root skeleton → PB-02/PB-03 models and services → PB-04 errors → PB-06 validation → PB-08/PB-13/PB-14 data access → PB-10/PB-11/PB-12 security → PB-09/PB-15/PB-16 cleanup.

---

## PB-01 Extract configuration to environment variables

**Python — before**
```python
app.config["SECRET_KEY"] = "my-secret-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Python — after** (`src/config/settings.py`)
```python
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "app.db")   # keep the original default file name
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))                  # keep the original default port

settings = Settings()
```
```python
# app.py (entry point)
from src.app import create_app
from src.config.settings import settings

app = create_app()
if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

**JS — before**
```js
const config = { dbPass: "prod_pass_123", paymentKey: "pk_live_abc", port: 3000 };
```
**JS — after** (`src/config/index.js`)
```js
module.exports = Object.freeze({
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
});
```
Plus `.env.example` listing every variable with placeholder values. Never commit `.env`.

---

## PB-02 Parameterized queries inside the model

**Python — before**
```python
cursor.execute("SELECT * FROM items WHERE id = " + str(id))
cursor.execute("INSERT INTO items (name, price) VALUES ('" + name + "', " + str(price) + ")")
query += " AND name LIKE '%" + term + "%'"
```
**Python — after**
```python
cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (name, price))
clauses, params = [], []
if term:
    clauses.append("(name LIKE ? OR description LIKE ?)")
    params += [f"%{term}%", f"%{term}%"]
sql = "SELECT * FROM items" + (" WHERE " + " AND ".join(clauses) if clauses else "")
cursor.execute(sql, params)
```
**JS — before**
```js
db.all(`SELECT * FROM items WHERE id = ${req.params.id}`, cb);
```
**JS — after**
```js
const item = await db.get('SELECT * FROM items WHERE id = ?', [id]);
```

---

## PB-03 Split a God file / fat controller into model → service → controller → route

**Before (one function does everything)**
```python
def create_order():
    data = request.get_json()
    if not data.get("user_id"): return jsonify({"error": "user required"}), 400
    total = 0
    for it in data["items"]:
        row = db.execute("SELECT price, stock FROM products WHERE id = ?", (it["id"],)).fetchone()
        if row["stock"] < it["qty"]: return jsonify({"error": "no stock"}), 400
        total += row["price"] * it["qty"]
    db.execute("INSERT INTO orders (user_id, total) VALUES (?, ?)", (data["user_id"], total))
    print("SENDING EMAIL")
    return jsonify({"data": {"total": total}, "success": True}), 201
```
**After**
```python
# models/product_model.py
class ProductModel:
    def __init__(self, db): self.db = db
    def find_many(self, ids): ...            # one query with IN (...)

# services/order_service.py
class OrderService:
    def __init__(self, products, orders, notifier): ...
    def create(self, user_id, items):
        products = self.products.find_many([i["id"] for i in items])
        total = pricing.calculate_total(products, items)   # raises InsufficientStockError
        order_id = self.orders.create(user_id, items, total)
        self.notifier.order_created(order_id)
        return {"order_id": order_id, "total": total}

# controllers/order_controller.py
def create_order(service):
    def handler():
        payload = validate_order(request.get_json())        # raises ValidationError → 400
        return jsonify({"data": service.create(**payload), "success": True}), 201
    return handler

# routes/order_routes.py
bp.add_url_rule("/orders", view_func=controller.create_order, methods=["POST"])
```
**JS — after (same split)**
```js
// routes/orderRoutes.js
router.post('/orders', asyncHandler(orderController.create));
// controllers/orderController.js
create: async (req, res) => { const input = validateOrder(req.body); res.status(201).json(await orderService.create(input)); }
// services/orderService.js — rules; models/orderModel.js — SQL
```

---

## PB-04 Centralized error handling with domain errors

**Python — before**
```python
def get_item(id):
    try:
        ...
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```
**Python — after**
```python
# utils/errors.py
class AppError(Exception):
    status = 500
    def __init__(self, message, status=None, payload=None):
        super().__init__(message); self.message = message
        self.status = status or self.status; self.payload = payload or {}
class NotFoundError(AppError): status = 404
class ValidationError(AppError): status = 400

# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message, **err.payload}), err.status  # use the SAME envelope/key names as the original API
    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("unhandled error")
        return jsonify({"error": "Internal error"}), 500                # no internal details leaked

# controller
def get_item(item_id):
    item = service.get(item_id)            # raises NotFoundError("Item not found")
    return jsonify({"data": item, "success": True}), 200
```
**JS — after**
```js
class AppError extends Error { constructor(message, status = 500) { super(message); this.status = status; } }
// middlewares/errorHandler.js — registered last
module.exports = (err, req, res, next) => {
  const status = err.status || 500;
  if (status === 500) logger.error(err);
  // keep the original response type of the API (text or JSON)
  return err.asText ? res.status(status).send(err.message) : res.status(status).json({ error: err.message });
};
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```

---

## PB-05 Composition root and dependency injection

**Before**
```python
# every module: from database import get_db  (global connection)
```
**After**
```python
# src/app.py
def create_app(settings=settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    db = Database(settings.DATABASE_PATH)            # connection factory
    db.init_schema_and_seed()
    product_model = ProductModel(db)
    product_service = ProductService(product_model)
    app.register_blueprint(build_product_routes(ProductController(product_service)))
    register_error_handlers(app)
    return app
```
**JS — after**
```js
// src/server.js
const config = require('./config');
const db = await createDatabase(config.dbPath);
const models = { accounts: new AccountModel(db), invoices: new InvoiceModel(db) };
const services = { billing: new BillingService(models, config) };
const app = buildApp({ controllers: buildControllers(services) });
app.listen(config.port, () => logger.info(`listening on ${config.port}`));
```

---

## PB-06 Validation layer reused by controllers

**Before** — the same `if "name" not in data ... if price < 0 ...` block copied in create and update.
**After (Python)**
```python
# validators/item_validator.py
VALID_KINDS = (...)
def validate_product(data, *, partial=False):
    if not data: raise ValidationError("Invalid payload")          # keep the original messages
    for field in REQUIRED_FIELDS:
        if not partial and field not in data: raise ValidationError(f"{field} is required")
    if data.get("price", 0) < 0: raise ValidationError("price must be >= 0")
    return normalized(data)
```
**After (JS)**
```js
function validateBooking(body = {}) {
  const required = ['guestName', 'email', 'roomId', 'nights'];
  if (required.some(f => !body[f])) throw new AppError('Bad Request', 400);
  return { ...body, roomId: Number(body.roomId), nights: Number(body.nights) };
}
```
Keep the original error messages and status codes the API returned.

---

## PB-07 Replace global mutable state

**Before**
```js
let cache = {}; let total = 0;
function remember(k, v) { cache[k] = v; }
```
```python
_conn = None
def get_conn():
    global _conn
    if _conn is None: _conn = sqlite3.connect("app.db", check_same_thread=False)
    return _conn
```
**After**
```js
class CacheService { constructor() { this.store = new Map(); } set(k, v) { this.store.set(k, v); } }
// created once in the composition root and injected where needed
```
```python
class Database:
    def __init__(self, path): self.path = path
    def connect(self):
        conn = sqlite3.connect(self.path); conn.row_factory = sqlite3.Row; return conn
# Flask: open per request in flask.g, close in teardown_appcontext
```

---

## PB-08 Eliminate N+1 queries

**Python — before**
```python
for order in orders:
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
    for it in items:
        name = db.execute("SELECT name FROM products WHERE id = ?", (it["product_id"],)).fetchone()
```
**Python — after (JOIN + grouping in memory)**
```python
rows = db.execute("""
    SELECT oi.order_id, oi.product_id, oi.quantity, oi.unit_price, p.name AS product_name
    FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id
    WHERE oi.order_id IN ({})""".format(",".join("?" * len(order_ids))), order_ids).fetchall()
items_by_order = defaultdict(list)
for r in rows: items_by_order[r["order_id"]].append(to_item(r))
```
**ORM (SQLAlchemy)** — `db.session.execute(select(Post).options(joinedload(Post.author), joinedload(Post.section)))`; counts with `GROUP BY` instead of one `count()` per row.

**JS — before** `groups.forEach(g => db.all('SELECT ... WHERE group_id = ?', [g.id], ...))`
**JS — after**
```js
const rows = await db.all(`
  SELECT g.id, g.name, m.name AS member, f.amount, f.state
  FROM groups g
  LEFT JOIN memberships ms ON ms.group_id = g.id
  LEFT JOIN members m ON m.id = ms.member_id
  LEFT JOIN fees f ON f.membership_id = ms.id`);
// group rows by parent in JS, preserving the original response shape
```

---

## PB-09 Named constants instead of magic numbers/strings

**Before** `if amount > 2500: fee = amount * 0.03` · `if state not in ["open", "closed"]`
**After**
```python
FEE_TIERS = ((2_500, 0.03), (500, 0.01))   # (threshold, rate), highest first
TICKET_STATES = ("open", "in_review", "closed")
def fee_for(amount):
    return next((amount * rate for threshold, rate in FEE_TIERS if amount > threshold), 0)
```
```js
const MAX_UPLOAD_MB = 25;                 // was a bare 25 in two handlers
const INVOICE_STATUS = Object.freeze({ OPEN: 'OPEN', SETTLED: 'SETTLED' });
```

---

## PB-10 Secure password hashing

**Before**
```python
cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))   # plaintext
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function fakeHash(p) { return Buffer.from(p).toString('base64').substring(0, 10); }
```
**After**
```python
from werkzeug.security import generate_password_hash, check_password_hash   # ships with Flask
user.password = generate_password_hash(raw_password)
if not check_password_hash(user.password, raw_password): raise UnauthorizedError(...)
```
```js
const crypto = require('crypto');
function hashPassword(raw) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${salt}:${crypto.scryptSync(raw, salt, 64).toString('hex')}`;
}
function verifyPassword(raw, stored) {
  const [salt, hash] = stored.split(':');
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), crypto.scryptSync(raw, salt, 64));
}
```
Login must look the user up by email (parameterized) and verify the hash in code — never `WHERE password = ?`. Seed data must be hashed when inserted so existing logins keep working.

---

## PB-11 Response DTOs without sensitive data; no secrets in logs

**Before**
```python
def to_dict(self): return {"id": self.id, "email": self.email, "password": self.password}
```
```js
console.log(`charging ${cardNumber} using ${config.apiKey}`);
```
**After**
```python
PUBLIC_USER_FIELDS = ("id", "name", "email", "role", "created_at")
def to_public_dict(self): return {f: getattr(self, f) for f in PUBLIC_USER_FIELDS}
```
```js
logger.info('charging card', { cardLast4: cardNumber.slice(-4) });
```
Diagnostic endpoints (health/status) return only non-sensitive information. Removing a sensitive field is an intentional contract change — list it.

---

## PB-12 Protect dangerous endpoints

**Before**
```python
@app.route("/debug/sql", methods=["POST"])
def run_sql(): cursor.execute(request.json["statement"]) ...
```
**After**
```python
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)
    return wrapper

bp.add_url_rule("/debug/sql", view_func=require_admin_token(admin_controller.run_sql), methods=["POST"])
```
```js
const requireAdmin = (req, res, next) =>
  config.adminToken && req.get('X-Admin-Token') === config.adminToken ? next() : next(new AppError('Forbidden', 403));
router.get('/admin/report', requireAdmin, reportController.financial);
```
Keep the route (same path/method); when the admin credential is not configured the endpoint is disabled (403). For arbitrary-SQL endpoints additionally restrict to read-only statements. List as an intentional contract change.

---

## PB-13 Transactions and referential integrity

**Python — before** inserts of parent, children and stock updates with a single `commit()` at the end and early `return` in the middle.
**Python — after**
```python
with conn:                                   # sqlite3 context manager = transaction (commit/rollback)
    order_id = orders.insert(conn, user_id, total)
    order_items.insert_many(conn, order_id, items)
    products.decrement_stock(conn, items)
```
**JS — after**
```js
await db.exec('BEGIN');
try { /* parent row, child rows, audit row */ await db.exec('COMMIT'); }
catch (e) { await db.exec('ROLLBACK'); throw e; }
// deleting a parent: delete/cleanup children first (or ON DELETE CASCADE), and handle the error
```

---

## PB-14 Callbacks → promises and async/await

**Before**
```js
db.get(sql1, [a], (err, x) => {
  db.get(sql2, [b], (err, y) => {
    db.run(sql3, [c], function (err) { res.json({ id: this.lastID }); });
  });
});
```
**After**
```js
// database/index.js — small promisified wrapper over the callback driver
const run = (sql, p = []) => new Promise((ok, ko) => db.run(sql, p, function (e) { e ? ko(e) : ok({ lastID: this.lastID, changes: this.changes }); }));
const get = (sql, p = []) => new Promise((ok, ko) => db.get(sql, p, (e, row) => (e ? ko(e) : ok(row))));
const all = (sql, p = []) => new Promise((ok, ko) => db.all(sql, p, (e, rows) => (e ? ko(e) : ok(rows))));

// service
const x = await get(sql1, [a]);
const y = await get(sql2, [b]);
const { lastID } = await run(sql3, [c]);
```

---

## PB-15 Logger instead of print/console.log

**Before** `print("Item created: " + str(id))` · `console.log("[LOG] saving " + key)`
**After**
```python
import logging
logger = logging.getLogger(__name__)          # configured once in the composition root
logger.info("product created", extra={"product_id": product_id})
```
```js
// utils/logger.js
const level = process.env.LOG_LEVEL || 'info';
module.exports = { info: (...a) => console.log('[info]', ...a), error: (...a) => console.error('[error]', ...a) };
```
Fake side effects ("SENDING EMAIL...") become a notification service method that logs at INFO.

---

## PB-16 Replace deprecated APIs

```python
# before
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
post = Post.query.get(post_id)
# after
from datetime import datetime, timezone
def utcnow(): return datetime.now(timezone.utc).replace(tzinfo=None)   # keeps naive UTC values compatible with existing data
created_at = db.Column(db.DateTime, default=utcnow)
post = db.session.get(Post, post_id)
```
```js
// before
const buf = new Buffer(str); app.use(bodyParser.json());
// after
const buf = Buffer.from(str); app.use(express.json());
```
Keep serialized date formats identical to the original responses (e.g. `str(datetime)` output) to preserve the contract.
