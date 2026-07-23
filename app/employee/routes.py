from datetime import date
from flask import render_template, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.employee import employee
from app.models import Shift, Notification
from app.services import unread_count

# ============================================================
# DASHBOARD
# ============================================================
@employee.route('/my-schedule')
@login_required
def dashboard():
    upcoming_shifts = Shift.query.filter(
        Shift.user_id == current_user.id,
        Shift.date >= date.today()
    ).order_by(Shift.date, Shift.start_time).all()
    return render_template('employee/dashboard.html',
                           shifts=upcoming_shifts)

# ============================================================
# NOTIFICATIONS
# ============================================================
@employee.route('/notifications')
@login_required
def notifications():
    notes = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template(
        'employee/notifications.html',
        notes=notes,
        unread=unread_count(current_user.id),
    )

@employee.route('/notifications/read/<int:note_id>', methods=['POST'])
@login_required
def mark_read(note_id):
    note = db.get_or_404(Notification, note_id)
    if note.user_id != current_user.id:
        abort(403)
    note.is_read = True
    db.session.commit()
    return redirect(url_for('employee.notifications'))

@employee.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('employee.notifications'))

@employee.route('/api/unread-count')
@login_required
def api_unread_count():
    return jsonify({'unread': unread_count(current_user.id)})
