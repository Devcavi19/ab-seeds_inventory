import turso
import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print("Checking local database...")
if not os.path.exists(db_path):
    print("Local database missing!")
else:
    print(f"Local database exists, size: {os.path.getsize(db_path)}")

print("Attempting sync...")
try:
    conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
    conn_sync.push()
    conn_sync.pull()
    print("Sync successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Sync failed: {e}")
