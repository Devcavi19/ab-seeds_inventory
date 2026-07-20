import turso.sync
import os
import threading
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

def run_sync():
    print("Thread starting...")
    conn = turso.sync.connect(db_path, remote_url=url, auth_token=token)
    conn.push()
    conn.pull()
    conn.close()
    print("Thread done.")

# Create the first one
conn_main = turso.sync.connect(db_path, remote_url=url, auth_token=token)
conn_main.execute("SELECT 1")

t = threading.Thread(target=run_sync)
t.start()
t.join()

print("Success")
