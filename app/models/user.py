import uuid
import bcrypt
from datetime import datetime, timezone, timedelta

class User:
    TABLE = 'users'
    
    @staticmethod
    def create(db, username: str, password: str, full_name: str, role: str = 'staff') -> dict:
        id = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8))).isoformat()
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        db.execute(
            "INSERT INTO users (id, username, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [id, username, password_hash, full_name, role, now, now]
        )
        db.commit()
        return User.get_by_id(db, id)
        
    @staticmethod
    def get_by_id(db, id: str) -> dict | None:
        result = db.execute("SELECT * FROM users WHERE id = ?", [id]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute("PRAGMA table_info(users)").fetchall()]
            return dict(zip(columns, result))
        return None
        
    @staticmethod
    def get_by_username(db, username: str) -> dict | None:
        result = db.execute("SELECT * FROM users WHERE username = ?", [username]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute("PRAGMA table_info(users)").fetchall()]
            return dict(zip(columns, result))
        return None

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))