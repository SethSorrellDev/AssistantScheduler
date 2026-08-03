"""
Route-level tests covering authentication and role-based access
control. These hit the real Flask test client, exercising the
login form, session handling, and the @role_required decorator.
"""
from tests.conftest import login


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_login_success_redirects_away_from_login(client, make_user):
    make_user("manager", email="manager@example.com", password="password123")

    response = login(client, "manager@example.com", "password123")

    assert response.status_code == 302
    assert "/login" not in response.headers["Location"]


def test_login_invalid_credentials_flashes_message(client, make_user):
    make_user("manager", email="manager@example.com", password="password123")

    response = client.post(
        "/login",
        data={"email": "manager@example.com", "password": "wrong-password"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in response.data


def test_unauthenticated_user_gets_401_on_dashboard(client):
    response = client.get("/dashboard")
    assert response.status_code == 401


def test_ssr_blocked_from_manager_dashboard(client, make_user):
    make_user("ssr", email="ssr@example.com", password="password123")
    login(client, "ssr@example.com", "password123")

    response = client.get("/dashboard")
    assert response.status_code == 403


def test_admin_can_access_manager_dashboard(client, make_user):
    make_user("admin", email="admin@example.com", password="password123")
    login(client, "admin@example.com", "password123")

    response = client.get("/dashboard")
    assert response.status_code == 200
