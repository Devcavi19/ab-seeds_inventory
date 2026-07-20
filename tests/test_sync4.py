import turso
conn = turso.connect("test.db")
c = conn.execute("INSERT INTO test VALUES (?)", [2])
conn.commit()
print(conn.execute("SELECT * FROM test").fetchall())
