"""
Shared pytest fixtures for AssistantScheduler tests.

Each test gets a fresh temp-file SQLite database, built directly
from the SQLAlchemy models (no Alembic needed for tests), and torn
down after the test completes.
"""
import os
import tempfile
import pytest


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

    from app import create_app, db as _db

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    from app import db as _db
    return _db


@pytest.fixture
def roles(app, db):
    """Seed the four standard roles and return them as a dict keyed by name."""
    from app.models import Role
    created = {}
    for name in ["admin", "manager", "ssr", "assistant"]:
        role = Role(name=name)
        db.session.add(role)
        created[name] = role
    db.session.commit()
    return created


@pytest.fixture
def make_user(app, db, roles):
    """Factory fixture: make_user('ssr', email=..., password=...)"""
    from app.models import User

    def _make_user(role_name, name=None, email=None, password="password123"):
        role = roles[role_name]
        email = email or f"{role_name}@example.com"
        name = name or f"Test {role_name.title()}"
        user = User(name=name, email=email, role_id=role.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user


def login(client, email, password="password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
