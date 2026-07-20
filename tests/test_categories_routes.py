import pytest
from app.models.category import Category
from app.models.user import User

def test_categories_routes(client, db):
    # Create a test admin user
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Test list categories (should redirect to login when not authenticated)
    response = client.get('/categories/')
    assert response.status_code == 302  # Redirect to login
    
    # Login as admin first
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})
    
    # Test list categories
    response = client.get('/categories/')
    assert response.status_code == 200
    assert b'Category Management' in response.data
    
    # Test create category
    response = client.post('/categories/create', data={'name': 'Vegetables', 'description': 'All vegetable seeds'})
    assert response.status_code == 302  # Redirect after creation
    
    # Verify category was created
    categories = Category.get_all(db)
    assert len(categories) == 1
    assert categories[0]['name'] == 'Vegetables'
    
    # Test edit category
    category_id = categories[0]['id']
    response = client.post(f'/categories/{category_id}/edit', data={'name': 'Tropical Vegetables', 'description': 'Tropical vegetable seeds'})
    assert response.status_code == 302  # Redirect after update
    
    # Verify category was updated
    updated_category = Category.get_by_id(db, category_id)
    assert updated_category['name'] == 'Tropical Vegetables'
    
    # Test delete category
    response = client.post(f'/categories/{category_id}/delete')
    assert response.status_code == 302  # Redirect after deletion
    
    # Verify category was soft deleted
    deleted_category = Category.get_by_id(db, category_id)
    assert deleted_category['is_deleted'] == True
    
    # Verify category is no longer in the list
    categories = Category.get_all(db)
    assert len(categories) == 0


def test_export_categories_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/categories/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=categories.csv' in response.headers['Content-Disposition']