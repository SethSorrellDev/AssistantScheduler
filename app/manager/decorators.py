from functools import wraps 
from flask import redirect, url_for, flash
from flask_login import current_user

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_manager():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('employee.dashboard'))
        return f(*args, **kwargs)
    return decorated_function