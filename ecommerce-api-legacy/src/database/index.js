const sqlite3 = require('sqlite3');

// Promise-based facade over the callback sqlite3 driver.
function wrap(raw) {
    let writeQueue = Promise.resolve();

    const db = {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },
        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },
        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
            });
        },
        exec(sql) {
            return new Promise((resolve, reject) => {
                raw.exec(sql, (err) => (err ? reject(err) : resolve()));
            });
        },
        // Runs `work` inside BEGIN/COMMIT. Transactions are queued because they share one connection.
        transaction(work) {
            const result = writeQueue.then(async () => {
                await db.exec('BEGIN');
                try {
                    const value = await work(db);
                    await db.exec('COMMIT');
                    return value;
                } catch (err) {
                    await db.exec('ROLLBACK');
                    throw err;
                }
            });
            writeQueue = result.catch(() => {});
            return result;
        },
        close() {
            return new Promise((resolve, reject) => raw.close((err) => (err ? reject(err) : resolve())));
        },
    };
    return db;
}

function createDatabase(filename) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(wrap(raw))));
    });
}

module.exports = { createDatabase };
