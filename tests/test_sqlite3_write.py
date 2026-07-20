import sqlite3
import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

# First, initialize the replica
conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn_sync.execute("CREATE TABLE IF NOT EXISTS _test_sqlite3 (id INT);")
conn_sync.push()
conn_sync.close()

# Now write with standard sqlite3
conn_sql = sqlite3.connect(db_path)
conn_sql.execute("PRAGMA journal_mode=WAL")
conn_sql.execute("INSERT INTO _test_sqlite3 VALUES (123);")
conn_sql.commit()
conn_sql.close()

# Try to push with turso.sync
conn_sync2 = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn_sync2.push()
conn_sync2.close()

# Verify
import urllib.request
import json
req = urllib.request.Request(url.replace("libsql://", "https://") + "/v2/pipeline",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    data=json.dumps({"requests": [{"type": "execute", "stmt": {"sql": "SELECT * FROM _test_sqlite3"}}]}, separators=(",",":")).encode("utf-8"))
try:
    with urllib.request.urlopen(req) as response:
        resp = json.loads(response.read().decode())
        print(resp)
except Exception as e:
    print(f"Verify failed: {e}")
