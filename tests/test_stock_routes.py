import pytest
from app.models.stock import Stock
from app.models.product import Product
from app.models.user import User

def test_stock_routes(client, db):
    # Create a test admin user
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Create a test product
    product = Product.create(db, "Stock Product", "Description", 12.99, 100, "test-category-id")
    product_id = product['id']
    
    # Test list stock (should redirect to login when not authenticated)
    response = client.get('/stock/')
    assert response.status_code == 302
    
    # Login as admin
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200
    
    # Test list stock (empty)
    response = client.get('/stock/')
    assert response.status_code == 200
    assert b'Stock Management' in response.data
    
    # Test create stock form
    response = client.get(f'/stock/{product_id}/create')
    assert response.status_code == 200
    assert b'Create Stock' in response.data
    
    # Test create stock
    response = client.post(f'/stock/{product_id}/create', data={
        'quantity': 50,
        'lot_number': 'LOT001',
        'expiry_date': '2026-12-31',
        'location': 'Warehouse A'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Stock created successfully' in response.data
    
    # Test edit stock form
    response = client.get(f'/stock/{product_id}/edit')
    assert response.status_code == 200
    assert b'Edit Stock' in response.data
    
    # Test update stock
    response = client.post(f'/stock/{product_id}/edit', data={
        'quantity': 75,
        'lot_number': 'LOT002',
        'expiry_date': '2027-01-31',
        'location': 'Warehouse B'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Stock updated successfully' in response.data
    
    # Test adjust stock form
    response = client.get(f'/stock/{product_id}/adjust')
    assert response.status_code == 200
    assert b'Adjust Stock' in response.data
    
    # Test adjust stock (positive)
    response = client.post(f'/stock/{product_id}/adjust', data={
        'adjustment': 10,
        'reason': 'Restock'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Stock adjusted successfully' in response.data
    
    # Test low stock view
    response = client.get('/stock/low')
    assert response.status_code == 200
    assert b'Low Stock Alerts' in response.data