import pytest
from flask import url_for
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.stock import Stock
from app.models.user import User

def login_as_admin(client, db):
    User.create(db, "admin", "password123", "Admin User", "admin")
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200

def test_sale_routes(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Test Customer", "customer@test.com", "1234567890", "123 Test St")
    product = Product.create(db, "Test Product", "Test description", 10.99, 100, "test-category-id")
    Stock.upsert(db, product['id'], 50, "LOT001", "2026-12-31", "Warehouse A")

    # Test list page
    response = client.get('/sales/')
    assert response.status_code == 200
    assert b'Sales' in response.data

    # Test create page
    response = client.get('/sales/create')
    assert response.status_code == 200
    assert b'Create Sale' in response.data

    # Test create submission (pending - should not touch stock)
    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-TEST-001',
        'status': 'pending',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': 'Test sale for routes',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['10'],
        'item_unit_price[]': ['12.99']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Sale created successfully' in response.data

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 50  # unchanged since sale is pending

    sales = Sale.get_all(db)
    created_sale = None
    for sale in sales:
        if sale['sale_number'] == 'SALE-TEST-001':
            created_sale = sale
            break

    assert created_sale is not None
    assert created_sale['total_amount'] == 129.9

    # Test view page
    response = client.get(f'/sales/{created_sale["id"]}/view')
    assert response.status_code == 200
    assert b'SALE-TEST-001' in response.data

    # Test edit page
    response = client.get(f'/sales/{created_sale["id"]}/edit')
    assert response.status_code == 200
    assert b'Edit Sale' in response.data

    # Test edit submission
    response = client.post(f'/sales/{created_sale["id"]}/edit', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-TEST-001-UPDATED',
        'status': 'pending',
        'sale_date': '2026-07-17',
        'payment_method': 'card',
        'notes': 'Updated test sale',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['15'],
        'item_unit_price[]': ['6.99']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Sale updated successfully' in response.data

    # Stock should still be unchanged - edit does not affect stock
    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 50


def test_sale_create_completed_deducts_stock(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Stock Customer", "stockcust@test.com", "1234567891", "1 Test St")
    product = Product.create(db, "Stock Product", "Desc", 10.0, 100, "cat-a")
    Stock.upsert(db, product['id'], 30, "LOT100", "2026-12-31", "Warehouse A")

    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-COMPLETED-001',
        'status': 'completed',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['10'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Sale created successfully' in response.data

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 20  # 30 - 10 deducted since status is completed


def test_sale_create_oversell_rejected(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Oversell Customer", "oversell@test.com", "1234567892", "2 Test St")
    product = Product.create(db, "Oversell Product", "Desc", 10.0, 100, "cat-b")
    Stock.upsert(db, product['id'], 5, "LOT101", "2026-12-31", "Warehouse A")

    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-OVERSELL-001',
        'status': 'completed',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['10'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Oversell Product' in response.data  # flash error names the product

    # Stock should be unchanged
    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 5

    # No sale should have been created
    sales = Sale.get_all(db)
    assert not any(s['sale_number'] == 'SALE-OVERSELL-001' for s in sales)


def test_sale_create_pending_within_stock_does_not_deduct(client, db):
    # A pending sale that passes the oversell check should not touch stock yet -
    # deduction only happens once the sale is completed.
    login_as_admin(client, db)

    customer = Customer.create(db, "Pending Customer", "pending@test.com", "1234567893", "3 Test St")
    product = Product.create(db, "Pending Product", "Desc", 10.0, 100, "cat-c")
    Stock.upsert(db, product['id'], 5, "LOT102", "2026-12-31", "Warehouse A")

    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-PENDING-001',
        'status': 'pending',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['3'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Sale created successfully' in response.data

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 5  # unchanged - status is pending, no deduction


def test_sale_create_pending_oversell_still_rejected(client, db):
    # The oversell check at creation time applies regardless of status - even a
    # pending sale must not request more than is currently in stock.
    login_as_admin(client, db)

    customer = Customer.create(db, "Pending Oversell Customer", "pendingoversell@test.com", "1234567893", "3 Test St")
    product = Product.create(db, "Pending Oversell Product", "Desc", 10.0, 100, "cat-c")
    Stock.upsert(db, product['id'], 5, "LOT102", "2026-12-31", "Warehouse A")

    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-PENDING-OVERSELL-001',
        'status': 'pending',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['999'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Pending Oversell Product' in response.data  # flash error names the product

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 5  # unchanged

    sales = Sale.get_all(db)
    assert not any(s['sale_number'] == 'SALE-PENDING-OVERSELL-001' for s in sales)


def test_sale_update_status_to_completed_deducts_stock(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Complete Later Customer", "completelater@test.com", "1234567894", "4 Test St")
    product = Product.create(db, "Complete Later Product", "Desc", 10.0, 100, "cat-d")
    Stock.upsert(db, product['id'], 40, "LOT103", "2026-12-31", "Warehouse A")

    # Create as pending
    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-COMPLETE-LATER-001',
        'status': 'pending',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['12'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)
    assert response.status_code == 200

    sales = Sale.get_all(db)
    sale = next(s for s in sales if s['sale_number'] == 'SALE-COMPLETE-LATER-001')

    # Stock unaffected while pending
    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 40

    # Now complete it
    response = client.post(f'/sales/{sale["id"]}/update-status', data={
        'status': 'completed'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Sale status updated successfully' in response.data

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 28  # 40 - 12 deducted upon completion

    updated_sale = Sale.get_by_id(db, sale['id'])
    assert updated_sale['status'] == 'completed'


def test_sale_update_status_to_completed_oversell_rejected(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Reject Complete Customer", "rejectcomplete@test.com", "1234567895", "5 Test St")
    product = Product.create(db, "Reject Complete Product", "Desc", 10.0, 100, "cat-e")
    Stock.upsert(db, product['id'], 10, "LOT104", "2026-12-31", "Warehouse A")

    # Create as pending with quantity that fits current stock (10 <= 10)
    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-REJECT-COMPLETE-001',
        'status': 'pending',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['10'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)
    assert response.status_code == 200

    sales = Sale.get_all(db)
    sale = next(s for s in sales if s['sale_number'] == 'SALE-REJECT-COMPLETE-001')

    # Stock drops (e.g. consumed by another sale) after this one was created as
    # pending, so by completion time there isn't enough left.
    Stock.adjust_quantity(db, product['id'], -7)  # 10 -> 3, less than the 10 requested

    # Attempt to complete - should be rejected because stock (3) < requested (10)
    response = client.post(f'/sales/{sale["id"]}/update-status', data={
        'status': 'completed'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Reject Complete Product' in response.data

    # Status should remain unchanged
    unchanged_sale = Sale.get_by_id(db, sale['id'])
    assert unchanged_sale['status'] == 'pending'

    # Stock should remain unchanged
    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 3


def test_sale_update_status_already_completed_does_not_double_deduct(client, db):
    login_as_admin(client, db)

    customer = Customer.create(db, "Double Deduct Customer", "doublededuct@test.com", "1234567896", "6 Test St")
    product = Product.create(db, "Double Deduct Product", "Desc", 10.0, 100, "cat-f")
    Stock.upsert(db, product['id'], 40, "LOT105", "2026-12-31", "Warehouse A")

    # Create as completed - deducts 12 immediately
    response = client.post('/sales/create', data={
        'customer_id': customer['id'],
        'sale_number': 'SALE-DOUBLE-DEDUCT-001',
        'status': 'completed',
        'sale_date': '2026-07-16',
        'payment_method': 'cash',
        'notes': '',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['12'],
        'item_unit_price[]': ['10.00']
    }, follow_redirects=True)
    assert response.status_code == 200

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 28

    sales = Sale.get_all(db)
    sale = next(s for s in sales if s['sale_number'] == 'SALE-DOUBLE-DEDUCT-001')

    # Update status to completed again - should not deduct again
    response = client.post(f'/sales/{sale["id"]}/update-status', data={
        'status': 'completed'
    }, follow_redirects=True)
    assert response.status_code == 200

    stock = Stock.get_by_product_id(db, product['id'])
    assert stock['quantity'] == 28  # unchanged, no double deduction
