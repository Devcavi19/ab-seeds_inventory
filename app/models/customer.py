import uuid
from datetime import datetime, timezone, timedelta

class Customer:
    TABLE = 'customers'
    
    @staticmethod
    def create(db, name: str, email: str, phone: str, address: str) -> dict:
        id = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8))).isoformat()
        
        db.execute(
            f"""
            INSERT INTO {Customer.TABLE} (id, name, email, phone, address, is_active, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [id, name, email, phone, address, True, now, now]
        )
        db.commit()
        return Customer.get_by_id(db, id)
        
    @staticmethod
    def get_by_id(db, id: str) -> dict | None:
        result = db.execute(f"SELECT * FROM {Customer.TABLE} WHERE id = ?", [id]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Customer.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        results = db.execute(f"SELECT * FROM {Customer.TABLE} WHERE is_active = TRUE ORDER BY created_at DESC").fetchall()
        customers = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Customer.TABLE})").fetchall()]
            for row in results:
                customers.append(dict(zip(columns, row)))
        return customers
        
    @staticmethod
    def update(db, id: str, name: str, email: str, phone: str, address: str) -> dict | None:
        now = datetime.now(timezone(timedelta(hours=8))).isoformat()
        
        db.execute(
            f"""
            UPDATE {Customer.TABLE} 
            SET name = ?, email = ?, phone = ?, address = ?, updated_at = ? 
            WHERE id = ?
            """,
            [name, email, phone, address, now, id]
        )
        db.commit()
        return Customer.get_by_id(db, id)
        
    @staticmethod
    def soft_delete(db, id: str) -> dict | None:
        now = datetime.now(timezone(timedelta(hours=8))).isoformat()
        
        db.execute(
            f"""
            UPDATE {Customer.TABLE} 
            SET is_active = FALSE, updated_at = ? 
            WHERE id = ?
            """,
            [now, id]
        )
        db.commit()
        return Customer.get_by_id(db, id)