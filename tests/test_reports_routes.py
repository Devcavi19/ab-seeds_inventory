import pytest
from app.models.user import User
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.sale import Sale
from app.models.purchase_order import PurchaseOrder
from app.models.stock import Stock


def _login_admin(client, db, username="reportsadmin"):
    User.create(db, username, "password123", "Reports Admin", "admin")
    client.post('/auth/login', data={'username': username, 'password': 'password123'})


def _login_staff(client, db, username="reportsstaff"):
    User.create(db, username, "password123", "Reports Staff", "staff")
    client.post('/auth/login', data={'username': username, 'password': 'password123'})


def test_reports_require_login(client, db):
    response = client.get('/reports/sales', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_reports_are_admin_only(client, db):
    _login_staff(client, db)

    response = client.get('/reports/sales')
    assert response.status_code == 403

    response = client.get('/reports/purchases')
    assert response.status_code == 403

    response = client.get('/reports/stock')
    assert response.status_code == 403


def test_sales_report_page(client, db):
    _login_admin(client, db)

    customer = Customer.create(db, "Report Customer", "rc@test.com", "111", "Addr")
    sale = Sale.create(db, customer['id'], "SALE-REPORT-1", "completed", "2026-07-10")
    Sale.update_total_amount(db, sale['id'], 88.0)

    response = client.get('/reports/sales')
    assert response.status_code == 200
    assert b'SALE-REPORT-1' in response.data


def test_sales_report_date_filter(client, db):
    _login_admin(client, db)

    customer = Customer.create(db, "Filter Customer", "fc@test.com", "222", "Addr")
    in_range = Sale.create(db, customer['id'], "SALE-INRANGE", "completed", "2026-07-10")
    Sale.update_total_amount(db, in_range['id'], 10.0)
    out_of_range = Sale.create(db, customer['id'], "SALE-OUTRANGE", "completed", "2026-01-01")
    Sale.update_total_amount(db, out_of_range['id'], 20.0)

    response = client.get('/reports/sales?start_date=2026-07-01&end_date=2026-07-31')
    assert response.status_code == 200
    assert b'SALE-INRANGE' in response.data
    assert b'SALE-OUTRANGE' not in response.data


def test_purchases_report_page(client, db):
    _login_admin(client, db)

    supplier = Supplier.create(db, "Report Supplier", "Jim", "333", "rs@test.com", "Addr")
    order = PurchaseOrder.create(db, supplier['id'], "PO-REPORT-1", "completed", "2026-07-10")
    PurchaseOrder.update_total_amount(db, order['id'], 150.0)

    response = client.get('/reports/purchases')
    assert response.status_code == 200
    assert b'PO-REPORT-1' in response.data


def test_purchases_report_date_filter(client, db):
    _login_admin(client, db)

    supplier = Supplier.create(db, "Filter Supplier", "Jim", "444", "fs@test.com", "Addr")
    in_range = PurchaseOrder.create(db, supplier['id'], "PO-INRANGE", "completed", "2026-07-10")
    PurchaseOrder.update_total_amount(db, in_range['id'], 10.0)
    out_of_range = PurchaseOrder.create(db, supplier['id'], "PO-OUTRANGE", "completed", "2026-01-01")
    PurchaseOrder.update_total_amount(db, out_of_range['id'], 20.0)

    response = client.get('/reports/purchases?start_date=2026-07-01&end_date=2026-07-31')
    assert response.status_code == 200
    assert b'PO-INRANGE' in response.data
    assert b'PO-OUTRANGE' not in response.data


def test_stock_report_page_joins_product_name(client, db):
    _login_admin(client, db)

    product = Product.create(db, "Stock Report Product", "Desc", 9.99, 50, "cat1")
    Stock.upsert(db, product['id'], 42, "LOT-REPORT", "2027-01-01", "Warehouse Z")

    response = client.get('/reports/stock')
    assert response.status_code == 200
    assert b'Stock Report Product' in response.data
    assert b'42' in response.data


def test_export_sales_report_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/reports/sales/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=sales_report.csv' in response.headers['Content-Disposition']


def test_export_purchases_report_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/reports/purchases/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=purchases_report.csv' in response.headers['Content-Disposition']


def test_export_stock_report_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/reports/stock/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=stock_report.csv' in response.headers['Content-Disposition']
