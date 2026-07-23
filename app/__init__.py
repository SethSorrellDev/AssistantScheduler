import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO  # NEW

# Extensions (module-level so blueprints can import them)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO()  # NEW


def create_app():
    app = Flask(__name__)

    # --- Config ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///schedule.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)
    # async_mode="eventlet" matches the worker we installed.
    # cors_allowed_origins is fine as "*" for local dev; lock it down in Phase 4.
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")  # NEW

    # --- Models must be imported so Migrate sees them ---
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

    # --- Context processor ---
    @app.context_processor
    def inject_unread():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.services import unread_count
            return {"unread_count": unread_count(current_user.id)}
        return {"unread_count": 0}

    # --- Register SocketIO event handlers ---
    from app import events  # noqa: F401  # NEW


    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    return app
