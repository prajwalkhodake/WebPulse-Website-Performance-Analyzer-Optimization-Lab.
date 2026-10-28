"""
Authentication & Authorization Test Cases
Verifies registration, validation, login/logout, session tracking, and account management.
"""
from app.models.user import User


def test_user_password_hashing():
    """Verify that user passwords are correctly hashed with Werkzeug."""
    u = User(username='security_test', email='security@test.com')
    u.set_password('MyStrongSecretPass')
    assert u.password_hash != 'MyStrongSecretPass'
    assert u.check_password('MyStrongSecretPass') is True
    assert u.check_password('WrongSecretPass') is False


def test_registration_success(client, app):
    """Test successful user registration flow."""
    response = client.post('/auth/register', data={
        'username': 'newdeveloper',
        'email': 'dev@webpulse.io',
        'password': 'Password987!',
        'confirm_password': 'Password987!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your account has been successfully created' in response.data

    with app.app_context():
        user = User.query.filter_by(username='newdeveloper').first()
        assert user is not None
        assert user.email == 'dev@webpulse.io'
        assert user.check_password('Password987!') is True


def test_registration_duplicate_username(client, test_user):
    """Test that existing usernames cannot be registered again."""
    response = client.post('/auth/register', data={
        'username': 'testengineer',  # Already exists in fixture
        'email': 'different@webpulse.io',
        'password': 'Password987!',
        'confirm_password': 'Password987!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'This username is already taken' in response.data


def test_registration_duplicate_email(client, test_user):
    """Test that existing email addresses cannot be registered again."""
    response = client.post('/auth/register', data={
        'username': 'uniqueuser123',
        'email': 'engineer@webpulse.com',  # Already exists in fixture
        'password': 'Password987!',
        'confirm_password': 'Password987!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'An account with this email address already exists' in response.data


def test_registration_password_mismatch(client):
    """Test that mismatched passwords trigger form validation errors."""
    response = client.post('/auth/register', data={
        'username': 'mismatchuser',
        'email': 'mismatch@webpulse.io',
        'password': 'Password987!',
        'confirm_password': 'DifferentPassword!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Passwords must match' in response.data


def test_registration_short_password(client):
    """Test that passwords shorter than 8 characters are rejected."""
    response = client.post('/auth/register', data={
        'username': 'shortpassuser',
        'email': 'short@webpulse.io',
        'password': 'short',
        'confirm_password': 'short'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Password must be at least 8 characters long' in response.data


def test_login_success_with_username(client, test_user):
    """Test login with username and valid password."""
    response = client.post('/auth/login', data={
        'username_or_email': 'testengineer',
        'password': 'SecurePass123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back, testengineer!' in response.data
    assert b'Total Projects' in response.data


def test_login_success_with_email(client, test_user):
    """Test login with email and valid password."""
    response = client.post('/auth/login', data={
        'username_or_email': 'engineer@webpulse.com',
        'password': 'SecurePass123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back, testengineer!' in response.data


def test_login_invalid_credentials(client, test_user):
    """Test login failure with incorrect password."""
    response = client.post('/auth/login', data={
        'username_or_email': 'testengineer',
        'password': 'IncorrectPassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid username/email or password' in response.data


def test_dashboard_access_control(client):
    """Test that unauthenticated users are redirected from protected views."""
    response = client.get('/dashboard/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_logout(client, test_user):
    """Test user logout."""
    # First log in
    client.post('/auth/login', data={
        'username_or_email': 'testengineer',
        'password': 'SecurePass123!'
    }, follow_redirects=True)

    # Then log out
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out securely' in response.data

    # Verify protected page is no longer accessible
    protected_res = client.get('/dashboard/', follow_redirects=False)
    assert protected_res.status_code == 302


def test_account_update_profile(client, test_user, app):
    """Test updating account username and email."""
    # Log in
    client.post('/auth/login', data={
        'username_or_email': 'testengineer',
        'password': 'SecurePass123!'
    }, follow_redirects=True)

    response = client.post('/auth/account', data={
        'username': 'updatedengineer',
        'email': 'updated@webpulse.com',
        'current_password': '',
        'new_password': '',
        'confirm_new_password': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your account settings have been updated' in response.data

    with app.app_context():
        user = User.query.filter_by(username='updatedengineer').first()
        assert user is not None
        assert user.email == 'updated@webpulse.com'
