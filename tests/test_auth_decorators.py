import pytest
from app.models.user import User
from app.auth import login_required, admin_required
from flask import Flask

def test_login_required_decorator(client, db):
    # Create a test user
    user = User.create(db, "testuser", "testpass", "Test User", "staff")
    
    # Create a test route with login_required
    @client.application.route('/protected')
    @login_required
    def protected_route():
        return "Protected Content"
    
    # Test access without login - should redirect to login
    response = client.get('/protected', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data
    
    # Test access with login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    response = client.get('/protected')
    assert response.status_code == 200
    assert b'Protected Content' in response.data

def test_admin_required_decorator(client, db):
    # Create a test user
    user = User.create(db, "testuser", "testpass", "Test User", "staff")
    
    # Create a test route with admin_required
    @client.application.route('/admin-only')
    @admin_required
    def admin_route():
        return "Admin Content"
    
    # Test access with non-admin user
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    response = client.get('/admin-only')
    assert response.status_code == 403  # Forbidden
    
    # Test access with admin user
    admin_user = User.create(db, "adminuser", "adminpass", "Admin User", "admin")
    client.post('/auth/login', data={
        'username': 'adminuser',
        'password': 'adminpass'
    })
    
    response = client.get('/admin-only')
    assert response.status_code == 200
    assert b'Admin Content' in response.data