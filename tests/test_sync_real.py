import turso.sync
import os
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

if not url:
    print("No TURSO_DATABASE_URL")
    exit(1)

import time
t0 = time.time()
conn = turso.sync.connect(db_path, remote_url=url, auth_token=token)
t1 = time.time()
print(f"Connect took {t1-t0:.3f}s")

t0 = time.time()
c = conn.execute("SELECT 1")
print(c.fetchall())
t1 = time.time()
print(f"Execute took {t1-t0:.3f}s")
