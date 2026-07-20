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

print("2. Executing test table insert via local connection...")
conn_local.execute("CREATE TABLE IF NOT EXISTS _test_sync2 (id INT);")
conn_local.execute("INSERT INTO _test_sync2 VALUES (88);")
conn_local.commit()
conn_local.close()

print("3. Connecting via turso.sync.connect to push...")
conn_sync = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn_sync.push()
print("Success!")
