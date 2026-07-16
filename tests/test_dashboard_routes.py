import pytest
from app.models.user import User
from app.models.customer import Customer
from app.models.sale import Sale


def test_dashboard_requires_login(client, db):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_favicon_link_rendered_in_head(client, db):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'<link rel="icon" type="image/png" href="/static/images/icon.png">' in response.data


def test_dashboard_reachable_by_admin(client, db):
    User.create(db, "admin", "password123", "Admin User", "admin")
    client.post('/auth/login', data={'username': 'admin', 'password': 'password123'})

    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_dashboard_reachable_by_non_admin(client, db):
    # Unlike every other data-listing blueprint, the dashboard must be reachable
    # by a logged-in non-admin (staff) user.
    User.create(db, "staffuser", "password123", "Staff User", "staff")
    client.post('/auth/login', data={'username': 'staffuser', 'password': 'password123'})

    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_dashboard_shows_summary_data(client, db):
    User.create(db, "admin2", "password123", "Admin Two", "admin")
    client.post('/auth/login', data={'username': 'admin2', 'password': 'password123'})

    customer = Customer.create(db, "Dash Customer", "dash@test.com", "123", "Addr")
    sale = Sale.create(db, customer['id'], "SALE-DASH-1", "completed", "2026-07-16")
    Sale.update_total_amount(db, sale['id'], 42.0)

    response = client.get('/')
    assert response.status_code == 200
    assert b'Total Products' in response.data
    assert b'Total Customers' in response.data
    assert b'Low Stock' in response.data


def test_login_as_admin_redirects_to_dashboard(client, db):
    User.create(db, "adminredirect", "password123", "Admin Redirect", "admin")

    response = client.post('/auth/login', data={
        'username': 'adminredirect',
        'password': 'password123'
    })

    assert response.status_code == 302
    assert response.headers['Location'] == '/'
    assert '/management/users' not in response.headers['Location']


def test_login_as_non_admin_redirects_to_dashboard(client, db):
    User.create(db, "staffredirect", "password123", "Staff Redirect", "staff")

    response = client.post('/auth/login', data={
        'username': 'staffredirect',
        'password': 'password123'
    })

    assert response.status_code == 302
    assert response.headers['Location'] == '/'
