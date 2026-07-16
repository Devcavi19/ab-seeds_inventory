import pytest
from app.models.product import Product
from app.models.category import Category

def test_product_create_and_get(db):
    # Create a category first
    category = Category.create(db, "Vegetables", "All vegetable seeds")
    
    # Create a product
    product = Product.create(db, "Tomato Seeds", "Organic tomato seeds", 9.99, 100, category['id'])
    assert product['name'] == "Tomato Seeds"
    assert product['description'] == "Organic tomato seeds"
    assert product['price'] == 9.99
    assert product['stock_quantity'] == 100
    assert product['category_id'] == category['id']
    
    # Get by ID
    fetched = Product.get_by_id(db, product['id'])
    assert fetched['name'] == "Tomato Seeds"

def test_product_update(db):
    category = Category.create(db, "Fruits", "All fruit seeds")
    product = Product.create(db, "Apple Seeds", "Organic apple seeds", 5.99, 50, category['id'])
    
    updated = Product.update(db, product['id'], "Apple Tree Seeds", "Premium apple tree seeds", 7.99, 75, category['id'])
    assert updated['name'] == "Apple Tree Seeds"
    assert updated['description'] == "Premium apple tree seeds"
    assert updated['price'] == 7.99
    assert updated['stock_quantity'] == 75

def test_product_soft_delete(db):
    category = Category.create(db, "Herbs", "All herb seeds")
    product = Product.create(db, "Basil Seeds", "Organic basil seeds", 3.99, 200, category['id'])
    
    deleted = Product.soft_delete(db, product['id'])
    assert deleted['is_deleted'] == True
    
    # Should still be retrievable
    fetched = Product.get_by_id(db, product['id'])
    assert fetched['is_deleted'] == True

def test_product_list_all(db):
    category = Category.create(db, "Flowers", "All flower seeds")
    Product.create(db, "Rose Seeds", "Organic rose seeds", 8.99, 150, category['id'])
    Product.create(db, "Tulip Seeds", "Organic tulip seeds", 6.99, 120, category['id'])
    
    products = Product.get_all(db)
    assert len(products) >= 2
    assert any(prod['name'] == "Rose Seeds" for prod in products)
    assert any(prod['name'] == "Tulip Seeds" for prod in products)

def test_product_search(db):
    category = Category.create(db, "Vegetables", "All vegetable seeds")
    Product.create(db, "Tomato Seeds", "Organic tomato seeds", 9.99, 100, category['id'])
    Product.create(db, "Cucumber Seeds", "Organic cucumber seeds", 4.99, 200, category['id'])
    Product.create(db, "Carrot Seeds", "Organic carrot seeds", 3.99, 150, category['id'])
    
    results = Product.search(db, "tomato")
    assert len(results) == 1
    assert results[0]['name'] == "Tomato Seeds"

def test_product_filter_by_category(db):
    category1 = Category.create(db, "Vegetables", "All vegetable seeds")
    category2 = Category.create(db, "Fruits", "All fruit seeds")
    
    Product.create(db, "Tomato Seeds", "Organic tomato seeds", 9.99, 100, category1['id'])
    Product.create(db, "Apple Seeds", "Organic apple seeds", 5.99, 50, category2['id'])
    Product.create(db, "Cucumber Seeds", "Organic cucumber seeds", 4.99, 200, category1['id'])
    
    veg_products = Product.get_by_category(db, category1['id'])
    assert len(veg_products) == 2
    assert all(prod['category_id'] == category1['id'] for prod in veg_products)