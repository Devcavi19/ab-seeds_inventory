import uuid
from datetime import datetime, timezone

class Sale:
    TABLE = 'sales'

    @staticmethod
    def create(db, customer_id: str, sale_number: str, status: str, sale_date: str,
               payment_method: str = '', total_amount: float = 0.0, notes: str = '',
               created_by: str = None) -> dict:
        """
        Create a new sale
        """
        now = datetime.now(timezone.utc).isoformat()
        id = str(uuid.uuid4())

        db.execute(
            f"""
            INSERT INTO {Sale.TABLE}
            (id, sale_number, customer_id, status, sale_date, total_amount,
             payment_method, notes, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [id, sale_number, customer_id, status, sale_date, total_amount,
             payment_method, notes, created_by, now, now]
        )
        db.commit()
        return Sale.get_by_id(db, id)

    @staticmethod
    def get_by_id(db, sale_id: str) -> dict | None:
        """Get sale by ID"""
        result = db.execute(
            f"SELECT * FROM {Sale.TABLE} WHERE id = ?",
            [sale_id]
        ).fetchone()

        if result:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Sale.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None

    @staticmethod
    def get_all(db) -> list[dict]:
        """Get all sales"""
        results = db.execute(f"SELECT * FROM {Sale.TABLE} ORDER BY sale_date DESC").fetchall()
        sales = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({Sale.TABLE})").fetchall()]
            for row in results:
                sales.append(dict(zip(columns, row)))
        return sales

    @staticmethod
    def update(db, sale_id: str, customer_id: str, sale_number: str, status: str,
               sale_date: str, payment_method: str, total_amount: float, notes: str) -> dict | None:
        """Update a sale"""
        now = datetime.now(timezone.utc).isoformat()

        db.execute(
            f"""
            UPDATE {Sale.TABLE}
            SET sale_number = ?, customer_id = ?, status = ?, sale_date = ?,
                payment_method = ?, total_amount = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            [sale_number, customer_id, status, sale_date, payment_method,
             total_amount, notes, now, sale_id]
        )
        db.commit()
        return Sale.get_by_id(db, sale_id)

    @staticmethod
    def update_status(db, sale_id: str, status: str) -> dict | None:
        """Update sale status"""
        now = datetime.now(timezone.utc).isoformat()

        db.execute(
            f"""
            UPDATE {Sale.TABLE}
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            [status, now, sale_id]
        )
        db.commit()
        return Sale.get_by_id(db, sale_id)

    @staticmethod
    def update_total_amount(db, sale_id: str, total_amount: float) -> dict | None:
        """Update sale total amount"""
        now = datetime.now(timezone.utc).isoformat()

        db.execute(
            f"""
            UPDATE {Sale.TABLE}
            SET total_amount = ?, updated_at = ?
            WHERE id = ?
            """,
            [total_amount, now, sale_id]
        )
        db.commit()
        return Sale.get_by_id(db, sale_id)
