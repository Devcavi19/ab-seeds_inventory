import pytest
from app.models.user import User

def test_user_create_and_get(db):
    user = User.create(db, "admin", "password123", "Admin User", "admin")
    assert user['username'] == "admin"
    assert user['role'] == "admin"
    
    fetched = User.get_by_id(db, user['id'])
    assert fetched['username'] == "admin"

def test_verify_password(db):
    user = User.create(db, "staff", "pass123", "Staff", "staff")
    assert User.verify_password(user['password_hash'], "pass123") is True
    assert User.verify_password(user['password_hash'], "wrong") is False