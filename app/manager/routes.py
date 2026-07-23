from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.manager import manager
from app.decorators import role_required
from app.manager.forms import EmployeeForm, RouteForm, ShiftForm, StopForm, RouteStopForm
from app.models import User, Role, Route, Shift, AuditLog, Stop, RouteStop
from app.services import notify_user, record_audit
# ============================================================
# HELPERS
# ============================================================
def _employee_query():
    """Users whose role is 'employee', via the role relationship."""
    return User.query.join(Role).filter(Role.name.in_(['ssr', 'assistant']))

def _populate_role_choices(form):
    """Fill the role dropdown from the roles table."""
    assignable = Role.query.filter(Role.name.in_(['ssr', 'assistant', 'manager'])).all()
    form.role.choices = [(r.id, r.name.title()) for r in assignable]

def _populate_shift_form_choices(form):
    """Fill employee and route dropdowns."""
    form.user_id.choices = [
        (u.id, u.name) for u in
        _employee_query().order_by(User.name).all()
    ]
    form.route_id.choices = [
        (r.id, r.name) for r in Route.query.order_by(Route.name).all()
    ]

# ============================================================
# DASHBOARD
# ============================================================
@manager.route('/dashboard')
@role_required('manager')
def dashboard():
    from app.models import Role
    employee_count = _employee_query().count()
    route_count = Route.query.count()
    upcoming_shifts = Shift.query.filter(
        Shift.date >= date.today()
    ).count()
    ssrs = User.query.join(Role).filter(Role.name == 'ssr').order_by(User.name).all()
    assistants = User.query.join(Role).filter(Role.name == 'assistant').order_by(User.name).all()
    return render_template('manager/dashboard.html',
                           employee_count=employee_count,
                           route_count=route_count,
                           upcoming_shifts=upcoming_shifts,
                           ssrs=ssrs,
                           assistants=assistants)

# ============================================================
# EMPLOYEES
# ============================================================
@manager.route('/employees')
@role_required('manager')
def employees():
    all_users = User.query.order_by(User.name).all()
    return render_template('manager/employees.html', users=all_users)

@manager.route('/employees/add', methods=['GET', 'POST'])
@role_required('manager')
def add_employee():
    form = EmployeeForm()
    _populate_role_choices(form)
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash('An account with that email already exists.', 'danger')
            return render_template('manager/employee_form.html',
                                   form=form, action='Add')
        if not form.password.data:
            flash('Password is required for new employees.', 'danger')
            return render_template('manager/employee_form.html',
                                   form=form, action='Add')
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            role_id=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'{user.name} has been added.', 'success')
        return redirect(url_for('manager.employees'))
    return render_template('manager/employee_form.html',
                           form=form, action='Add')

@manager.route('/employees/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('manager')
def edit_employee(user_id):
    user = db.get_or_404(User, user_id)
    form = EmployeeForm(obj=user)
    _populate_role_choices(form)
    if form.validate_on_submit():
        if form.email.data.lower() != user.email:
            existing = User.query.filter_by(email=form.email.data.lower()).first()
            if existing:
                flash('That email is already in use.', 'danger')
                return render_template('manager/employee_form.html',
                                       form=form, action='Edit')
        user.name = form.name.data
        user.email = form.email.data.lower()
        user.role_id = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(f'{user.name} has been updated.', 'success')
        return redirect(url_for('manager.employees'))
    if request.method == 'GET' and user.role_id:
        form.role.data = user.role_id
    return render_template('manager/employee_form.html',
                           form=form, action='Edit')

@manager.route('/employees/delete/<int:user_id>', methods=['POST'])
@role_required('manager')
def delete_employee(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manager.employees'))
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f'{name} has been deleted.', 'info')
    return redirect(url_for('manager.employees'))

# ============================================================
# ROUTES (service routes, not URL routes)
# ============================================================
@manager.route('/routes')
@role_required('manager')
def routes():
    all_routes = Route.query.order_by(Route.name).all()
    return render_template('manager/routes.html', routes=all_routes)

@manager.route('/routes/add', methods=['GET', 'POST'])
@role_required('manager')
def add_route():
    form = RouteForm()
    if form.validate_on_submit():
        route = Route(
            name=form.name.data,
            description=form.description.data,
            ppe_required=form.ppe_required.data or None,
        )
        db.session.add(route)
        db.session.commit()
        flash(f'Route "{route.name}" added.', 'success')
        return redirect(url_for('manager.routes'))
    return render_template('manager/route_form.html', form=form, action='Add')

@manager.route('/routes/edit/<int:route_id>', methods=['GET', 'POST'])
@role_required('manager')
def edit_route(route_id):
    route = db.get_or_404(Route, route_id)
    form = RouteForm(obj=route)
    if form.validate_on_submit():
        route.name = form.name.data
        route.description = form.description.data
        route.ppe_required = form.ppe_required.data or None
        db.session.commit()
        flash(f'Route "{route.name}" updated.', 'success')
        return redirect(url_for('manager.routes'))
    return render_template('manager/route_form.html', form=form, action='Edit')

@manager.route('/routes/delete/<int:route_id>', methods=['POST'])
@role_required('manager')
def delete_route(route_id):
    route = db.get_or_404(Route, route_id)
    name = route.name
    db.session.delete(route)
    db.session.commit()
    flash(f'Route "{name}" deleted.', 'info')
    return redirect(url_for('manager.routes'))

# ============================================================
# SHIFTS
# ============================================================
@manager.route('/shifts')
@role_required('manager')
def shifts():
    from collections import defaultdict
    from datetime import timedelta
    all_shifts = Shift.query.filter(
        Shift.date >= date.today()
    ).order_by(Shift.date, Shift.start_time).all()
    week_dict = defaultdict(list)
    for shift in all_shifts:
        week_start = shift.date - timedelta(days=shift.date.weekday())
        week_dict[week_start].append(shift)
    weeks = []
    for week_start in sorted(week_dict.keys()):
        week_end = week_start + timedelta(days=6)
        shifts_this_week = week_dict[week_start]
        day_dict = defaultdict(list)
        for s in shifts_this_week:
            day_dict[s.date].append(s)
        weeks.append({
            'start': week_start,
            'end': week_end,
            'count': len(shifts_this_week),
            'days': [(d, day_dict[d]) for d in sorted(day_dict.keys())]
        })
    return render_template('manager/shifts.html', weeks=weeks)

@manager.route('/shifts/add', methods=['GET', 'POST'])
@role_required('manager')
def add_shift():
    form = ShiftForm()
    _populate_shift_form_choices(form)
    if form.validate_on_submit():
        if form.end_time.data <= form.start_time.data:
            flash('End time must be after start time.', 'danger')
            return render_template('manager/shift_form.html',
                                   form=form, action='Add')
        shift = Shift(
            user_id=form.user_id.data,
            route_id=form.route_id.data,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            notes=form.notes.data,
            status='scheduled',
        )
        db.session.add(shift)
        db.session.commit()
        if shift.user_id:
            notify_user(
                shift.user_id,
                message=f"You have a new shift on {shift.date.strftime('%A, %b %d')}.",
                link="/employee/shifts",
            )
        record_audit(
            actor_id=current_user.id,
            action="shift_created",
            entity="shift",
            entity_id=shift.id,
            detail=f"Shift #{shift.id} created by {current_user.email}",
        )
        flash('Shift created.', 'success')
        return redirect(url_for('manager.shifts'))
    return render_template('manager/shift_form.html', form=form, action='Add')

@manager.route('/shifts/edit/<int:shift_id>', methods=['GET', 'POST'])
@role_required('manager')
def edit_shift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    form = ShiftForm(obj=shift)
    _populate_shift_form_choices(form)
    if form.validate_on_submit():
        if form.end_time.data <= form.start_time.data:
            flash('End time must be after start time.', 'danger')
            return render_template('manager/shift_form.html',
                                   form=form, action='Edit')
        shift.user_id = form.user_id.data
        shift.route_id = form.route_id.data
        shift.date = form.date.data
        shift.start_time = form.start_time.data
        shift.end_time = form.end_time.data
        shift.notes = form.notes.data
        shift.status = 'modified'
        db.session.commit()
        if shift.user_id:
            notify_user(
                shift.user_id,
                message=f"Your shift on {shift.date.strftime('%A, %b %d')} was updated.",
                link="/employee/shifts",
            )
        record_audit(
            actor_id=current_user.id,
            action="shift_updated",
            entity="shift",
            entity_id=shift.id,
            detail=f"Shift #{shift.id} updated by {current_user.email}",
        )
        flash('Shift updated.', 'success')
        return redirect(url_for('manager.shifts'))
    return render_template('manager/shift_form.html', form=form, action='Edit')

@manager.route('/shifts/delete/<int:shift_id>', methods=['POST'])
@role_required('manager')
def delete_shift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    # Capture these before the delete — they're gone after commit.
    affected_user_id = shift.user_id
    shift_date = shift.date
    captured_shift_id = shift.id
    db.session.delete(shift)
    db.session.commit()
    if affected_user_id:
        notify_user(
            affected_user_id,
            message=f"Your shift on {shift_date.strftime('%A, %b %d')} has been removed.",
            link="/employee/shifts",
        )
    record_audit(
        actor_id=current_user.id,
        action="shift_deleted",
        entity="shift",
        entity_id=captured_shift_id,
        detail=f"Shift #{captured_shift_id} deleted by {current_user.email}",
    )
    flash('Shift deleted.', 'info')
    return redirect(url_for('manager.shifts'))

# ============================================================
# AUDIT LOG
# ============================================================
@manager.route('/audit-log')
@role_required('manager')
def audit_log():
    logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template('manager/audit_log.html', logs=logs)


# ============================================================
# STOPS — global pool
# ============================================================
@manager.route('/stops')
@role_required('manager')
def stops():
    routes = Route.query.order_by(Route.name).all()
    unassigned = Stop.query.filter(
        ~Stop.id.in_(db.session.query(RouteStop.stop_id))
    ).order_by(Stop.name).all()
    return render_template('manager/stops.html', routes=routes, unassigned=unassigned)


@manager.route('/stops/add', methods=['GET', 'POST'])
@role_required('manager')
def add_stop():
    form = StopForm()
    if form.validate_on_submit():
        stop = Stop(
            name=form.name.data,
            address=form.address.data or None,
            notes=form.notes.data or None,
        )
        db.session.add(stop)
        db.session.commit()
        flash(f'Stop "{stop.name}" added.', 'success')
        return redirect(url_for('manager.stops'))
    return render_template('manager/stop_form.html', form=form, action='Add')


@manager.route('/stops/edit/<int:stop_id>', methods=['GET', 'POST'])
@role_required('manager')
def edit_stop(stop_id):
    stop = db.get_or_404(Stop, stop_id)
    form = StopForm(obj=stop)
    if form.validate_on_submit():
        stop.name = form.name.data
        stop.address = form.address.data or None
        stop.notes = form.notes.data or None
        db.session.commit()
        flash(f'Stop "{stop.name}" updated.', 'success')
        return redirect(url_for('manager.stops'))
    return render_template('manager/stop_form.html', form=form, action='Edit')


@manager.route('/stops/delete/<int:stop_id>', methods=['POST'])
@role_required('manager')
def delete_stop(stop_id):
    stop = db.get_or_404(Stop, stop_id)
    name = stop.name
    db.session.delete(stop)
    db.session.commit()
    flash(f'Stop "{name}" deleted.', 'info')
    return redirect(url_for('manager.stops'))


# ============================================================
# ROUTE STOPS — assign stops to a route with day + sequence
# ============================================================
@manager.route('/routes/<int:route_id>/stops')
@role_required('manager')
def route_stops(route_id):
    route = db.get_or_404(Route, route_id)
    # Group route_stops by day for display
    days = {1: [], 2: [], 3: [], 4: []}
    for rs in route.route_stops:
        if rs.day in days:
            days[rs.day].append(rs)
    return render_template('manager/route_stops.html', route=route, days=days)


@manager.route('/routes/<int:route_id>/stops/add', methods=['GET', 'POST'])
@role_required('manager')
def add_route_stop(route_id):
    route = db.get_or_404(Route, route_id)
    form = RouteStopForm()
    # Populate stop choices — all stops in the pool
    form.stop_id.choices = [
        (s.id, s.name) for s in Stop.query.order_by(Stop.name).all()
    ]
    if form.validate_on_submit():
        # Check for duplicate (same stop, same route, same day)
        existing = RouteStop.query.filter_by(
            route_id=route_id,
            stop_id=form.stop_id.data,
            day=form.day.data
        ).first()
        if existing:
            flash(
                f'That stop is already assigned to Day {form.day.data} on this route.',
                'warning'
            )
            return render_template('manager/route_stop_form.html',
                                   form=form, route=route)
        rs = RouteStop(
            route_id=route_id,
            stop_id=form.stop_id.data,
            day=form.day.data,
            sequence=form.sequence.data or 0,
            notes=form.notes.data or None,
        )
        db.session.add(rs)
        db.session.commit()
        flash('Stop added to route.', 'success')
        return redirect(url_for('manager.route_stops', route_id=route_id))
    return render_template('manager/route_stop_form.html', form=form, route=route)


@manager.route('/routes/<int:route_id>/stops/remove/<int:rs_id>', methods=['POST'])
@role_required('manager')
def remove_route_stop(route_id, rs_id):
    rs = db.get_or_404(RouteStop, rs_id)
    db.session.delete(rs)
    db.session.commit()
    flash('Stop removed from route.', 'info')
    return redirect(url_for('manager.route_stops', route_id=route_id))
