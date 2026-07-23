"""Service helpers that combine DB writes with live SocketIO pushes."""
from app import db, socketio
from app.models import Notification, AuditLog


def notify_user(user_id, message, link=None):
    """Persist a notification for one user and push it to their room live."""
    note = Notification(user_id=user_id, message=message, link=link)
    db.session.add(note)
    db.session.commit()

    socketio.emit(
        "notification",
        note.to_dict(),
        to=f"user_{user_id}",
    )
    return note


def record_audit(actor_id, action, entity, entity_id=None, detail=None):
    """Write an audit row and push a live event to the managers room."""
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
    )
    db.session.add(log)
    db.session.commit()

    socketio.emit(
        "audit",
        {
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "detail": detail,
            "actor_id": actor_id,
        },
        to="managers",
    )
    return log


def unread_count(user_id):
    """How many unread notifications a user has (for the bell badge)."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
