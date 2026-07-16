-- Update products table to match the new schema
DROP TABLE IF EXISTS products;

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    stock_quantity INTEGER,
    category_id TEXT REFERENCES categories(id),
    image_path TEXT,
    is_deleted INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);