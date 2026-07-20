import turso
import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print("1. Connecting locally with turso.connect...")
conn_local = turso.connect(db_path)

print("2. Inserting data...")
conn_local.execute("CREATE TABLE IF NOT EXISTS _test_sync4 (id INT);")
conn_local.execute("INSERT INTO _test_sync4 VALUES (44);")
conn_local.commit()
conn_local.close()

print("3. Connecting via sync to push...")
conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn_sync.push()

print("4. Opening direct remote connection to verify...")
import urllib.request
import json
req = urllib.request.Request(url.replace("libsql://", "https://") + "/v2/pipeline",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    data=json.dumps({"requests": [{"type": "execute", "stmt": {"sql": "SELECT * FROM _test_sync4"}}]}, separators=(",",":")).encode("utf-8"))
try:
    with urllib.request.urlopen(req) as response:
        resp = json.loads(response.read().decode())
        print(resp)
except Exception as e:
    print(f"Verify failed: {e}")
