import os
import sqlite3
from core.config import settings

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        sqlite_query = query.replace('%s', '?')
        sqlite_query = sqlite_query.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        
        if params is not None:
            self.cursor.execute(sqlite_query, params)
        else:
            self.cursor.execute(sqlite_query)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    db_url = settings.DATABASE_URL
    if db_url and PSYCOPG2_AVAILABLE:
        try:
            conn = psycopg2.connect(db_url, connection_factory=psycopg2.extras.RealDictConnection)
            return conn
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
            pass
    
    # SQLite Fallback
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sentry.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = dict_factory
    return SQLiteConnectionWrapper(conn)
