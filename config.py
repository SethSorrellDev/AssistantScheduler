import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # New in Phase 2
    BCRYPT_ROUNDS = 12          # bcrypt cost factor; higher = slower = safer
    DEFAULT_ROLE = "employee"   # role given to brand-new self-registered users

    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True