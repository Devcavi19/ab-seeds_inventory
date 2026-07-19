import os
import sqlite3
from flask import g, current_app
try:
    import turso.sync
except ImportError:
    turso = None

def get_db():
    if 'db' not in g:
        # Create data dir if not exists
        os.makedirs(os.path.dirname(current_app.config['DATABASE_PATH']), exist_ok=True)
        
        sync_url = current_app.config.get('TURSO_DATABASE_URL')
        auth_token = current_app.config.get('TURSO_AUTH_TOKEN')
        
        if sync_url and auth_token and turso:
            # Use the global sync connection so that libSQL correctly tracks writes
            # without spinning up multiple Tokio runtimes and causing Rust panics.
            g.db = current_app.sync_service.conn
        else:
            g.db = sqlite3.connect(database=current_app.config['DATABASE_PATH'])
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        # Only close if it's the standard sqlite3 connection
        sync_url = current_app.config.get('TURSO_DATABASE_URL')
        if not (sync_url and current_app.config.get('TURSO_AUTH_TOKEN') and turso):
            db.close()

def init_db(app):
    app.teardown_appcontext(close_db)

def init_migrations(app):
    migrations_dir = os.path.join(app.root_path, '..', 'migrations')
    if not os.path.exists(migrations_dir):
        return

    with app.app_context():
        db = get_db()
        db.execute(
            'CREATE TABLE IF NOT EXISTS schema_migrations ('
            'filename TEXT PRIMARY KEY, '
            'applied_at TEXT DEFAULT CURRENT_TIMESTAMP)'
        )
        applied = {
            row[0]
            for row in db.execute('SELECT filename FROM schema_migrations')
        }
        for filename in sorted(os.listdir(migrations_dir)):
            if filename.endswith('.sql') and filename not in applied:
                filepath = os.path.join(migrations_dir, filename)
                with open(filepath, 'r') as f:
                    db.executescript(f.read())
                db.execute(
                    'INSERT INTO schema_migrations (filename) VALUES (?)',
                    (filename,),
                )
        db.commit()