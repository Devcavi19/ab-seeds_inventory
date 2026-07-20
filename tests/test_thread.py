import turso.sync
import os
import threading
from dotenv import load_dotenv
load_dotenv()

db_path = "data/local.db"
url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

conn = turso.sync.connect(db_path, remote_url=url, auth_token=token)

def run_query():
    try:
        print(conn.execute("SELECT 1").fetchall())
    except Exception as e:
        print(f"Error: {e}")

t = threading.Thread(target=run_query)
t.start()
t.join()
