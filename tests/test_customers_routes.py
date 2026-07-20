import pytest
from app.models.customer import Customer
from app.models.user import User

def test_customers_routes(client, db):
    # Create a test admin user
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Test list customers (should redirect to login when not authenticated)
    response = client.get('/customers/')
    assert response.status_code == 302
    
    # Login as admin
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200
    
    # Test list customers (empty)
    response = client.get('/customers/')
    assert response.status_code == 200
    assert b'Customer Management' in response.data
    
    # Test create customer form
    response = client.get('/customers/create')
    assert response.status_code == 200
    assert b'Create New Customer' in response.data
    
    # Test create customer
    response = client.post('/customers/create', data={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '123-456-7890',
        'address': '123 Test St'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer created successfully' in response.data
    
    # Get the created customer
    customers = Customer.get_all(db)
    customer_id = customers[0]['id']
    
    # Test edit customer form
    response = client.get(f'/customers/{customer_id}/edit')
    assert response.status_code == 200
    assert b'Edit Customer' in response.data
    
    # Test update customer
    response = client.post(f'/customers/{customer_id}/edit', data={
        'name': 'Updated Customer',
        'email': 'updated@example.com',
        'phone': '987-654-3210',
        'address': '456 Updated Ave'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer updated successfully' in response.data
    
    # Test delete customer
    response = client.post(f'/customers/{customer_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer deleted successfully' in response.data
    
    # Verify customer is soft deleted
    deleted_customer = Customer.get_by_id(db, customer_id)
    assert deleted_customer['is_active'] == False

def test_export_customers_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/customers/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=customers.csv' in response.headers['Content-Disposition']
