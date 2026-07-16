import pytest
from datetime import datetime, timezone, timedelta

from app.services import report_service
from app.models.product import Product
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.stock import Stock
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.purchase_order import PurchaseOrder


def test_get_summary_counts(db):
    Product.create(db, "Product A", "Desc", 5.99, 10, "cat1")
    Product.create(db, "Product B", "Desc", 6.99, 10, "cat1")
    deleted_product = Product.create(db, "Product C", "Desc", 7.99, 10, "cat1")
    Product.soft_delete(db, deleted_product['id'])

    Customer.create(db, "Customer A", "a@test.com", "111", "Addr A")
    Customer.create(db, "Customer B", "b@test.com", "222", "Addr B")

    Supplier.create(db, "Supplier A", "John", "333", "s@test.com", "Addr S")
    inactive_supplier = Supplier.create(db, "Supplier B", "Jane", "444", "s2@test.com", "Addr S2")
    Supplier.soft_delete(db, inactive_supplier['id'])

    low_product = Product.create(db, "Low Stock Product", "Desc", 3.99, 5, "cat1")
    Stock.upsert(db, low_product['id'], 5, "LOT1", "2027-01-01", "Loc A")
    normal_product = Product.create(db, "Normal Stock Product", "Desc", 3.99, 5, "cat1")
    Stock.upsert(db, normal_product['id'], 100, "LOT2", "2027-01-01", "Loc B")

    customer = Customer.create(db, "Sales Customer", "sc@test.com", "555", "Addr")
    Sale.create(db, customer['id'], "SALE-SUM-1", "pending", "2026-07-16")
    Sale.create(db, customer['id'], "SALE-SUM-2", "completed", "2026-07-16")

    supplier = Supplier.create(db, "PO Supplier", "Jim", "666", "po@test.com", "Addr")
    PurchaseOrder.create(db, supplier['id'], "PO-SUM-1", "pending", "2026-07-16")
    PurchaseOrder.create(db, supplier['id'], "PO-SUM-2", "completed", "2026-07-16")

    counts = report_service.get_summary_counts(db)

    assert counts['total_products'] == 4  # Product A, Product B, Low Stock Product, Normal Stock Product (Product C soft-deleted)
    assert counts['total_customers'] == 3
    assert counts['total_suppliers'] == 2  # Supplier A + PO Supplier (Supplier B soft-deleted)
    assert counts['low_stock_count'] >= 1
    assert counts['pending_sales_count'] >= 1
    assert counts['pending_purchase_orders_count'] >= 1


def test_get_total_sales_amount_no_rows_returns_zero(db):
    assert report_service.get_total_sales_amount(db) == 0.0


def test_get_total_sales_amount_sums_completed_only(db):
    customer = Customer.create(db, "Amount Customer", "amt@test.com", "777", "Addr")
    sale1 = Sale.create(db, customer['id'], "SALE-AMT-1", "completed", "2026-07-10")
    Sale.update_total_amount(db, sale1['id'], 100.0)
    sale2 = Sale.create(db, customer['id'], "SALE-AMT-2", "completed", "2026-07-11")
    Sale.update_total_amount(db, sale2['id'], 50.0)
    sale3 = Sale.create(db, customer['id'], "SALE-AMT-3", "pending", "2026-07-12")
    Sale.update_total_amount(db, sale3['id'], 999.0)

    total = report_service.get_total_sales_amount(db)
    assert total == 150.0


def test_get_total_sales_amount_date_filter(db):
    customer = Customer.create(db, "Date Customer", "date@test.com", "888", "Addr")
    sale1 = Sale.create(db, customer['id'], "SALE-DATE-1", "completed", "2026-07-01")
    Sale.update_total_amount(db, sale1['id'], 20.0)
    sale2 = Sale.create(db, customer['id'], "SALE-DATE-2", "completed", "2026-07-10")
    Sale.update_total_amount(db, sale2['id'], 30.0)
    sale3 = Sale.create(db, customer['id'], "SALE-DATE-3", "completed", "2026-07-20")
    Sale.update_total_amount(db, sale3['id'], 40.0)

    total = report_service.get_total_sales_amount(db, "2026-07-05", "2026-07-15")
    assert total == 30.0


def test_get_total_purchases_amount_no_rows_returns_zero(db):
    assert report_service.get_total_purchases_amount(db) == 0.0


def test_get_total_purchases_amount_sums_completed_only(db):
    supplier = Supplier.create(db, "Amount Supplier", "Jim", "999", "amt-s@test.com", "Addr")
    po1 = PurchaseOrder.create(db, supplier['id'], "PO-AMT-1", "completed", "2026-07-10")
    PurchaseOrder.update_total_amount(db, po1['id'], 200.0)
    po2 = PurchaseOrder.create(db, supplier['id'], "PO-AMT-2", "completed", "2026-07-11")
    PurchaseOrder.update_total_amount(db, po2['id'], 75.0)
    po3 = PurchaseOrder.create(db, supplier['id'], "PO-AMT-3", "pending", "2026-07-12")
    PurchaseOrder.update_total_amount(db, po3['id'], 999.0)

    total = report_service.get_total_purchases_amount(db)
    assert total == 275.0


def test_get_total_purchases_amount_date_filter(db):
    supplier = Supplier.create(db, "Date Supplier", "Jim", "1010", "date-s@test.com", "Addr")
    po1 = PurchaseOrder.create(db, supplier['id'], "PO-DATE-1", "completed", "2026-07-01")
    PurchaseOrder.update_total_amount(db, po1['id'], 10.0)
    po2 = PurchaseOrder.create(db, supplier['id'], "PO-DATE-2", "completed", "2026-07-10")
    PurchaseOrder.update_total_amount(db, po2['id'], 20.0)
    po3 = PurchaseOrder.create(db, supplier['id'], "PO-DATE-3", "completed", "2026-07-20")
    PurchaseOrder.update_total_amount(db, po3['id'], 30.0)

    total = report_service.get_total_purchases_amount(db, "2026-07-05", "2026-07-15")
    assert total == 20.0


def test_get_sales_by_day_zero_fills_gaps_and_orders_oldest_to_newest(db):
    customer = Customer.create(db, "Day Customer", "day@test.com", "1111", "Addr")

    today = datetime.now(timezone.utc).date()
    day_minus_6 = (today - timedelta(days=6)).isoformat()
    day_minus_3 = (today - timedelta(days=3)).isoformat()
    day_today = today.isoformat()

    sale1 = Sale.create(db, customer['id'], "SALE-DAY-1", "completed", day_minus_6)
    Sale.update_total_amount(db, sale1['id'], 10.0)
    sale2 = Sale.create(db, customer['id'], "SALE-DAY-2", "completed", day_today)
    Sale.update_total_amount(db, sale2['id'], 25.0)
    # A pending sale on day_minus_3 should NOT count toward that day's total
    sale3 = Sale.create(db, customer['id'], "SALE-DAY-3", "pending", day_minus_3)
    Sale.update_total_amount(db, sale3['id'], 999.0)

    result = report_service.get_sales_by_day(db, 7)

    assert len(result) == 7
    dates = [r['date'] for r in result]
    expected_dates = [(today - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
    assert dates == expected_dates

    by_date = {r['date']: r['total'] for r in result}
    assert by_date[day_minus_6] == 10.0
    assert by_date[day_today] == 25.0
    assert by_date[day_minus_3] == 0.0  # zero-filled: only a pending sale exists that day

    # Any day with no sales at all must still be present with 0.0, not omitted
    for r in result:
        assert isinstance(r['total'], float)


def test_get_top_selling_products(db):
    customer = Customer.create(db, "Top Customer", "top@test.com", "1212", "Addr")
    product1 = Product.create(db, "Top Product 1", "Desc", 5.0, 100, "cat1")
    product2 = Product.create(db, "Top Product 2", "Desc", 6.0, 100, "cat1")
    product3 = Product.create(db, "Top Product 3", "Desc", 7.0, 100, "cat1")

    completed_sale = Sale.create(db, customer['id'], "SALE-TOP-1", "completed", "2026-07-10")
    SaleItem.create(db, completed_sale['id'], product1['id'], 10, 5.0)
    SaleItem.create(db, completed_sale['id'], product2['id'], 3, 6.0)

    completed_sale2 = Sale.create(db, customer['id'], "SALE-TOP-2", "completed", "2026-07-11")
    SaleItem.create(db, completed_sale2['id'], product1['id'], 5, 5.0)

    # Sale items on a pending sale must not count toward totals
    pending_sale = Sale.create(db, customer['id'], "SALE-TOP-3", "pending", "2026-07-12")
    SaleItem.create(db, pending_sale['id'], product3['id'], 1000, 7.0)

    results = report_service.get_top_selling_products(db, 5)

    result_by_id = {r['product_id']: r for r in results}
    assert result_by_id[product1['id']]['total_quantity'] == 15
    assert result_by_id[product1['id']]['product_name'] == "Top Product 1"
    assert result_by_id[product2['id']]['total_quantity'] == 3
    assert product3['id'] not in result_by_id

    # Ordered by total_quantity DESC
    quantities = [r['total_quantity'] for r in results]
    assert quantities == sorted(quantities, reverse=True)
    assert results[0]['product_id'] == product1['id']


def test_get_top_selling_products_respects_limit(db):
    customer = Customer.create(db, "Limit Customer", "limit@test.com", "1313", "Addr")
    sale = Sale.create(db, customer['id'], "SALE-LIMIT-1", "completed", "2026-07-10")

    products = []
    for i in range(7):
        product = Product.create(db, f"Limit Product {i}", "Desc", 1.0, 100, "cat1")
        products.append(product)
        SaleItem.create(db, sale['id'], product['id'], i + 1, 1.0)

    results = report_service.get_top_selling_products(db, 3)
    assert len(results) == 3


def test_get_low_stock_items_delegates_to_stock_model(db):
    low_product = Product.create(db, "Delegate Low Product", "Desc", 2.0, 5, "cat1")
    Stock.upsert(db, low_product['id'], 5, "LOT1", "2027-01-01", "Loc A")
    normal_product = Product.create(db, "Delegate Normal Product", "Desc", 2.0, 100, "cat1")
    Stock.upsert(db, normal_product['id'], 100, "LOT2", "2027-01-01", "Loc B")

    items = report_service.get_low_stock_items(db)
    ids = [i['product_id'] for i in items]
    assert low_product['id'] in ids
    assert normal_product['id'] not in ids

    # threshold param is honored
    items_high_threshold = report_service.get_low_stock_items(db, threshold=1000)
    ids_high = [i['product_id'] for i in items_high_threshold]
    assert low_product['id'] in ids_high
    assert normal_product['id'] in ids_high
