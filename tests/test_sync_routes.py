from app.models.user import User


def test_sync_status_as_admin_returns_expected_keys(client, db):
    User.create(db, "admin", "password123", "Admin User", "admin")
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})

    response = client.get('/sync/status')
    assert response.status_code == 200

    data = response.get_json()
    assert set(data.keys()) == {
        'available', 'configured', 'last_sync_at', 'last_sync_status', 'last_error'
    }


def test_sync_now_as_admin_returns_not_configured(client, db):
    User.create(db, "admin", "password123", "Admin User", "admin")
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})

    response = client.post('/sync/now')
    assert response.status_code == 200

    data = response.get_json()
    # conftest.py sets TURSO_DATABASE_URL/TURSO_AUTH_TOKEN to None for every
    # test, so sync is never configured here. The exact status still depends
    # on whether libsql_experimental itself is importable in this
    # environment: 'not_configured' if it is, 'unavailable' if it isn't
    # (this sandbox does not have it installed - see task11-brief.md).
    sync_service = client.application.sync_service
    expected_status = 'not_configured' if sync_service.is_available() else 'unavailable'
    assert data['status'] == expected_status
    assert data['error'] is None


def test_sync_status_rejects_non_admin(client, db):
    User.create(db, "staffuser", "password123", "Staff User", "staff")
    client.post('/auth/login', data={'username': 'staffuser', 'password': 'password123'})

    response = client.get('/sync/status')
    assert response.status_code == 403


def test_sync_now_rejects_non_admin(client, db):
    User.create(db, "staffuser", "password123", "Staff User", "staff")
    client.post('/auth/login', data={'username': 'staffuser', 'password': 'password123'})

    response = client.post('/sync/now')
    assert response.status_code == 403


def test_sync_status_rejects_logged_out(client):
    response = client.get('/sync/status')
    assert response.status_code in (302, 401, 403)


def test_sync_now_rejects_logged_out(client):
    response = client.post('/sync/now')
    assert response.status_code in (302, 401, 403)
