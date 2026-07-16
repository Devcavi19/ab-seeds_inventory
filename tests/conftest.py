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