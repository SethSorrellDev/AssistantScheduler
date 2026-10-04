from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.auth import auth
from app.auth import identity
from app.auth.forms import LoginForm, ProfileForm, RegisterForm
from app.models import User


NOT_AUTHORIZED = ("This account isn't authorized to use AssistantScheduler. "
                  "Ask a manager to add your email.")


def _resolve_local_user(ident):
    """Find the local user for a verified identity. Roles live here, never in the token."""
    user = User.query.filter_by(identity_sub=ident.sub).first()
    if user is None and ident.email:
        user = User.query.filter_by(email=ident.email).first()
        if user is not None:
            if user.identity_sub is not None:
                return None  # already linked to a different identity; never re-link
            user.identity_sub = ident.sub
            user.password_hash = None  # the legacy hash is dead once SSO is linked
            db.session.commit()
    if user is None or user.role is None:
        return None
    return user


def _migrate_legacy_account(email, password):
    """One-time: a not-yet-linked user whose old local password matches gets an identity account."""
    user = User.query.filter_by(email=email).first()
    if user is None or user.identity_sub is not None or not user.check_password(password):
        return None
    first, _, last = user.name.strip().partition(' ')
    try:
        identity.register(email, password, first, last or first)
        return identity.authenticate(email, password)
    except identity.IdentityError:
        return None


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_manager:
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('employee.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        try:
            try:
                ident = identity.authenticate(email, form.password.data)
            except identity.InvalidCredentials:
                ident = _migrate_legacy_account(email, form.password.data)
                if ident is None:
                    flash('Invalid email or password.', 'danger')
                    return redirect(url_for('auth.login'))
        except identity.IdentityError as exc:
            flash(str(exc), 'danger')
            return redirect(url_for('auth.login'))

        user = _resolve_local_user(ident)
        if user is None:
            flash(NOT_AUTHORIZED, 'danger')
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


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            identity.register(form.email.data.strip().lower(), form.password.data,
                              form.first_name.data, form.last_name.data)
        except identity.IdentityError as exc:
            flash(str(exc), 'danger')
            return render_template('auth/register.html', form=form)
        flash('Account created. You can sign in once a manager has added your email.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


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
        # Email is the link to the shared sign-in, so it is never edited here.
        current_user.name = form.name.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form)


from flask import redirect, url_for as _url_for
from app.auth import auth as _auth

@_auth.route('/')
def index():
    return redirect(_url_for('auth.login'))
