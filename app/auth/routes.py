"""
Authentication Routes
Handles user registration, login, logout, and profile management with strict CSRF and redirection validation.
"""
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db
from app.models.user import User
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm, AccountUpdateForm


def is_safe_redirect_url(target: str) -> bool:
    """Ensure the target redirection URL is local and cannot redirect offsite."""
    if not target:
        return False
    netloc = urlsplit(target).netloc
    return netloc == ''


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been successfully created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Create Account', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate existing users."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username_or_email.data.strip()
        # Query by username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if not is_safe_redirect_url(next_page):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')

    return render_template('auth/login.html', title='Sign In', form=form)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Log out current user."""
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """View and update account details."""
    form = AccountUpdateForm(original_user=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()

        # If password update is requested
        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash('Current password is required and must be correct to change your password.', 'danger')
                return render_template('auth/account.html', title='Account Settings', form=form)
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash('Your account settings have been updated.', 'success')
        return redirect(url_for('auth.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('auth/account.html', title='Account Settings', form=form)
