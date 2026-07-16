import pytest
from app.models.customer import Customer

def test_customer_create_and_get(db):
    customer = Customer.create(db, "John Doe", "john@example.com", "123-456-7890", "123 Main St")
    assert customer['name'] == "John Doe"
    assert customer['email'] == "john@example.com"
    assert customer['phone'] == "123-456-7890"
    assert customer['address'] == "123 Main St"
    
    fetched = Customer.get_by_id(db, customer['id'])
    assert fetched['name'] == "John Doe"

def test_customer_update(db):
    customer = Customer.create(db, "Jane Smith", "jane@example.com", "987-654-3210", "456 Oak Ave")
    updated = Customer.update(db, customer['id'], "Jane Doe", "jane.doe@example.com", "987-654-3210", "456 Oak Avenue")
    assert updated['name'] == "Jane Doe"
    assert updated['email'] == "jane.doe@example.com"
    assert updated['address'] == "456 Oak Avenue"

def test_customer_soft_delete(db):
    customer = Customer.create(db, "Bob Johnson", "bob@example.com", "555-123-4567", "789 Pine Rd")
    deleted = Customer.soft_delete(db, customer['id'])
    assert deleted['is_active'] == False
    
    # Should still be retrievable
    fetched = Customer.get_by_id(db, customer['id'])
    assert fetched['is_active'] == False

def test_customer_list_all(db):
    Customer.create(db, "Customer 1", "customer1@example.com", "111-111-1111", "Address 1")
    Customer.create(db, "Customer 2", "customer2@example.com", "222-222-2222", "Address 2")
    
    customers = Customer.get_all(db)
    assert len(customers) >= 2
    assert any(cust['name'] == "Customer 1" for cust in customers)
    assert any(cust['name'] == "Customer 2" for cust in customers)