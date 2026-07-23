from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.auth import auth
from app.auth.forms import LoginForm, ProfileForm, ChangePasswordForm
from app.models import User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_manager:
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('employee.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_manager:
                next_page = url_for('manager.dashboard')
            else:
                next_page = url_for('employee.dashboard')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing and existing.id != current_user.id:
            flash('That email is already in use.', 'danger')
        else:
            current_user.name = form.name.data
            current_user.email = form.email.data.lower()
            db.session.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated.', 'success')
            return redirect(url_for('auth.profile'))
    return render_template('auth/change_password.html', form=form)


from flask import redirect, url_for as _url_for
from app.auth import auth as _auth

@_auth.route('/')
def index():
    return redirect(_url_for('auth.login'))
