from datetime import datetime, timezone, timedelta

from app.models.stock import Stock


def get_summary_counts(db) -> dict:
    """
    One dict of headline counts for the dashboard summary cards.

    Note: products has no `is_active` column in this codebase's schema (only
    `is_deleted`, see migrations/002_update_products_schema.sql) - "active
    products" is expressed as `is_deleted = 0`, mirroring the convention
    already used by Product.get_all/search/get_by_category.
    """
    total_products = db.execute(
        "SELECT COUNT(*) FROM products WHERE is_deleted = 0"
    ).fetchone()[0]

    total_customers = db.execute(
        "SELECT COUNT(*) FROM customers WHERE is_active = TRUE"
    ).fetchone()[0]

    total_suppliers = db.execute(
        "SELECT COUNT(*) FROM suppliers WHERE is_active = 1"
    ).fetchone()[0]

    low_stock_count = db.execute(
        "SELECT COUNT(*) FROM stock WHERE quantity < 20"
    ).fetchone()[0]

    pending_sales_count = db.execute(
        "SELECT COUNT(*) FROM sales WHERE status = 'pending'"
    ).fetchone()[0]

    pending_purchase_orders_count = db.execute(
        "SELECT COUNT(*) FROM purchase_orders WHERE status = 'pending'"
    ).fetchone()[0]

    return {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'low_stock_count': low_stock_count,
        'pending_sales_count': pending_sales_count,
        'pending_purchase_orders_count': pending_purchase_orders_count,
    }


def get_total_sales_amount(db, start_date: str = None, end_date: str = None) -> float:
    """Sum of completed sales' total_amount, optionally filtered by sale_date range (inclusive)."""
    if start_date and end_date:
        result = db.execute(
            """
            SELECT SUM(total_amount) FROM sales
            WHERE status = 'completed' AND sale_date BETWEEN ? AND ?
            """,
            [start_date, end_date]
        ).fetchone()
    else:
        result = db.execute(
            "SELECT SUM(total_amount) FROM sales WHERE status = 'completed'"
        ).fetchone()

    total = result[0]
    return total if total is not None else 0.0


def get_total_purchases_amount(db, start_date: str = None, end_date: str = None) -> float:
    """Sum of completed purchase orders' total_amount, optionally filtered by order_date range (inclusive)."""
    if start_date and end_date:
        result = db.execute(
            """
            SELECT SUM(total_amount) FROM purchase_orders
            WHERE status = 'completed' AND order_date BETWEEN ? AND ?
            """,
            [start_date, end_date]
        ).fetchone()
    else:
        result = db.execute(
            "SELECT SUM(total_amount) FROM purchase_orders WHERE status = 'completed'"
        ).fetchone()

    total = result[0]
    return total if total is not None else 0.0


def get_sales_by_day(db, days: int = 7) -> list[dict]:
    """
    One entry per calendar day for the last `days` days (including today),
    ordered oldest to newest. Days with no completed sales are zero-filled
    rather than omitted, since this feeds a chart that needs a stable x-axis.
    """
    today = datetime.now(timezone.utc).date()
    date_range = [(today - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]

    results = db.execute(
        """
        SELECT sale_date, SUM(total_amount) FROM sales
        WHERE status = 'completed'
        GROUP BY sale_date
        """
    ).fetchall()
    totals_by_date = {row[0]: row[1] for row in results}

    return [
        {'date': day, 'total': totals_by_date.get(day) or 0.0}
        for day in date_range
    ]


def get_top_selling_products(db, limit: int = 5) -> list[dict]:
    """Top `limit` products by total quantity sold across completed sales."""
    results = db.execute(
        """
        SELECT p.id, p.name, SUM(si.quantity) AS total_quantity
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN products p ON si.product_id = p.id
        WHERE s.status = 'completed'
        GROUP BY p.id, p.name
        ORDER BY total_quantity DESC
        LIMIT ?
        """,
        [limit]
    ).fetchall()

    return [
        {'product_id': row[0], 'product_name': row[1], 'total_quantity': row[2]}
        for row in results
    ]


def get_low_stock_items(db, threshold: int = 20) -> list[dict]:
    """Delegates to Stock.get_low_stock - kept here so dashboard/reports have
    one place to import all aggregation calls from."""
    return Stock.get_low_stock(db, threshold)
