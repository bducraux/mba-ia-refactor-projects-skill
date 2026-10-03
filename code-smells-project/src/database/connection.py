import sqlite3

from flask import g

_CHAVE_G = "db_conn"


class Database:
    """Fábrica de conexões SQLite: uma conexão por requisição (flask.g), fechada no teardown."""

    def __init__(self, path):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def connection(self):
        if _CHAVE_G not in g:
            g.db_conn = self.connect()
        return g.db_conn

    def close(self, _exc=None):
        conn = g.pop(_CHAVE_G, None)
        if conn is not None:
            conn.close()

    def init_app(self, app):
        app.teardown_appcontext(self.close)
