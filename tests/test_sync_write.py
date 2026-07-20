import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

conn = turso.sync.connect(db_path, remote_url=url, auth_token=token)

print("Executing test table creation...")
conn.execute("CREATE TABLE IF NOT EXISTS _test_sync (id INT);")
print("Executing test table insert...")
conn.execute("INSERT INTO _test_sync VALUES (99);")
conn.commit()

print("Pushing to Turso...")
conn.push()
print("Success!")
