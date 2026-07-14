CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
  is_active INTEGER NOT NULL DEFAULT 1,
  token_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  sku TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '',
  unit TEXT NOT NULL DEFAULT 'pcs',
  price_cents INTEGER NOT NULL DEFAULT 0,
  low_stock_threshold REAL NOT NULL DEFAULT 0,
  is_archived INTEGER NOT NULL DEFAULT 0,
  current_qty REAL NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL,
  server_seq INTEGER NOT NULL
);

-- Append-only: rows are never updated or deleted (except current_qty cache on items).
CREATE TABLE IF NOT EXISTS movements (
  id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL REFERENCES items(id),
  type TEXT NOT NULL CHECK (type IN ('in', 'out', 'adjustment')),
  qty_delta REAL NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  user_id TEXT NOT NULL,
  username TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  server_seq INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_items_seq ON items(server_seq);
CREATE INDEX IF NOT EXISTS idx_movements_seq ON movements(server_seq);
CREATE INDEX IF NOT EXISTS idx_movements_item ON movements(item_id, created_at);

INSERT OR IGNORE INTO meta (key, value) VALUES ('last_seq', '0');
