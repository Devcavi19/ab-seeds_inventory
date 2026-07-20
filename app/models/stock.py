import uuid
from datetime import datetime, timezone

class Stock:
    TABLE = 'stock'
    
    @staticmethod
    def upsert(db, product_id: str, quantity: int, lot_number: str, expiry_date: str, location: str) -> dict:
        """
        Upsert stock for a product. If stock exists for the product, update it.
        If not, create new stock entry.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Check if stock already exists for this product
        existing = Stock.get_by_product_id(db, product_id)
        
        if existing:
            # Update existing stock
            db.execute(
                f"""
                UPDATE {Stock.TABLE} 
                SET quantity = ?, lot_number = ?, expiry_date = ?, location = ?, updated_at = ? 
                WHERE product_id = ?
                """,
                [quantity, lot_number, expiry_date, location, now, product_id]
            )
            db.commit()
            return Stock.get_by_product_id(db, product_id)
        else:
            # Create new stock entry
            id = str(uuid.uuid4())
            db.execute(
                f"""
                INSERT INTO {Stock.TABLE} (id, product_id, quantity, lot_number, expiry_date, location, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [id, product_id, quantity, lot_number, expiry_date, location, now]
            )
            db.commit()
            return Stock.get_by_product_id(db, product_id)
    
    @staticmethod
    def get_by_product_id(db, product_id: str) -> dict | None:
        """Get stock by product ID.

        If no stock record exists yet but the product has a stock_quantity
        column (set by the simplified product schema), a stock record is
        auto-created from that value so that sales validation never sees a
        false-zero for products that were added without going through the
        stock management flow.
        """
        result = db.execute(
            f"SELECT * FROM {Stock.TABLE} WHERE product_id = ?", 
            [product_id]
        ).fetchone()
        
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Stock.TABLE})").fetchall()]
            return dict(zip(columns, result))

        # --- Safety-net: auto-seed from products.stock_quantity ---
        # This covers products created before migration 004, or any product
        # that was inserted without an explicit stock record.
        product_row = db.execute(
            "SELECT stock_quantity FROM products WHERE id = ? AND is_deleted = 0",
            [product_id]
        ).fetchone()
        if product_row is not None:
            quantity = product_row[0] if product_row[0] is not None else 0
            Stock.upsert(db, product_id, quantity, '', '', '')
            # Re-fetch the newly created record
            result = db.execute(
                f"SELECT * FROM {Stock.TABLE} WHERE product_id = ?",
                [product_id]
            ).fetchone()
            if result:
                columns = [column[1] for column in db.execute(f"PRAGMA table_info({Stock.TABLE})").fetchall()]
                return dict(zip(columns, result))

        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        """Get all stock entries"""
        results = db.execute(f"SELECT * FROM {Stock.TABLE} ORDER BY updated_at DESC").fetchall()
        stocks = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Stock.TABLE})").fetchall()]
            for row in results:
                stocks.append(dict(zip(columns, row)))
        return stocks
    
    @staticmethod
    def adjust_quantity(db, product_id: str, adjustment: int) -> dict | None:
        """Adjust stock quantity by specified amount (can be positive or negative)"""
        existing = Stock.get_by_product_id(db, product_id)
        if not existing:
            return None
        
        new_quantity = existing['quantity'] + adjustment
        if new_quantity < 0:
            new_quantity = 0  # Prevent negative stock
        
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Stock.TABLE} 
            SET quantity = ?, updated_at = ? 
            WHERE product_id = ?
            """,
            [new_quantity, now, product_id]
        )
        db.commit()
        return Stock.get_by_product_id(db, product_id)
    
    @staticmethod
    def get_low_stock(db, threshold: int = 20) -> list[dict]:
        """Get products with stock below specified threshold"""
        results = db.execute(
            f"""
            SELECT s.* FROM {Stock.TABLE} s
            WHERE s.quantity < ?
            ORDER BY s.quantity ASC
            """,
            [threshold]
        ).fetchall()
        
        low_stocks = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Stock.TABLE})").fetchall()]
            for row in results:
                low_stocks.append(dict(zip(columns, row)))
        return low_stocks