import pytest
from app.models.supplier import Supplier

def test_supplier_create_and_get(db):
    supplier = Supplier.create(db, "SeedCo", "John Doe", "123-456-7890", "john@seedco.com", "123 Main St")
    assert supplier['name'] == "SeedCo"
    assert supplier['contact_person'] == "John Doe"
    assert supplier['phone'] == "123-456-7890"
    assert supplier['email'] == "john@seedco.com"
    assert supplier['address'] == "123 Main St"
    
    fetched = Supplier.get_by_id(db, supplier['id'])
    assert fetched['name'] == "SeedCo"

def test_supplier_update(db):
    supplier = Supplier.create(db, "AgriSupplies", "Jane Smith", "987-654-3210", "jane@agrisupplies.com", "456 Oak Ave")
    updated = Supplier.update(db, supplier['id'], "AgriSupplies Inc", "Jane Smith", "987-654-3210", "jane@agrisupplies.com", "456 Oak Ave", "Preferred supplier")
    assert updated['name'] == "AgriSupplies Inc"
    assert updated['notes'] == "Preferred supplier"

def test_supplier_soft_delete(db):
    supplier = Supplier.create(db, "GreenThumb", "Bob Johnson", "555-123-4567", "bob@greenthumb.com", "789 Pine Rd")
    deleted = Supplier.soft_delete(db, supplier['id'])
    assert deleted['is_active'] == False
    
    # Should still be retrievable
    fetched = Supplier.get_by_id(db, supplier['id'])
    assert fetched['is_active'] == False

def test_supplier_list_all(db):
    Supplier.create(db, "Supplier 1", "Person 1", "111-111-1111", "supplier1@test.com", "Address 1")
    Supplier.create(db, "Supplier 2", "Person 2", "222-222-2222", "supplier2@test.com", "Address 2")
    
    suppliers = Supplier.get_all(db)
    assert len(suppliers) >= 2
    assert any(sup['name'] == "Supplier 1" for sup in suppliers)
    assert any(sup['name'] == "Supplier 2" for sup in suppliers)