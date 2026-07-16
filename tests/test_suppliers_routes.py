import pytest
from app.models.supplier import Supplier
from app.models.user import User

def test_suppliers_routes(client, db):
    # Create a test admin user
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Test list suppliers (should redirect to login when not authenticated)
    response = client.get('/suppliers/')
    assert response.status_code == 302  # Redirect to login
    
    # Login as admin first
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})
    
    # Test list suppliers
    response = client.get('/suppliers/')
    assert response.status_code == 200
    assert b'Supplier Management' in response.data
    
    # Test create supplier
    response = client.post('/suppliers/create', data={
        'name': 'SeedCo',
        'contact_person': 'John Doe',
        'phone': '123-456-7890',
        'email': 'john@seedco.com',
        'address': '123 Main St',
        'notes': 'Preferred supplier'
    })
    assert response.status_code == 302  # Redirect after creation
    
    # Verify supplier was created
    suppliers = Supplier.get_all(db)
    assert len(suppliers) == 1
    assert suppliers[0]['name'] == 'SeedCo'
    
    # Test edit supplier
    supplier_id = suppliers[0]['id']
    response = client.post(f'/suppliers/{supplier_id}/edit', data={
        'name': 'SeedCo Inc',
        'contact_person': 'John Doe',
        'phone': '123-456-7890',
        'email': 'john@seedco.com',
        'address': '123 Main St',
        'notes': 'Preferred supplier - updated'
    })
    assert response.status_code == 302  # Redirect after update
    
    # Verify supplier was updated
    updated_supplier = Supplier.get_by_id(db, supplier_id)
    assert updated_supplier['name'] == 'SeedCo Inc'
    assert updated_supplier['notes'] == 'Preferred supplier - updated'
    
    # Test delete supplier
    response = client.post(f'/suppliers/{supplier_id}/delete')
    assert response.status_code == 302  # Redirect after deletion
    
    # Verify supplier was soft deleted
    deleted_supplier = Supplier.get_by_id(db, supplier_id)
    assert deleted_supplier['is_active'] == False
    
    # Verify supplier is no longer in the list
    suppliers = Supplier.get_all(db)
    assert len(suppliers) == 0