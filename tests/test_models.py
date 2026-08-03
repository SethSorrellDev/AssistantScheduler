"""
Model-level tests: password hashing, role convenience properties,
and the RouteStop unique-constraint behavior — same stop is allowed
on the same route across different days, but blocked from being
assigned twice to the same route on the same day.
"""
import pytest
from sqlalchemy.exc import IntegrityError


def test_password_hashing_and_verification(app, db, make_user):
    user = make_user("ssr", password="correct-horse-battery")
    assert user.password_hash != "correct-horse-battery"
    assert user.check_password("correct-horse-battery") is True


def test_wrong_password_fails(app, db, make_user):
    user = make_user("ssr", password="correct-horse-battery")
    assert user.check_password("wrong-password") is False


def test_is_manager_includes_admin(app, db, make_user):
    manager = make_user("manager")
    admin = make_user("admin")
    assert manager.is_manager is True
    assert admin.is_manager is True


def test_is_manager_false_for_ssr_and_assistant(app, db, make_user):
    ssr = make_user("ssr")
    assistant = make_user("assistant")
    assert ssr.is_manager is False
    assert assistant.is_manager is False


def test_is_employee_true_for_ssr_and_assistant_only(app, db, make_user):
    ssr = make_user("ssr")
    assistant = make_user("assistant")
    manager = make_user("manager")
    assert ssr.is_employee is True
    assert assistant.is_employee is True
    assert manager.is_employee is False


def test_role_display_labels(app, db, make_user):
    assert make_user("ssr").role_display == "SSR"
    assert make_user("assistant").role_display == "Assistant"
    assert make_user("manager").role_display == "Manager"
    assert make_user("admin").role_display == "Admin"


def test_route_stop_blocks_duplicate_on_same_day(app, db, roles):
    from app.models import Route, Stop, RouteStop

    route = Route(name="Route 15")
    stop = Stop(name="Nucor Steel")
    db.session.add_all([route, stop])
    db.session.commit()

    db.session.add(RouteStop(route_id=route.id, stop_id=stop.id, day=1, sequence=0))
    db.session.commit()

    db.session.add(RouteStop(route_id=route.id, stop_id=stop.id, day=1, sequence=1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_route_stop_allowed_on_different_days(app, db, roles):
    from app.models import Route, Stop, RouteStop

    route = Route(name="Route 15")
    stop = Stop(name="Nucor Steel")
    db.session.add_all([route, stop])
    db.session.commit()

    db.session.add(RouteStop(route_id=route.id, stop_id=stop.id, day=1, sequence=0))
    db.session.add(RouteStop(route_id=route.id, stop_id=stop.id, day=3, sequence=0))
    db.session.commit()

    assert RouteStop.query.filter_by(route_id=route.id, stop_id=stop.id).count() == 2
