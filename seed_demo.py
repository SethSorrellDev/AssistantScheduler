"""Demo roster, routes, stops and upcoming shifts for the live demo.

    python seed_demo.py            # add demo data (safe to re-run)
    python seed_demo.py --remove   # delete everything this script created

Demo people use @demo.invalid emails and a placeholder identity_sub, so no
real sign-in can ever be linked to them. They exist only as roster entries.
"""
import sys
from datetime import date, time, timedelta

from app import create_app, db
from app.models import Location, Role, Route, RouteStop, Shift, Stop, User

DOMAIN = "demo.invalid"

PEOPLE = [  # (name, email local part, role)
    ("Morgan Ellis", "morgan.ellis", "ssr"),
    ("Riley Chen", "riley.chen", "ssr"),
    ("Casey Alvarez", "casey.alvarez", "ssr"),
    ("Jamie Okafor", "jamie.okafor", "assistant"),
    ("Taylor Brooks", "taylor.brooks", "assistant"),
    ("Devon Patel", "devon.patel", "assistant"),
    ("Quinn Larson", "quinn.larson", "assistant"),
]

ROUTES = [  # (name, description, PPE)
    ("North Loop", "Industrial district, heavy uniform volume.", "Safety glasses, Gloves, Hi-vis vest"),
    ("East Corridor", "Mixed food-service and light manufacturing.", "Hairnets, Beard nets, Smocks"),
    ("Downtown Run", "Offices and small retail, tight parking.", "None"),
]

STOPS = [  # (name, address, notes)
    ("Ridgeline Fabrication", "100 Industrial Pkwy", "Check in at the east gate. Dock closes at 3 PM."),
    ("Harbor Point Foods", "220 Mill St", "Hairnet required past the lobby."),
    ("Summit Auto Parts", "45 Commerce Dr", "Call the shop foreman on arrival."),
    ("Maple Street Diner", "12 Maple St", "Rear entrance only. Deliveries before 10 AM."),
    ("Cobalt Machining", "880 Foundry Rd", "Hearing protection required on the floor."),
    ("City Hall Annex", "3 Courthouse Sq", "Metered parking out front. Use the loading zone."),
]

# (route index, day) -> stop indexes in order
ROUTE_STOPS = {
    0: {1: [0, 4], 3: [0, 4]},
    1: {2: [1, 3], 4: [1, 3]},
    2: {1: [5, 2], 3: [5, 2]},
}

SHIFT_START, SHIFT_END = time(6, 0), time(14, 30)
DAYS_AHEAD = 14


def _role(name):
    role = Role.query.filter_by(name=name).first()
    if role is None:
        raise SystemExit(f"Role '{name}' is missing. Run the normal seed first.")
    return role


def seed():
    created = {"users": 0, "routes": 0, "stops": 0, "shifts": 0}

    location = Location.query.filter_by(name="Frankfort Plant").first()
    if location is None:
        location = Location(name="Frankfort Plant", address="Frankfort, IN")
        db.session.add(location)
        db.session.flush()

    people = {}
    for n, (name, local, role_name) in enumerate(PEOPLE, start=1):
        email = f"{local}@{DOMAIN}"
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(name=name, email=email, role_id=_role(role_name).id,
                        location_id=location.id,
                        identity_sub=f"demo-seed-{n}")
            db.session.add(user)
            created["users"] += 1
        people[role_name] = people.get(role_name, []) + [user]

    routes = []
    for name, description, ppe in ROUTES:
        route = Route.query.filter_by(name=name).first()
        if route is None:
            route = Route(name=name, description=description,
                          ppe_required=ppe, location_id=location.id)
            db.session.add(route)
            created["routes"] += 1
        routes.append(route)

    stops = []
    for name, address, notes in STOPS:
        stop = Stop.query.filter_by(name=name).first()
        if stop is None:
            stop = Stop(name=name, address=address, notes=notes)
            db.session.add(stop)
            created["stops"] += 1
        stops.append(stop)
    db.session.flush()

    for r_idx, days in ROUTE_STOPS.items():
        for day, stop_idxs in days.items():
            for seq, s_idx in enumerate(stop_idxs):
                exists = RouteStop.query.filter_by(
                    route_id=routes[r_idx].id, stop_id=stops[s_idx].id, day=day
                ).first()
                if not exists:
                    db.session.add(RouteStop(route_id=routes[r_idx].id,
                                             stop_id=stops[s_idx].id,
                                             day=day, sequence=seq))

    ssrs, assistants = people["ssr"], people["assistant"]
    today = date.today()
    workday = 0
    for offset in range(1, DAYS_AHEAD + 1):
        day = today + timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        for i, route in enumerate(routes):
            for user in (ssrs[i % len(ssrs)],
                         assistants[(i + workday) % len(assistants)]):
                exists = Shift.query.filter_by(user_id=user.id, date=day).first()
                if not exists:
                    db.session.add(Shift(user_id=user.id, route_id=route.id,
                                         date=day, start_time=SHIFT_START,
                                         end_time=SHIFT_END, status="scheduled"))
                    created["shifts"] += 1
        workday += 1

    db.session.commit()
    print("Demo data added:", created)


def remove():
    users = User.query.filter(User.email.like(f"%@{DOMAIN}")).all()
    ids = [u.id for u in users]
    shifts = Shift.query.filter(Shift.user_id.in_(ids)).delete(synchronize_session=False) if ids else 0
    for u in users:
        db.session.delete(u)
    for name, _, _ in ROUTES:
        route = Route.query.filter_by(name=name).first()
        if route and not Shift.query.filter_by(route_id=route.id).first():
            db.session.delete(route)
    for name, _, _ in STOPS:
        stop = Stop.query.filter_by(name=name).first()
        if stop:
            db.session.delete(stop)
    db.session.commit()
    print(f"Removed {len(users)} demo users and {shifts} shifts, plus demo routes and stops.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        remove() if "--remove" in sys.argv else seed()
