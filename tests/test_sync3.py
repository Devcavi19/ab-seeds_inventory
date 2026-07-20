import turso
conn = turso.connect("test.db")
c = conn.execute("CREATE TABLE IF NOT EXISTS test (id INT)")
print(c)
c = conn.execute("INSERT INTO test VALUES (1)")
conn.commit()
print("done")
