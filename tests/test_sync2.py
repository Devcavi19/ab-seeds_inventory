import turso
conn = turso.connect("test.db")
print(hasattr(conn, 'execute'))
print(hasattr(conn, 'commit'))
print(hasattr(conn, 'close'))
