-- Seed the stock table from products.stock_quantity for any product
-- that does not yet have a stock record. This bridges the gap created
-- when migration 002 introduced products.stock_quantity without
-- back-populating the dedicated stock table.
INSERT OR IGNORE INTO stock (id, product_id, quantity, lot_number, expiry_date, location, updated_at)
SELECT
    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6))) AS id,
    p.id            AS product_id,
    COALESCE(p.stock_quantity, 0)   AS quantity,
    ''              AS lot_number,
    ''              AS expiry_date,
    ''              AS location,
    COALESCE(p.updated_at, p.created_at, datetime('now')) AS updated_at
FROM products p
WHERE p.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1 FROM stock s WHERE s.product_id = p.id
  );
