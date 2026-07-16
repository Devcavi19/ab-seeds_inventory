import pytest
from flask import url_for
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.user import User

def test_purchase_order_routes(client, db):
    # Create a test admin user
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Login as admin
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200
    
    # Create test supplier
    supplier = Supplier.create(db, "Test Supplier", "John Doe", "1234567890", 
                              "supplier@test.com", "123 Test St", "Test supplier")
    
    # Create test product
    product = Product.create(db, "Test Product", "Test description", 10.99, 100, "test-category-id")
    
    # Test list page
    response = client.get('/purchases/')
    assert response.status_code == 200
    assert b'Purchase Orders' in response.data
    
    # Test create page
    response = client.get('/purchases/create')
    assert response.status_code == 200
    assert b'Create Purchase Order' in response.data
    
    # Test create submission
    response = client.post('/purchases/create', data={
        'supplier_id': supplier['id'],
        'order_number': 'PO-TEST-001',
        'status': 'pending',
        'order_date': '2026-07-16',
        'notes': 'Test order for routes',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['10'],
        'item_unit_cost[]': ['5.99']
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Purchase order created successfully' in response.data
    
    # Get the created order
    orders = PurchaseOrder.get_all(db)
    created_order = None
    for order in orders:
        if order['order_number'] == 'PO-TEST-001':
            created_order = order
            break
    
    assert created_order is not None
    
    # Test view page
    response = client.get(f'/purchases/{created_order["id"]}/view')
    assert response.status_code == 200
    assert b'PO-TEST-001' in response.data
    
    # Test edit page
    response = client.get(f'/purchases/{created_order["id"]}/edit')
    assert response.status_code == 200
    assert b'Edit Purchase Order' in response.data
    
    # Test edit submission
    response = client.post(f'/purchases/{created_order["id"]}/edit', data={
        'supplier_id': supplier['id'],
        'order_number': 'PO-TEST-001-UPDATED',
        'status': 'completed',
        'order_date': '2026-07-17',
        'notes': 'Updated test order',
        'item_product_id[]': [product['id']],
        'item_quantity[]': ['15'],
        'item_unit_cost[]': ['6.99']
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Purchase order updated successfully' in response.data
    
    # Test update status
    response = client.post(f'/purchases/{created_order["id"]}/update-status', data={
        'status': 'received'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Purchase order status updated successfully' in response.data
    
    # Verify the order status was updated
    updated_order = PurchaseOrder.get_by_id(db, created_order['id'])
    assert updated_order['status'] == 'received'