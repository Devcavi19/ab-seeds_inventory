import pytest
from app.models.user import User

def test_login_logout(client, db):
    # Create a test user
    user = User.create(db, "testuser", "testpass", "Test User", "staff")
    
    # Test login page loads
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    
    # Test successful login
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Test logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_invalid_login(client, db):
    # Test invalid login
    response = client.post('/auth/login', data={
        'username': 'nonexistent',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data