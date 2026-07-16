import pytest
from app.models.stock import Stock
from app.models.product import Product

def test_stock_upsert_and_get(db):
    # Create a test product first
    product = Product.create(db, "Test Product", "Description", 10.99, 100, "test-category-id")
    product_id = product['id']
    
    # Test upsert (create)
    stock = Stock.upsert(db, product_id, 50, "LOT001", "2026-12-31", "Warehouse A")
    assert stock['product_id'] == product_id
    assert stock['quantity'] == 50
    assert stock['lot_number'] == "LOT001"
    assert stock['expiry_date'] == "2026-12-31"
    assert stock['location'] == "Warehouse A"
    
    # Test upsert (update)
    updated_stock = Stock.upsert(db, product_id, 75, "LOT002", "2027-01-31", "Warehouse B")
    assert updated_stock['quantity'] == 75
    assert updated_stock['lot_number'] == "LOT002"
    
    # Test get by product id
    fetched = Stock.get_by_product_id(db, product_id)
    assert fetched['quantity'] == 75

def test_stock_get_all(db):
    # Create test products
    product1 = Product.create(db, "Product 1", "Desc 1", 5.99, 50, "cat1")
    product2 = Product.create(db, "Product 2", "Desc 2", 7.99, 30, "cat2")
    
    # Create stock entries
    Stock.upsert(db, product1['id'], 100, "LOT1", "2026-12-31", "Location A")
    Stock.upsert(db, product2['id'], 50, "LOT2", "2027-01-31", "Location B")
    
    # Test get all
    stocks = Stock.get_all(db)
    assert len(stocks) >= 2
    assert any(s['product_id'] == product1['id'] for s in stocks)
    assert any(s['product_id'] == product2['id'] for s in stocks)

def test_stock_adjust_quantity(db):
    # Create test product and stock
    product = Product.create(db, "Adjust Product", "Desc", 8.99, 40, "cat1")
    Stock.upsert(db, product['id'], 100, "LOT1", "2026-12-31", "Location A")
    
    # Test positive adjustment
    adjusted = Stock.adjust_quantity(db, product['id'], 25)
    assert adjusted['quantity'] == 125
    
    # Test negative adjustment
    adjusted = Stock.adjust_quantity(db, product['id'], -10)
    assert adjusted['quantity'] == 115

def test_stock_get_low_stock(db):
    # Create test products and stock
    product1 = Product.create(db, "Low Product", "Desc", 3.99, 5, "cat1")
    product2 = Product.create(db, "Normal Product", "Desc", 4.99, 50, "cat2")
    
    Stock.upsert(db, product1['id'], 10, "LOT1", "2026-12-31", "Location A")
    Stock.upsert(db, product2['id'], 100, "LOT2", "2027-01-31", "Location B")
    
    # Test get low stock (threshold = 20)
    low_stocks = Stock.get_low_stock(db, 20)
    assert len(low_stocks) >= 1
    assert any(s['product_id'] == product1['id'] for s in low_stocks)
    assert not any(s['product_id'] == product2['id'] for s in low_stocks)