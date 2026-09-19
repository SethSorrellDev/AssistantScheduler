"""
Tests for shift conflict validation — the _has_shift_conflict() check
wired into add_shift and edit_shift. Verifies overlapping shifts for
the same employee are blocked, non-overlapping shifts are allowed,
conflicts are scoped per-employee (not global), an edit doesn't
falsely conflict with itself, and a cancelled shift doesn't block a
new booking in the same slot.
"""
from datetime import date, time
from unittest.mock import patch

from tests.conftest import login


def _shift_form(user_id, route_id, shift_date, start, end, notes=""):
    return {
        "user_id": str(user_id),
        "route_id": str(route_id),
        "date": shift_date.strftime("%Y-%m-%d"),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "notes": notes,
    }


def test_overlapping_shift_same_employee_is_blocked(client, db, make_user):
    from app.models import Route, Shift

    make_user("manager", email="manager@example.com", password="password123")
    ssr = make_user("ssr", email="ssr@example.com", password="password123")
    route = Route(name="Route 15")
    db.session.add(route)
    db.session.commit()

    login(client, "manager@example.com", "password123")
    shift_date = date(2026, 9, 21)

    with patch("app.services.socketio.emit"):
        client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(8, 0), time(16, 0)),
            follow_redirects=True,
        )
        response = client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(14, 0), time(18, 0)),
            follow_redirects=True,
        )

    assert b"already has a shift" in response.data
    assert Shift.query.count() == 1


def test_non_overlapping_shift_same_employee_is_allowed(client, db, make_user):
    from app.models import Route, Shift

    make_user("manager", email="manager@example.com", password="password123")
    ssr = make_user("ssr", email="ssr@example.com", password="password123")
    route = Route(name="Route 15")
    db.session.add(route)
    db.session.commit()

    login(client, "manager@example.com", "password123")
    shift_date = date(2026, 9, 21)

    with patch("app.services.socketio.emit"):
        client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(5, 0), time(12, 0)),
            follow_redirects=True,
        )
        response = client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(13, 0), time(18, 0)),
            follow_redirects=True,
        )

    assert b"already has a shift" not in response.data
    assert Shift.query.count() == 2


def test_overlapping_shift_different_employee_is_allowed(client, db, make_user):
    from app.models import Route, Shift

    make_user("manager", email="manager@example.com", password="password123")
    ssr = make_user("ssr", email="ssr1@example.com", password="password123")
    assistant = make_user("assistant", email="assistant1@example.com", password="password123")
    route = Route(name="Route 15")
    db.session.add(route)
    db.session.commit()

    login(client, "manager@example.com", "password123")
    shift_date = date(2026, 9, 21)

    with patch("app.services.socketio.emit"):
        client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(8, 0), time(16, 0)),
            follow_redirects=True,
        )
        response = client.post(
            "/shifts/add",
            data=_shift_form(assistant.id, route.id, shift_date, time(8, 0), time(16, 0)),
            follow_redirects=True,
        )

    assert b"already has a shift" not in response.data
    assert Shift.query.count() == 2


def test_editing_a_shift_does_not_conflict_with_itself(client, db, make_user):
    from app.models import Route, Shift

    make_user("manager", email="manager@example.com", password="password123")
    ssr = make_user("ssr", email="ssr@example.com", password="password123")
    route = Route(name="Route 15")
    db.session.add(route)
    db.session.commit()

    login(client, "manager@example.com", "password123")
    shift_date = date(2026, 9, 21)

    with patch("app.services.socketio.emit"):
        client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(8, 0), time(16, 0)),
            follow_redirects=True,
        )
        shift = Shift.query.first()

        response = client.post(
            f"/shifts/edit/{shift.id}",
            data=_shift_form(ssr.id, route.id, shift_date, time(8, 0), time(16, 30)),
            follow_redirects=True,
        )

    assert b"already has a shift" not in response.data
    db.session.refresh(shift)
    assert shift.end_time == time(16, 30)


def test_cancelled_shift_does_not_block_new_booking(client, db, make_user):
    from app.models import Route, Shift

    make_user("manager", email="manager@example.com", password="password123")
    ssr = make_user("ssr", email="ssr@example.com", password="password123")
    route = Route(name="Route 15")
    db.session.add(route)
    db.session.commit()

    login(client, "manager@example.com", "password123")
    shift_date = date(2026, 9, 21)

    with patch("app.services.socketio.emit"):
        client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(8, 0), time(16, 0)),
            follow_redirects=True,
        )
        shift = Shift.query.first()
        shift.status = "cancelled"
        db.session.commit()

        response = client.post(
            "/shifts/add",
            data=_shift_form(ssr.id, route.id, shift_date, time(9, 0), time(17, 0)),
            follow_redirects=True,
        )

    assert b"already has a shift" not in response.data
    assert Shift.query.filter(Shift.status != "cancelled").count() == 1
