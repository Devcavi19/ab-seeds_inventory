import turso
import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print("Removing DB...")
os.system("rm -f data/local.db*")

print("Connecting...")
try:
    conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
    print("Success")
except Exception as e:
    print(e)
