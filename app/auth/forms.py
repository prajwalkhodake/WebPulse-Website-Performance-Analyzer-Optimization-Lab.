"""
Authentication and User Forms
Implements WTForms with server-side field and custom uniqueness validators.
"""
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User


class RegistrationForm(FlaskForm):
    """User account registration form."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=30, message='Username must be between 3 and 30 characters.')
        ],
        render_kw={'placeholder': 'Choose a unique username', 'autocomplete': 'username'}
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email address is required.'),
            Email(check_deliverability=False, message='Please provide a valid email address.'),
            Length(max=120)
        ],
        render_kw={'placeholder': 'developer@domain.com', 'autocomplete': 'email'}
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters long.')
        ],
        render_kw={'placeholder': 'Minimum 8 characters', 'autocomplete': 'new-password'}
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ],
        render_kw={'placeholder': 'Re-enter your password', 'autocomplete': 'new-password'}
    )
    submit = SubmitField('Create Account')

    def validate_username(self, username_field):
        """Ensure username is alphanumeric/dashes and not already registered."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', username_field.data):
            raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
        existing_user = User.query.filter_by(username=username_field.data.strip()).first()
        if existing_user:
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_email(self, email_field):
        """Ensure email is not already registered."""
        existing_user = User.query.filter_by(email=email_field.data.strip().lower()).first()
        if existing_user:
            raise ValidationError('An account with this email address already exists.')


class LoginForm(FlaskForm):
    """User login form."""
    username_or_email = StringField(
        'Username or Email',
        validators=[DataRequired(message='Please enter your username or email address.')],
        render_kw={'placeholder': 'username or email@domain.com', 'autocomplete': 'username'}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Please enter your password.')],
        render_kw={'placeholder': 'Enter your password', 'autocomplete': 'current-password'}
    )
    remember_me = BooleanField('Remember me on this device')
    submit = SubmitField('Sign In')


class AccountUpdateForm(FlaskForm):
    """User profile and password settings form."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=30)
        ]
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email address is required.'),
            Email(check_deliverability=False, message='Please provide a valid email address.')
        ]
    )
    current_password = PasswordField(
        'Current Password',
        validators=[Optional()],
        render_kw={'placeholder': 'Required only if changing password'}
    )
    new_password = PasswordField(
        'New Password',
        validators=[
            Optional(),
            Length(min=8, message='New password must be at least 8 characters long.')
        ],
        render_kw={'placeholder': 'Leave blank to keep current password'}
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[
            EqualTo('new_password', message='New passwords must match.')
        ],
        render_kw={'placeholder': 'Re-enter new password'}
    )
    submit = SubmitField('Update Settings')

    def __init__(self, original_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_username(self, username_field):
        cleaned = username_field.data.strip()
        if cleaned != self.original_user.username:
            if not re.match(r'^[a-zA-Z0-9_-]+$', cleaned):
                raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
            if User.query.filter_by(username=cleaned).first():
                raise ValidationError('This username is already taken.')

    def validate_email(self, email_field):
        cleaned = email_field.data.strip().lower()
        if cleaned != self.original_user.email:
            if User.query.filter_by(email=cleaned).first():
                raise ValidationError('This email is already in use by another account.')
