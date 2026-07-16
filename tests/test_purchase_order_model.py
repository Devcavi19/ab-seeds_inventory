import pytest
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.product import Product

def test_purchase_order_create_and_get(db):
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier", "John Doe", "1234567890", 
                              "supplier@test.com", "123 Test St", "Test supplier")
    
    # Test create purchase order
    order = PurchaseOrder.create(
        db, 
        supplier['id'], 
        "PO-001", 
        "pending", 
        "2026-07-16",
        notes="Test order"
    )
    
    assert order['supplier_id'] == supplier['id']
    assert order['order_number'] == "PO-001"
    assert order['status'] == "pending"
    assert order['order_date'] == "2026-07-16"
    assert order['notes'] == "Test order"
    
    # Test get by id
    fetched = PurchaseOrder.get_by_id(db, order['id'])
    assert fetched['id'] == order['id']
    assert fetched['order_number'] == "PO-001"

def test_purchase_order_get_all(db):
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier 2", "Jane Doe", "9876543210",
                              "supplier2@test.com", "456 Test Ave", "Test supplier 2")
    
    # Create multiple purchase orders
    order1 = PurchaseOrder.create(db, supplier['id'], "PO-002", "pending", "2026-07-16")
    order2 = PurchaseOrder.create(db, supplier['id'], "PO-003", "completed", "2026-07-15")
    
    # Test get all
    orders = PurchaseOrder.get_all(db)
    assert len(orders) >= 2
    assert any(o['id'] == order1['id'] for o in orders)
    assert any(o['id'] == order2['id'] for o in orders)

def test_purchase_order_update(db):
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier 3", "Bob Smith", "5551234567",
                              "supplier3@test.com", "789 Test Blvd", "Test supplier 3")
    
    # Create purchase order
    order = PurchaseOrder.create(db, supplier['id'], "PO-004", "pending", "2026-07-16")
    
    # Update purchase order
    updated = PurchaseOrder.update(
        db, 
        order['id'],
        supplier['id'],
        "PO-004-UPDATED",
        "completed",
        "2026-07-17",
        "2026-07-18",
        1000.0,
        "Updated notes"
    )
    
    assert updated['order_number'] == "PO-004-UPDATED"
    assert updated['status'] == "completed"
    assert updated['order_date'] == "2026-07-17"
    assert updated['received_date'] == "2026-07-18"
    assert updated['total_amount'] == 1000.0
    assert updated['notes'] == "Updated notes"

def test_purchase_order_update_status(db):
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier 4", "Alice Johnson", "1112223333",
                              "supplier4@test.com", "321 Test Rd", "Test supplier 4")
    
    # Create purchase order
    order = PurchaseOrder.create(db, supplier['id'], "PO-005", "pending", "2026-07-16")
    
    # Update status
    updated = PurchaseOrder.update_status(db, order['id'], "completed")
    assert updated['status'] == "completed"

def test_purchase_order_update_total_amount(db):
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier 5", "Charlie Brown", "4445556666",
                              "supplier5@test.com", "654 Test Ln", "Test supplier 5")
    
    # Create purchase order
    order = PurchaseOrder.create(db, supplier['id'], "PO-006", "pending", "2026-07-16")
    
    # Update total amount
    updated = PurchaseOrder.update_total_amount(db, order['id'], 1500.50)
    assert updated['total_amount'] == 1500.50

def test_purchase_order_item_create_and_get(db):
    # Create test supplier and product
    supplier = Supplier.create(db, "Test Supplier 6", "David Wilson", "7778889999",
                              "supplier6@test.com", "987 Test Dr", "Test supplier 6")
    product = Product.create(db, "Test Product", "Test description", 10.99, 100, "test-category-id")
    order = PurchaseOrder.create(db, supplier['id'], "PO-007", "pending", "2026-07-16")
    
    # Create purchase order item
    item = PurchaseOrderItem.create(
        db, 
        order['id'],
        product['id'],
        50,
        5.99
    )
    
    assert item['purchase_order_id'] == order['id']
    assert item['product_id'] == product['id']
    assert item['quantity'] == 50
    assert item['unit_cost'] == 5.99
    assert item['received_quantity'] == 0
    
    # Test get by id
    fetched = PurchaseOrderItem.get_by_id(db, item['id'])
    assert fetched['id'] == item['id']
    assert fetched['quantity'] == 50

def test_purchase_order_item_get_by_order_id(db):
    # Create test supplier and products
    supplier = Supplier.create(db, "Test Supplier 7", "Eve Davis", "9990001111",
                              "supplier7@test.com", "111 Test Way", "Test supplier 7")
    product1 = Product.create(db, "Test Product 1", "Desc 1", 8.99, 50, "cat1")
    product2 = Product.create(db, "Test Product 2", "Desc 2", 9.99, 30, "cat2")
    order = PurchaseOrder.create(db, supplier['id'], "PO-008", "pending", "2026-07-16")
    
    # Create multiple items
    item1 = PurchaseOrderItem.create(db, order['id'], product1['id'], 25, 4.99)
    item2 = PurchaseOrderItem.create(db, order['id'], product2['id'], 35, 5.99)
    
    # Test get by order id
    items = PurchaseOrderItem.get_by_order_id(db, order['id'])
    assert len(items) >= 2
    assert any(i['id'] == item1['id'] for i in items)
    assert any(i['id'] == item2['id'] for i in items)

def test_purchase_order_item_update(db):
    # Create test supplier and product
    supplier = Supplier.create(db, "Test Supplier 8", "Frank Miller", "2223334444",
                              "supplier8@test.com", "222 Test Ct", "Test supplier 8")
    product = Product.create(db, "Test Product 3", "Desc 3", 7.99, 40, "cat3")
    order = PurchaseOrder.create(db, supplier['id'], "PO-009", "pending", "2026-07-16")
    item = PurchaseOrderItem.create(db, order['id'], product['id'], 20, 3.99)
    
    # Update item
    updated = PurchaseOrderItem.update(db, item['id'], 30, 4.99, 25)
    assert updated['quantity'] == 30
    assert updated['unit_cost'] == 4.99
    assert updated['received_quantity'] == 25

def test_purchase_order_item_update_received_quantity(db):
    # Create test supplier and product
    supplier = Supplier.create(db, "Test Supplier 9", "Grace Lee", "3334445555",
                              "supplier9@test.com", "333 Test Pl", "Test supplier 9")
    product = Product.create(db, "Test Product 4", "Desc 4", 6.99, 60, "cat4")
    order = PurchaseOrder.create(db, supplier['id'], "PO-010", "pending", "2026-07-16")
    item = PurchaseOrderItem.create(db, order['id'], product['id'], 40, 2.99)
    
    # Update received quantity
    updated = PurchaseOrderItem.update_received_quantity(db, item['id'], 35)
    assert updated['received_quantity'] == 35

def test_purchase_order_item_delete(db):
    # Create test supplier and product
    supplier = Supplier.create(db, "Test Supplier 10", "Henry Clark", "4445556666",
                              "supplier10@test.com", "444 Test Cir", "Test supplier 10")
    product = Product.create(db, "Test Product 5", "Desc 5", 5.99, 70, "cat5")
    order = PurchaseOrder.create(db, supplier['id'], "PO-011", "pending", "2026-07-16")
    item = PurchaseOrderItem.create(db, order['id'], product['id'], 15, 1.99)
    
    # Delete item
    result = PurchaseOrderItem.delete(db, item['id'])
    assert result == True
    
    # Verify deletion
    deleted = PurchaseOrderItem.get_by_id(db, item['id'])
    assert deleted is None

def test_purchase_order_item_delete_by_order_id(db):
    # Create test supplier and products
    supplier = Supplier.create(db, "Test Supplier 11", "Ivy Adams", "5556667777",
                              "supplier11@test.com", "555 Test Ave", "Test supplier 11")
    product = Product.create(db, "Test Product 6", "Desc 6", 4.99, 80, "cat6")
    order = PurchaseOrder.create(db, supplier['id'], "PO-012", "pending", "2026-07-16")
    
    # Create multiple items
    item1 = PurchaseOrderItem.create(db, order['id'], product['id'], 10, 0.99)
    item2 = PurchaseOrderItem.create(db, order['id'], product['id'], 20, 1.99)
    
    # Delete all items for order
    count = PurchaseOrderItem.delete_by_order_id(db, order['id'])
    assert count >= 2
    
    # Verify deletion
    items = PurchaseOrderItem.get_by_order_id(db, order['id'])
    assert len(items) == 0