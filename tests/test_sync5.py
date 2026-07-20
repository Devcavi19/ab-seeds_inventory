import turso
conn = turso.connect("test.db")
c = conn.executescript("CREATE TABLE IF NOT EXISTS test2 (id INT); INSERT INTO test2 VALUES (1);")
print("executescript supported")
