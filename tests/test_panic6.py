import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

conn = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)')
print("Success")
