CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT,
    role TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    is_deleted INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    sku TEXT UNIQUE,
    name TEXT,
    variety TEXT,
    brand TEXT,
    category_id TEXT REFERENCES categories(id),
    description TEXT,
    unit TEXT,
    cost_price REAL,
    selling_price REAL,
    reorder_level INTEGER,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    id TEXT PRIMARY KEY,
    name TEXT,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS stock (
    id TEXT PRIMARY KEY,
    product_id TEXT UNIQUE REFERENCES products(id),
    quantity INTEGER,
    lot_number TEXT,
    expiry_date TEXT,
    location TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id TEXT PRIMARY KEY,
    order_number TEXT UNIQUE,
    supplier_id TEXT REFERENCES suppliers(id),
    status TEXT,
    order_date TEXT,
    received_date TEXT,
    total_amount REAL,
    notes TEXT,
    created_by TEXT REFERENCES users(id),
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id TEXT PRIMARY KEY,
    purchase_order_id TEXT REFERENCES purchase_orders(id),
    product_id TEXT REFERENCES products(id),
    quantity INTEGER,
    unit_cost REAL,
    received_quantity INTEGER
);

CREATE TABLE IF NOT EXISTS sales (
    id TEXT PRIMARY KEY,
    sale_number TEXT UNIQUE,
    customer_id TEXT REFERENCES customers(id),
    status TEXT,
    sale_date TEXT,
    total_amount REAL,
    payment_method TEXT,
    notes TEXT,
    created_by TEXT REFERENCES users(id),
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sale_items (
    id TEXT PRIMARY KEY,
    sale_id TEXT REFERENCES sales(id),
    product_id TEXT REFERENCES products(id),
    quantity INTEGER,
    unit_price REAL
);