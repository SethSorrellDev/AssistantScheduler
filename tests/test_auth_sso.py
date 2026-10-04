from app.auth import identity
from tests.conftest import login


def _logged_in(client):
    with client.session_transaction() as session:
        return "_user_id" in session


def test_first_login_links_identity_by_email_and_clears_legacy_hash(app, client, db, make_user):
    user = make_user("ssr")
    login(client, user.email)
    db.session.refresh(user)
    assert _logged_in(client)
    assert user.identity_sub == f"test-sub-{user.email}"
    assert user.password_hash is None


def test_valid_identity_without_a_local_user_is_not_logged_in(app, client, db, roles):
    login(client, "stranger@example.com")
    assert not _logged_in(client)


def test_email_already_linked_to_another_identity_is_refused(app, client, db, make_user):
    user = make_user("ssr")
    user.identity_sub = "someone-else"
    db.session.commit()
    login(client, user.email)
    assert not _logged_in(client)


def test_wrong_password_is_rejected(app, client, db, make_user):
    user = make_user("ssr")
    login(client, user.email, "nope-nope")
    assert not _logged_in(client)


def test_legacy_password_is_migrated_into_identity_on_first_login(app, client, db, make_user, monkeypatch):
    user = make_user("ssr", name="Pat Legacy", password="legacy-pass-1")
    registered = []

    def authenticate(email, password):
        if not registered:
            raise identity.InvalidCredentials("Invalid email or password.")
        return identity.Identity(sub="sub-legacy", email=email)

    monkeypatch.setattr(identity, "authenticate", authenticate)
    monkeypatch.setattr(identity, "register", lambda *args: registered.append(args))

    login(client, user.email, "legacy-pass-1")
    db.session.refresh(user)
    assert registered == [(user.email, "legacy-pass-1", "Pat", "Legacy")]
    assert _logged_in(client)
    assert user.identity_sub == "sub-legacy"
    assert user.password_hash is None


def test_register_page_creates_identity_account_and_redirects_to_login(app, client, monkeypatch):
    calls = []
    monkeypatch.setattr(identity, "register", lambda *args: calls.append(args))
    response = client.post("/register", data={
        "first_name": "Ada", "last_name": "Lovelace", "email": "Ada@Example.com",
        "password": "longenough1", "confirm": "longenough1",
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert calls == [("ada@example.com", "longenough1", "Ada", "Lovelace")]
