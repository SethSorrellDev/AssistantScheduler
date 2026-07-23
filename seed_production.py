"""
One-time production seed.
Run via Render Shell after first deploy:
    python seed_production.py
"""
import os
from app import create_app, db
from app.models import Role, User

app = create_app()

with app.app_context():
    # --- Roles ---
    role_names = ["admin", "manager", "ssr", "assistant"]
    for name in role_names:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()
    print("Roles seeded.")

    # --- Admin account ---
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@assistantscheduler.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "changeme123!")
    admin_name = os.environ.get("ADMIN_NAME", "Site Admin")

    if not User.query.filter_by(email=admin_email).first():
        role = Role.query.filter_by(name="manager").first()
        user = User(name=admin_name, email=admin_email, role_id=role.id)
        user.set_password(admin_password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin account created: {admin_email}")
    else:
        print(f"Admin account already exists: {admin_email}")

    print("Seed complete.")
