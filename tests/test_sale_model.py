import pytest
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.customer import Customer
from app.models.product import Product

def test_sale_create_and_get(db):
    # Create test customer
    customer = Customer.create(db, "Test Customer", "customer@test.com", "1234567890", "123 Test St")

    # Test create sale
    sale = Sale.create(
        db,
        customer['id'],
        "SALE-001",
        "pending",
        "2026-07-16",
        notes="Test sale"
    )

    assert sale['customer_id'] == customer['id']
    assert sale['sale_number'] == "SALE-001"
    assert sale['status'] == "pending"
    assert sale['sale_date'] == "2026-07-16"
    assert sale['notes'] == "Test sale"

    # Test get by id
    fetched = Sale.get_by_id(db, sale['id'])
    assert fetched['id'] == sale['id']
    assert fetched['sale_number'] == "SALE-001"

def test_sale_get_all(db):
    customer = Customer.create(db, "Test Customer 2", "customer2@test.com", "9876543210", "456 Test Ave")

    sale1 = Sale.create(db, customer['id'], "SALE-002", "pending", "2026-07-16")
    sale2 = Sale.create(db, customer['id'], "SALE-003", "completed", "2026-07-15")

    sales = Sale.get_all(db)
    assert len(sales) >= 2
    assert any(s['id'] == sale1['id'] for s in sales)
    assert any(s['id'] == sale2['id'] for s in sales)

def test_sale_update(db):
    customer = Customer.create(db, "Test Customer 3", "customer3@test.com", "5551234567", "789 Test Blvd")

    sale = Sale.create(db, customer['id'], "SALE-004", "pending", "2026-07-16")

    updated = Sale.update(
        db,
        sale['id'],
        customer['id'],
        "SALE-004-UPDATED",
        "completed",
        "2026-07-17",
        "cash",
        1000.0,
        "Updated notes"
    )

    assert updated['sale_number'] == "SALE-004-UPDATED"
    assert updated['status'] == "completed"
    assert updated['sale_date'] == "2026-07-17"
    assert updated['payment_method'] == "cash"
    assert updated['total_amount'] == 1000.0
    assert updated['notes'] == "Updated notes"

def test_sale_update_status(db):
    customer = Customer.create(db, "Test Customer 4", "customer4@test.com", "1112223333", "321 Test Rd")

    sale = Sale.create(db, customer['id'], "SALE-005", "pending", "2026-07-16")

    updated = Sale.update_status(db, sale['id'], "completed")
    assert updated['status'] == "completed"

def test_sale_update_total_amount(db):
    customer = Customer.create(db, "Test Customer 5", "customer5@test.com", "4445556666", "654 Test Ln")

    sale = Sale.create(db, customer['id'], "SALE-006", "pending", "2026-07-16")

    updated = Sale.update_total_amount(db, sale['id'], 1500.50)
    assert updated['total_amount'] == 1500.50

def test_sale_item_create_and_get(db):
    customer = Customer.create(db, "Test Customer 6", "customer6@test.com", "7778889999", "987 Test Dr")
    product = Product.create(db, "Test Product", "Test description", 10.99, 100, "test-category-id")
    sale = Sale.create(db, customer['id'], "SALE-007", "pending", "2026-07-16")

    item = SaleItem.create(
        db,
        sale['id'],
        product['id'],
        5,
        12.99
    )

    assert item['sale_id'] == sale['id']
    assert item['product_id'] == product['id']
    assert item['quantity'] == 5
    assert item['unit_price'] == 12.99

    fetched = SaleItem.get_by_id(db, item['id'])
    assert fetched['id'] == item['id']
    assert fetched['quantity'] == 5

def test_sale_item_get_by_sale_id(db):
    customer = Customer.create(db, "Test Customer 7", "customer7@test.com", "9990001111", "111 Test Way")
    product1 = Product.create(db, "Test Product 1", "Desc 1", 8.99, 50, "cat1")
    product2 = Product.create(db, "Test Product 2", "Desc 2", 9.99, 30, "cat2")
    sale = Sale.create(db, customer['id'], "SALE-008", "pending", "2026-07-16")

    item1 = SaleItem.create(db, sale['id'], product1['id'], 2, 4.99)
    item2 = SaleItem.create(db, sale['id'], product2['id'], 3, 5.99)

    items = SaleItem.get_by_sale_id(db, sale['id'])
    assert len(items) >= 2
    assert any(i['id'] == item1['id'] for i in items)
    assert any(i['id'] == item2['id'] for i in items)

def test_sale_item_update(db):
    customer = Customer.create(db, "Test Customer 8", "customer8@test.com", "2223334444", "222 Test Ct")
    product = Product.create(db, "Test Product 3", "Desc 3", 7.99, 40, "cat3")
    sale = Sale.create(db, customer['id'], "SALE-009", "pending", "2026-07-16")
    item = SaleItem.create(db, sale['id'], product['id'], 2, 3.99)

    updated = SaleItem.update(db, item['id'], 6, 4.99)
    assert updated['quantity'] == 6
    assert updated['unit_price'] == 4.99

def test_sale_item_delete(db):
    customer = Customer.create(db, "Test Customer 9", "customer9@test.com", "3334445555", "333 Test Pl")
    product = Product.create(db, "Test Product 4", "Desc 4", 6.99, 60, "cat4")
    sale = Sale.create(db, customer['id'], "SALE-010", "pending", "2026-07-16")
    item = SaleItem.create(db, sale['id'], product['id'], 4, 2.99)

    result = SaleItem.delete(db, item['id'])
    assert result == True

    deleted = SaleItem.get_by_id(db, item['id'])
    assert deleted is None

def test_sale_item_delete_by_sale_id(db):
    customer = Customer.create(db, "Test Customer 10", "customer10@test.com", "4445556666", "444 Test Cir")
    product = Product.create(db, "Test Product 5", "Desc 5", 5.99, 70, "cat5")
    sale = Sale.create(db, customer['id'], "SALE-011", "pending", "2026-07-16")

    item1 = SaleItem.create(db, sale['id'], product['id'], 1, 0.99)
    item2 = SaleItem.create(db, sale['id'], product['id'], 2, 1.99)

    count = SaleItem.delete_by_sale_id(db, sale['id'])
    assert count >= 2

    items = SaleItem.get_by_sale_id(db, sale['id'])
    assert len(items) == 0
