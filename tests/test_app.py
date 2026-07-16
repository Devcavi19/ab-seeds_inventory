from app.extensions import get_db

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

def test_database_connection(app, db):
    with app.app_context():
        result = db.execute("SELECT 1").fetchone()
        assert result[0] == 1

def test_migrations_run(app, db):
    with app.app_context():
        # Verify tables exist
        result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        assert result is not None