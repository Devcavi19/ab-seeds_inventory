import uuid
from datetime import datetime, timezone

class Supplier:
    TABLE = 'suppliers'
    
    @staticmethod
    def create(db, name: str, contact_person: str, phone: str, email: str, address: str, notes: str = "") -> dict:
        id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            INSERT INTO {Supplier.TABLE} (id, name, contact_person, phone, email, address, notes, is_active, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [id, name, contact_person, phone, email, address, notes, True, now, now]
        )
        db.commit()
        return Supplier.get_by_id(db, id)
        
    @staticmethod
    def get_by_id(db, id: str) -> dict | None:
        result = db.execute(f"SELECT * FROM {Supplier.TABLE} WHERE id = ?", [id]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Supplier.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        results = db.execute(f"SELECT * FROM {Supplier.TABLE} WHERE is_active = TRUE ORDER BY created_at DESC").fetchall()
        suppliers = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Supplier.TABLE})").fetchall()]
            for row in results:
                suppliers.append(dict(zip(columns, row)))
        return suppliers
        
    @staticmethod
    def update(db, id: str, name: str, contact_person: str, phone: str, email: str, address: str, notes: str = "") -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Supplier.TABLE} 
            SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?, notes = ?, updated_at = ? 
            WHERE id = ?
            """,
            [name, contact_person, phone, email, address, notes, now, id]
        )
        db.commit()
        return Supplier.get_by_id(db, id)
        
    @staticmethod
    def soft_delete(db, id: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Supplier.TABLE} 
            SET is_active = FALSE, updated_at = ? 
            WHERE id = ?
            """,
            [now, id]
        )
        db.commit()
        return Supplier.get_by_id(db, id)