import uuid
from datetime import datetime, timezone

class Category:
    TABLE = 'categories'
    
    @staticmethod
    def create(db, name: str, description: str) -> dict:
        id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            INSERT INTO {Category.TABLE} (id, name, description, is_deleted, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [id, name, description, False, now, now]
        )
        db.commit()
        return Category.get_by_id(db, id)
        
    @staticmethod
    def get_by_id(db, id: str) -> dict | None:
        result = db.execute(f"SELECT * FROM {Category.TABLE} WHERE id = ?", [id]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Category.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        results = db.execute(f"SELECT * FROM {Category.TABLE} WHERE is_deleted = FALSE ORDER BY created_at DESC").fetchall()
        categories = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Category.TABLE})").fetchall()]
            for row in results:
                categories.append(dict(zip(columns, row)))
        return categories
        
    @staticmethod
    def update(db, id: str, name: str, description: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Category.TABLE} 
            SET name = ?, description = ?, updated_at = ? 
            WHERE id = ?
            """,
            [name, description, now, id]
        )
        db.commit()
        return Category.get_by_id(db, id)
        
    @staticmethod
    def soft_delete(db, id: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Category.TABLE} 
            SET is_deleted = TRUE, updated_at = ? 
            WHERE id = ?
            """,
            [now, id]
        )
        db.commit()
        return Category.get_by_id(db, id)