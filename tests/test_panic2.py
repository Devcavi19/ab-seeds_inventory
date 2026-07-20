import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print("Connecting 1...")
conn1 = turso.sync.connect(db_path, remote_url=url, auth_token=token)

print("Connecting 2...")
try:
    conn2 = turso.sync.connect(db_path, remote_url=url, auth_token=token)
    print("Success")
except Exception as e:
    print(f"Exception: {e}")
