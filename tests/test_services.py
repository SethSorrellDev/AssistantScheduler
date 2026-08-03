"""
Service-layer tests for notify_user, record_audit, and unread_count.
socketio.emit is mocked so these tests run without a live socket
server and stay focused on the database side effects.
"""
from unittest.mock import patch


def test_notify_user_creates_notification_row(app, db, make_user):
    from app.services import notify_user
    from app.models import Notification

    user = make_user("ssr")

    with patch("app.services.socketio.emit") as mock_emit:
        note = notify_user(user.id, "Your shift on Monday was updated.")

    assert note.id is not None
    assert note.user_id == user.id
    assert note.message == "Your shift on Monday was updated."
    assert Notification.query.count() == 1
    mock_emit.assert_called_once()


def test_notify_user_emits_to_correct_room(app, db, make_user):
    from app.services import notify_user

    user = make_user("ssr")

    with patch("app.services.socketio.emit") as mock_emit:
        notify_user(user.id, "Test message")

    _, kwargs = mock_emit.call_args
    assert kwargs["to"] == f"user_{user.id}"


def test_notify_user_payload_matches_notification(app, db, make_user):
    from app.services import notify_user

    user = make_user("assistant")

    with patch("app.services.socketio.emit") as mock_emit:
        note = notify_user(user.id, "Shift cancelled")

    args, _ = mock_emit.call_args
    event_name, payload = args
    assert event_name == "notification"
    assert payload["message"] == "Shift cancelled"
    assert payload["id"] == note.id


def test_record_audit_creates_audit_log_row(app, db, make_user):
    from app.services import record_audit
    from app.models import AuditLog

    manager = make_user("manager")

    with patch("app.services.socketio.emit"):
        log = record_audit(
            actor_id=manager.id,
            action="shift_created",
            entity="shift",
            entity_id=42,
            detail="Shift #42 created by test",
        )

    assert log.id is not None
    assert log.actor_id == manager.id
    assert AuditLog.query.count() == 1


def test_record_audit_emits_to_managers_room(app, db, make_user):
    from app.services import record_audit

    manager = make_user("manager")

    with patch("app.services.socketio.emit") as mock_emit:
        record_audit(actor_id=manager.id, action="shift_deleted", entity="shift")

    _, kwargs = mock_emit.call_args
    assert kwargs["to"] == "managers"


def test_unread_count_counts_only_unread(app, db, make_user):
    from app.services import notify_user, unread_count
    from app.models import Notification

    user = make_user("ssr")

    with patch("app.services.socketio.emit"):
        notify_user(user.id, "First")
        notify_user(user.id, "Second")
        notify_user(user.id, "Third")

    assert unread_count(user.id) == 3

    note = Notification.query.first()
    note.is_read = True
    db.session.commit()

    assert unread_count(user.id) == 2
