from app import create_app, db
from app.models import Role, User, Route

app = create_app()

with app.app_context():
    # Roles are seeded by the migration itself.
    # This script only creates local demo users (no passwords exist) and sample data.
    # To sign in locally, run identity-service, use "Create an account" with one of
    # these emails, then sign in. The first login links the identity to the row.
    if User.query.first() is None:
        role = lambda name: Role.query.filter_by(name=name).first()

        db.session.add_all([
            User(name="Site Admin", email="admin@test.com", role=role('admin')),
            User(name="Pat Manager", email="manager@test.com", role=role('manager')),
            User(name="Alex Driver", email="alex@test.com", role=role('ssr')),
            User(name="Jordan Driver", email="jordan@test.com", role=role('ssr')),
            User(name="Sam Driver", email="sam@test.com", role=role('assistant')),
            Route(name="North Loop", description="Industrial district"),
        ])
        db.session.commit()
        print("Seeded users and a route. Emails: admin@test.com, manager@test.com, "
              "alex@test.com, jordan@test.com, sam@test.com")
    else:
        print("Users already present — skipping seed.")
