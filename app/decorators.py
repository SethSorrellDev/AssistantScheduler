from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*role_names):
    """Allow the route only if the user has one of role_names.
    Admins are always allowed (role hierarchy)."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            allowed = current_user.is_admin or any(
                current_user.has_role(r) for r in role_names
            )
            if not allowed:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(view_func):
    """Shorthand for admin-only routes."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
