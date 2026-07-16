import pytest
from app.models.category import Category

def test_category_create_and_get(db):
    category = Category.create(db, "Vegetables", "All vegetable seeds")
    assert category['name'] == "Vegetables"
    assert category['description'] == "All vegetable seeds"
    
    fetched = Category.get_by_id(db, category['id'])
    assert fetched['name'] == "Vegetables"

def test_category_update(db):
    category = Category.create(db, "Fruits", "All fruit seeds")
    updated = Category.update(db, category['id'], "Tropical Fruits", "Tropical fruit seeds only")
    assert updated['name'] == "Tropical Fruits"
    assert updated['description'] == "Tropical fruit seeds only"

def test_category_soft_delete(db):
    category = Category.create(db, "Herbs", "All herb seeds")
    deleted = Category.soft_delete(db, category['id'])
    assert deleted['is_deleted'] == True
    
    # Should still be retrievable
    fetched = Category.get_by_id(db, category['id'])
    assert fetched['is_deleted'] == True

def test_category_list_all(db):
    Category.create(db, "Category 1", "Description 1")
    Category.create(db, "Category 2", "Description 2")
    
    categories = Category.get_all(db)
    assert len(categories) >= 2
    assert any(cat['name'] == "Category 1" for cat in categories)
    assert any(cat['name'] == "Category 2" for cat in categories)