import pytest
from app.models.product import Product
from app.models.category import Category

def test_products_routes(client, db):
    # Create a test admin user
    from app.models.user import User
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    
    # Create a category for testing
    category = Category.create(db, "Test Category", "Test description")
    
    # Test list products (should redirect to login when not authenticated)
    response = client.get('/products/')
    assert response.status_code == 302  # Redirect to login
    
    # Login as admin first
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})
    
    # Test list products
    response = client.get('/products/')
    assert response.status_code == 200
    assert b'Product Management' in response.data
    
    # Test create product
    response = client.post('/products/create', data={
        'name': 'Test Product',
        'description': 'Test product description',
        'price': '9.99',
        'stock_quantity': '100',
        'category_id': category['id']
    })
    assert response.status_code == 302  # Redirect after creation
    
    # Verify product was created
    products = Product.get_all(db)
    assert len(products) == 1
    assert products[0]['name'] == 'Test Product'
    
    # Test edit product
    product_id = products[0]['id']
    response = client.post(f'/products/{product_id}/edit', data={
        'name': 'Updated Product',
        'description': 'Updated description',
        'price': '14.99',
        'stock_quantity': '150',
        'category_id': category['id']
    })
    assert response.status_code == 302  # Redirect after update
    
    # Verify product was updated
    updated_product = Product.get_by_id(db, product_id)
    assert updated_product['name'] == 'Updated Product'
    assert updated_product['price'] == 14.99
    
    # Test delete product
    response = client.post(f'/products/{product_id}/delete')
    assert response.status_code == 302  # Redirect after deletion
    
    # Verify product was soft deleted
    deleted_product = Product.get_by_id(db, product_id)
    assert deleted_product['is_deleted'] == True
    
    # Verify product is no longer in the list
    products = Product.get_all(db)
    assert len(products) == 0
    
    # Test search functionality
    Product.create(db, "Tomato Seeds", "Organic tomato seeds", 9.99, 100, category['id'])
    Product.create(db, "Cucumber Seeds", "Organic cucumber seeds", 4.99, 200, category['id'])
    
    response = client.get('/products/?search=tomato')
    assert response.status_code == 200
    assert b'Tomato Seeds' in response.data
    assert b'Cucumber Seeds' not in response.data
    
    # Test category filtering
    category2 = Category.create(db, "Fruits", "Fruit seeds")
    Product.create(db, "Apple Seeds", "Organic apple seeds", 5.99, 50, category2['id'])
    
    response = client.get(f'/products/?category_id={category['id']}')
    assert response.status_code == 200
    assert b'Tomato Seeds' in response.data
    assert b'Cucumber Seeds' in response.data
    assert b'Apple Seeds' not in response.data

def test_export_products_csv(client, auth, db):
    # Create a test admin user
    from app.models.user import User
    User.create(db, "admin", "password123", "Admin User", "admin")
    
    auth.login()
    response = client.get('/products/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=products.csv' in response.headers['Content-Disposition']
