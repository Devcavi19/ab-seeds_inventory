import uuid
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename

def get_upload_folder():
    """Get the upload folder path"""
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

class Product:
    TABLE = 'products'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Product.ALLOWED_EXTENSIONS
    
    @staticmethod
    def create(db, name: str, description: str, price: float, stock_quantity: int, category_id: str, image_file=None) -> dict:
        id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Handle image upload
        image_path = None
        if image_file and Product.allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_folder = get_upload_folder()
            image_path = os.path.join(upload_folder, f"{id}_{filename}")
            image_file.save(image_path)
            # Store relative path
            image_path = os.path.relpath(image_path, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        db.execute(
            f"""
            INSERT INTO {Product.TABLE} (id, name, description, price, stock_quantity, category_id, image_path, is_deleted, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [id, name, description, price, stock_quantity, category_id, image_path, False, now, now]
        )
        db.commit()
        return Product.get_by_id(db, id)
        
    @staticmethod
    def get_by_id(db, id: str) -> dict | None:
        result = db.execute(f"SELECT * FROM {Product.TABLE} WHERE id = ?", [id]).fetchone()
        if result:
            # Convert tuple to dict with column names
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Product.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def get_all(db) -> list[dict]:
        results = db.execute(f"SELECT * FROM {Product.TABLE} WHERE is_deleted = FALSE ORDER BY created_at DESC").fetchall()
        products = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Product.TABLE})").fetchall()]
            for row in results:
                products.append(dict(zip(columns, row)))
        return products
        
    @staticmethod
    def update(db, id: str, name: str, description: str, price: float, stock_quantity: int, category_id: str, image_file=None) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        # Get existing product to preserve image if not updated
        existing = Product.get_by_id(db, id)
        if not existing:
            return None
            
        # Handle image upload
        image_path = existing['image_path']
        if image_file and Product.allowed_file(image_file.filename):
            # Delete old image if it exists
            if existing['image_path']:
                old_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), existing['image_path'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            filename = secure_filename(image_file.filename)
            upload_folder = get_upload_folder()
            image_path = os.path.join(upload_folder, f"{id}_{filename}")
            image_file.save(image_path)
            # Store relative path
            image_path = os.path.relpath(image_path, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        db.execute(
            f"""
            UPDATE {Product.TABLE} 
            SET name = ?, description = ?, price = ?, stock_quantity = ?, category_id = ?, image_path = ?, updated_at = ? 
            WHERE id = ?
            """,
            [name, description, price, stock_quantity, category_id, image_path, now, id]
        )
        db.commit()
        return Product.get_by_id(db, id)
        
    @staticmethod
    def soft_delete(db, id: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            f"""
            UPDATE {Product.TABLE} 
            SET is_deleted = TRUE, updated_at = ? 
            WHERE id = ?
            """,
            [now, id]
        )
        db.commit()
        return Product.get_by_id(db, id)
    
    @staticmethod
    def search(db, query: str) -> list[dict]:
        results = db.execute(
            f"SELECT * FROM {Product.TABLE} WHERE is_deleted = FALSE AND (name LIKE ? OR description LIKE ?) ORDER BY created_at DESC",
            [f'%{query}%', f'%{query}%']
        ).fetchall()
        
        products = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Product.TABLE})").fetchall()]
            for row in results:
                products.append(dict(zip(columns, row)))
        return products
        
    @staticmethod
    def get_by_category(db, category_id: str) -> list[dict]:
        results = db.execute(
            f"SELECT * FROM {Product.TABLE} WHERE is_deleted = FALSE AND category_id = ? ORDER BY created_at DESC",
            [category_id]
        ).fetchall()
        
        products = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Product.TABLE})").fetchall()]
            for row in results:
                products.append(dict(zip(columns, row)))
        return products