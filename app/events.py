"""SocketIO event handlers.

Imported once in create_app so the @socketio.on decorators register.
"""
from flask import request
from flask_login import current_user
from flask_socketio import join_room, leave_room

from app import socketio


@socketio.on("connect")
def handle_connect():
    """Put each connection into rooms so we can target pushes precisely."""
    if not current_user.is_authenticated:
        return False

    join_room(f"user_{current_user.id}")

    if current_user.is_manager:
        join_room("managers")

    return True


@socketio.on("disconnect")
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        if current_user.is_manager:
            leave_room("managers")
