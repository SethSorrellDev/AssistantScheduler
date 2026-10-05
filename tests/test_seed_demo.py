"""Tests for the demo data seeder, including the demo manager and audit trail."""
import pytest

import seed_demo
from app.models import AuditLog, Notification, Route, Shift, Stop, User


@pytest.fixture
def seeded(app, roles):
    seed_demo.seed()
    return app


def test_seed_creates_roster_manager_and_audit_trail(seeded):
    assert User.query.filter(User.email.like("%@demo.invalid")).count() == 8
    manager = User.query.filter_by(email="avery.quinn@demo.invalid").one()
    assert manager.role.name == "manager"
    assert AuditLog.query.filter_by(actor_id=manager.id).count() == len(seed_demo.AUDIT_TRAIL)


def test_demo_people_cannot_be_signed_into(seeded):
    for u in User.query.filter(User.email.like("%@demo.invalid")):
        assert u.identity_sub.startswith("demo-seed-")
        assert not u.password_hash


def test_audit_trail_looks_like_real_activity(seeded):
    logs = AuditLog.query.order_by(AuditLog.created_at).all()
    assert {l.action for l in logs} == {"shift_created", "shift_updated", "shift_deleted"}
    assert all(l.entity == "shift" and "@demo.invalid" in l.detail for l in logs)
    assert logs[0].created_at < logs[-1].created_at


def test_seed_is_idempotent(seeded):
    seed_demo.seed()
    assert User.query.count() == 8
    assert AuditLog.query.count() == len(seed_demo.AUDIT_TRAIL)
    assert Route.query.count() == 3
    assert Stop.query.count() == 6


def test_seeding_an_existing_roster_only_adds_the_new_pieces(app, roles):
    """Production already holds the original seven people and their shifts."""
    seed_demo.seed()
    manager = User.query.filter_by(email="avery.quinn@demo.invalid").one()
    AuditLog.query.delete()
    from app import db
    db.session.delete(manager)
    db.session.commit()
    shifts_before = Shift.query.count()

    seed_demo.seed()
    assert Shift.query.count() == shifts_before
    assert AuditLog.query.count() == len(seed_demo.AUDIT_TRAIL)


def test_remove_deletes_demo_data_including_audit_rows(seeded):
    seed_demo.remove()
    assert User.query.count() == 0
    assert AuditLog.query.count() == 0
    assert Shift.query.count() == 0
    assert Route.query.count() == 0
    assert Stop.query.count() == 0


def test_remove_leaves_real_data_alone(seeded, make_user):
    real = make_user("manager", email="real@example.com")
    from app import db
    from app.models import AuditLog
    db.session.add(AuditLog(actor_id=real.id, action="shift_created", entity="shift",
                            entity_id=999, detail="real"))
    db.session.commit()
    seed_demo.remove()
    assert User.query.filter_by(email="real@example.com").count() == 1
    assert AuditLog.query.filter_by(detail="real").count() == 1
