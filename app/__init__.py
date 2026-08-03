import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)

    # --- Secret key — MUST come from env in production ---
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production. "
                "Refusing to start with an insecure default."
            )
        secret_key = "dev-key-change-me"  # local development only
    app.config["SECRET_KEY"] = secret_key

    # --- Database URL ---
    # Render provides PostgreSQL as postgres:// but SQLAlchemy 2.x needs postgresql://
    database_url = os.environ.get("DATABASE_URL", "sqlite:///schedule.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
    if allowed_origins != "*":
        allowed_origins = [o.strip() for o in allowed_origins.split(",")]
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins=allowed_origins)

    # --- Models ---
    from app import models  # noqa: F401

    # --- User loader ---
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.User, int(user_id))

    # --- Blueprints ---
    from app.auth import auth as auth_bp
    from app.manager import manager as manager_bp
    from app.employee import employee as employee_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)

    # --- SocketIO event handlers ---
    from app import events  # noqa: F401

    # --- Context processor ---
    @app.context_processor
    def inject_unread():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.services import unread_count
            return {"unread_count": unread_count(current_user.id)}
        return {"unread_count": 0}

    # --- Root redirect ---
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    return app
