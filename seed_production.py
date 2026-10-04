"""
Production seed. Runs on every deploy from build.sh; safe to repeat.
Creates the roles and, if missing, one manager row for ADMIN_EMAIL.
There is no password: the person signs in through identity-service, and the
first successful sign-in with that email links the row to their identity.
"""
import os
from app import create_app, db
from app.models import Role, User

app = create_app()

with app.app_context():
    for name in ["admin", "manager", "ssr", "assistant"]:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()
    print("Roles seeded.")

    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    admin_name = os.environ.get("ADMIN_NAME", "Site Admin")

    if not admin_email:
        print("ADMIN_EMAIL not set; skipping admin row.")
    elif User.query.filter_by(email=admin_email).first():
        print(f"Admin account already exists: {admin_email}")
    else:
        role = Role.query.filter_by(name="manager").first()
        db.session.add(User(name=admin_name, email=admin_email, role_id=role.id))
        db.session.commit()
        print(f"Admin account created: {admin_email}. Sign in through identity-service to link it.")

    print("Seed complete.")
