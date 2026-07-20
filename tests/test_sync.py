import turso.sync
conn = turso.sync.connect("test.db", remote_url="http://dummy", auth_token="dummy")
print(hasattr(conn, 'execute'))
print(hasattr(conn, 'commit'))
print(hasattr(conn, 'close'))
