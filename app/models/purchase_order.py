import uuid
from datetime import datetime, timezone

class PurchaseOrder:
    TABLE = 'purchase_orders'
    
    @staticmethod
    def create(db, supplier_id: str, order_number: str, status: str, order_date: str, 
               received_date: str = None, total_amount: float = 0.0, notes: str = '', 
               created_by: str = None) -> dict:
        """
        Create a new purchase order
        """
        now = datetime.now(timezone.utc).isoformat()
        id = str(uuid.uuid4())
        
        db.execute(
            f"""
            INSERT INTO {PurchaseOrder.TABLE} 
            (id, order_number, supplier_id, status, order_date, received_date, 
             total_amount, notes, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [id, order_number, supplier_id, status, order_date, received_date, 
             total_amount, notes, created_by, now, now]
        )
        db.commit()
        return PurchaseOrder.get_by_id(db, id)
    
    @staticmethod
    def get_by_id(db, order_id: str) -> dict | None:
        """Get purchase order by ID"""
        result = db.execute(
            f"SELECT * FROM {PurchaseOrder.TABLE} WHERE id = ?",
            [order_id]
        ).fetchone()
        
        if result:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({PurchaseOrder.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        """Get all purchase orders"""
        results = db.execute(f"SELECT * FROM {PurchaseOrder.TABLE} ORDER BY order_date DESC").fetchall()
        orders = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({PurchaseOrder.TABLE})").fetchall()]
            for row in results:
                orders.append(dict(zip(columns, row)))
        return orders
    
    @staticmethod
    def update(db, order_id: str, supplier_id: str, order_number: str, status: str, 
                order_date: str, received_date: str = None, total_amount: float = 0.0, 
                notes: str = '') -> dict | None:
        """Update a purchase order"""
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {PurchaseOrder.TABLE} 
            SET order_number = ?, supplier_id = ?, status = ?, order_date = ?, 
                received_date = ?, total_amount = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            [order_number, supplier_id, status, order_date, received_date, 
             total_amount, notes, now, order_id]
        )
        db.commit()
        return PurchaseOrder.get_by_id(db, order_id)
    
    @staticmethod
    def update_status(db, order_id: str, status: str) -> dict | None:
        """Update purchase order status"""
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {PurchaseOrder.TABLE} 
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            [status, now, order_id]
        )
        db.commit()
        return PurchaseOrder.get_by_id(db, order_id)
    
    @staticmethod
    def update_total_amount(db, order_id: str, total_amount: float) -> dict | None:
        """Update purchase order total amount"""
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {PurchaseOrder.TABLE} 
            SET total_amount = ?, updated_at = ?
            WHERE id = ?
            """,
            [total_amount, now, order_id]
        )
        db.commit()
        return PurchaseOrder.get_by_id(db, order_id)