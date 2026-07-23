from app import create_app, db
from app.models import Role, User, Route

app = create_app()

with app.app_context():
    # Roles are seeded by the migration itself.
    # This script only creates users and sample data.
    if User.query.first() is None:
        admin_role = Role.query.filter_by(name='admin').first()
        manager_role = Role.query.filter_by(name='manager').first()
        employee_role = Role.query.filter_by(name='employee').first()

        admin = User(name="Site Admin", email="admin@test.com", role=admin_role)
        admin.set_password("password123")

        mgr = User(name="Pat Manager", email="manager@test.com", role=manager_role)
        mgr.set_password("password123")

        emp1 = User(name="Alex Driver", email="alex@test.com", role=employee_role)
        emp1.set_password("password123")

        emp2 = User(name="Jordan Driver", email="jordan@test.com", role=employee_role)
        emp2.set_password("password123")

        emp3 = User(name="Sam Driver", email="sam@test.com", role=employee_role)
        emp3.set_password("password123")

        db.session.add_all([admin, mgr, emp1, emp2, emp3])

        r = Route(name="North Loop", description="Industrial district")
        db.session.add(r)

        db.session.commit()
        print("Seeded users and a route.")
        print("Admin:     admin@test.com / password123")
        print("Manager:   manager@test.com / password123")
        print("Employees: alex@test.com, jordan@test.com, sam@test.com")
    else:
        print("Users already present — skipping seed.")
