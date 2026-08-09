from datetime import datetime, timezone
from flask_login import UserMixin
from app import db
import bcrypt


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Location {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)

    # Notification preferences — NEW
    phone_number = db.Column(db.String(20), nullable=True)
    notify_email = db.Column(db.Boolean, nullable=False, default=True)
    notify_sms = db.Column(db.Boolean, nullable=False, default=False)

    shifts = db.relationship("Shift", backref="employee", lazy=True,
                             foreign_keys="Shift.user_id")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    # --- Role convenience properties ---
    @property
    def is_manager(self):
        return self.role and self.role.name in ("manager", "admin")

    @property
    def is_ssr(self):
        return self.role and self.role.name == "ssr"

    @property
    def is_assistant(self):
        return self.role and self.role.name == "assistant"

    @property
    def is_employee(self):
        """True for both SSRs and Assistants — anyone who is not a manager."""
        return self.role and self.role.name in ("ssr", "assistant")

    @property
    def is_admin(self):
        return self.role and self.role.name == "admin"

    def has_role(self, role_name):
        return self.role and self.role.name == role_name

    @property
    def role_display(self):
        """Human-readable role label for templates."""
        labels = {"manager": "Manager", "ssr": "SSR", "assistant": "Assistant",
                  "admin": "Admin"}
        return labels.get(self.role.name, self.role.name) if self.role else "—"

    def __repr__(self):
        return f"<User {self.email}>"


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ppe_required = db.Column(db.Text, nullable=True)   # NEW — "None" or list of items
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    shifts = db.relationship("Shift", backref="route", lazy=True)

    def __repr__(self):
        return f"<Route {self.name}>"


class Shift(db.Model):
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Shift {self.id} on {self.date}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User",
                           backref=db.backref("notifications",
                                              cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%b %d, %I:%M %p"),
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                         nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    actor = db.relationship("User", foreign_keys=[actor_id],
                            backref=db.backref("audit_actions",
                                               cascade="all, delete-orphan"))


class Stop(db.Model):
    """A customer or location stop — exists independently of any route."""
    __tablename__ = "stops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Stop {self.name}>"


class RouteStop(db.Model):
    """Assignment of a Stop to a Route on a specific day and sequence position."""
    __tablename__ = "route_stops"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(
        db.Integer, db.ForeignKey("routes.id"), nullable=False, index=True
    )
    stop_id = db.Column(
        db.Integer, db.ForeignKey("stops.id"), nullable=False, index=True
    )
    day = db.Column(db.Integer, nullable=False)          # 1, 2, 3, or 4
    sequence = db.Column(db.Integer, nullable=False, default=0)  # order within day
    notes = db.Column(db.Text, nullable=True)            # route-specific stop notes

    route = db.relationship(
        "Route",
        backref=db.backref("route_stops", cascade="all, delete-orphan",
                           order_by="RouteStop.day, RouteStop.sequence")
    )
    stop = db.relationship(
        "Stop",
        backref=db.backref("route_stops", cascade="all, delete-orphan")
    )

    # Same stop on same route on same day is a duplicate — block it.
    # Same stop on same route on DIFFERENT days is allowed (e.g. Day 1 and Day 3).
    __table_args__ = (
        db.UniqueConstraint("route_id", "stop_id", "day", name="uq_route_stop_day"),
    )

    def __repr__(self):
        return f"<RouteStop route={self.route_id} stop={self.stop_id} day={self.day}>"
