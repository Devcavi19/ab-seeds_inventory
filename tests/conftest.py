import pytest
import os
import tempfile
from app import create_app

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'TURSO_DATABASE_URL': None,
        'TURSO_AUTH_TOKEN': None,
        'SECRET_KEY': 'test-secret-key',
    })
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    with app.app_context():
        from app.extensions import get_db
        yield get_db()


class AuthActions:
    def __init__(self, client):
        self.client = client
    
    def login(self, username='admin', password='password123'):
        return self.client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )
    
    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)