import urllib.request
import json
import os
from dotenv import load_dotenv
load_dotenv()

url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

req = urllib.request.Request(url.replace("libsql://", "https://") + "/v2/pipeline",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    data=json.dumps({"requests": [{"type": "execute", "stmt": {"sql": "SELECT id, name, is_deleted FROM products"}}]}, separators=(",",":")).encode("utf-8"))
try:
    with urllib.request.urlopen(req) as response:
        resp = json.loads(response.read().decode())
        print(resp)
except Exception as e:
    print(f"Verify failed: {e}")
