import uuid
from datetime import datetime, timezone, timedelta

class PurchaseOrderItem:
    TABLE = 'purchase_order_items'
    
    @staticmethod
    def create(db, purchase_order_id: str, product_id: str, quantity: int, unit_cost: float, 
               received_quantity: int = 0) -> dict:
        """
        Create a new purchase order item
        """
        id = str(uuid.uuid4())
        
        db.execute(
            f"""
            INSERT INTO {PurchaseOrderItem.TABLE} 
            (id, purchase_order_id, product_id, quantity, unit_cost, received_quantity)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [id, purchase_order_id, product_id, quantity, unit_cost, received_quantity]
        )
        db.commit()
        return PurchaseOrderItem.get_by_id(db, id)
    
    @staticmethod
    def get_by_id(db, item_id: str) -> dict | None:
        """Get purchase order item by ID"""
        result = db.execute(
            f"SELECT * FROM {PurchaseOrderItem.TABLE} WHERE id = ?",
            [item_id]
        ).fetchone()
        
        if result:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({PurchaseOrderItem.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_by_order_id(db, purchase_order_id: str) -> list[dict]:
        """Get all items for a purchase order"""
        results = db.execute(
            f"SELECT * FROM {PurchaseOrderItem.TABLE} WHERE purchase_order_id = ?",
            [purchase_order_id]
        ).fetchall()
        
        items = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({PurchaseOrderItem.TABLE})").fetchall()]
            for row in results:
                items.append(dict(zip(columns, row)))
        return items
    
    @staticmethod
    def update(db, item_id: str, quantity: int, unit_cost: float, received_quantity: int = 0) -> dict | None:
        """Update a purchase order item"""
        db.execute(
            f"""
            UPDATE {PurchaseOrderItem.TABLE} 
            SET quantity = ?, unit_cost = ?, received_quantity = ?
            WHERE id = ?
            """,
            [quantity, unit_cost, received_quantity, item_id]
        )
        db.commit()
        return PurchaseOrderItem.get_by_id(db, item_id)
    
    @staticmethod
    def update_received_quantity(db, item_id: str, received_quantity: int) -> dict | None:
        """Update received quantity for a purchase order item"""
        db.execute(
            f"""
            UPDATE {PurchaseOrderItem.TABLE} 
            SET received_quantity = ?
            WHERE id = ?
            """,
            [received_quantity, item_id]
        )
        db.commit()
        return PurchaseOrderItem.get_by_id(db, item_id)
    
    @staticmethod
    def delete(db, item_id: str) -> bool:
        """Delete a purchase order item"""
        cursor = db.execute(
            f"DELETE FROM {PurchaseOrderItem.TABLE} WHERE id = ?",
            [item_id]
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete_by_order_id(db, purchase_order_id: str) -> int:
        """Delete all items for a purchase order"""
        cursor = db.execute(
            f"DELETE FROM {PurchaseOrderItem.TABLE} WHERE purchase_order_id = ?",
            [purchase_order_id]
        )
        db.commit()
        return cursor.rowcount