import turso
import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print("1. Connecting locally...")
conn_local = turso.connect(db_path)

print("2. Inserting data...")
conn_local.execute("CREATE TABLE IF NOT EXISTS _test_sync3 (id INT);")
conn_local.execute("INSERT INTO _test_sync3 VALUES (77);")
conn_local.commit()
# Do NOT close conn_local!

print("3. Connecting via sync to push...")
try:
    conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
    conn_sync.push()
    print("Push success!")
except Exception as e:
    print(f"Error: {e}")
