from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    #Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    #Register blueprints
    from app.auth import auth as auth_bp
    from app.manager import manager as manager_bp
    from app.employee import employee as employee_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(employee_bp, url_prefix='/employee')

    #Root route - redirects based on login status
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('employee.dashboard'))
    
    return app

