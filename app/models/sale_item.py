import uuid

class SaleItem:
    TABLE = 'sale_items'

    @staticmethod
    def create(db, sale_id: str, product_id: str, quantity: int, unit_price: float) -> dict:
        """
        Create a new sale item
        """
        id = str(uuid.uuid4())

        db.execute(
            f"""
            INSERT INTO {SaleItem.TABLE}
            (id, sale_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            [id, sale_id, product_id, quantity, unit_price]
        )
        db.commit()
        return SaleItem.get_by_id(db, id)

    @staticmethod
    def get_by_id(db, item_id: str) -> dict | None:
        """Get sale item by ID"""
        result = db.execute(
            f"SELECT * FROM {SaleItem.TABLE} WHERE id = ?",
            [item_id]
        ).fetchone()

        if result:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({SaleItem.TABLE})").fetchall()]
            return dict(zip(columns, result))
        return None

    @staticmethod
    def get_by_sale_id(db, sale_id: str) -> list[dict]:
        """Get all items for a sale"""
        results = db.execute(
            f"SELECT * FROM {SaleItem.TABLE} WHERE sale_id = ?",
            [sale_id]
        ).fetchall()

        items = []
        if results:
            columns = [column[1] for column in db.execute(f"PRAGMA table_info({SaleItem.TABLE})").fetchall()]
            for row in results:
                items.append(dict(zip(columns, row)))
        return items

    @staticmethod
    def update(db, item_id: str, quantity: int, unit_price: float) -> dict | None:
        """Update a sale item"""
        db.execute(
            f"""
            UPDATE {SaleItem.TABLE}
            SET quantity = ?, unit_price = ?
            WHERE id = ?
            """,
            [quantity, unit_price, item_id]
        )
        db.commit()
        return SaleItem.get_by_id(db, item_id)

    @staticmethod
    def delete(db, item_id: str) -> bool:
        """Delete a sale item"""
        cursor = db.execute(
            f"DELETE FROM {SaleItem.TABLE} WHERE id = ?",
            [item_id]
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def delete_by_sale_id(db, sale_id: str) -> int:
        """Delete all items for a sale"""
        cursor = db.execute(
            f"DELETE FROM {SaleItem.TABLE} WHERE sale_id = ?",
            [sale_id]
        )
        db.commit()
        return cursor.rowcount
