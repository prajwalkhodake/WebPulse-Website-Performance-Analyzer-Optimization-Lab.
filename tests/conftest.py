"""
Pytest Fixtures for WebPulse Test Suite
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture(scope='session')
def app():
    """Create and configure application for testing."""
    _app = create_app('testing')
    return _app


@pytest.fixture(autouse=True)
def init_database(app):
    """Create fresh database tables for each test and drop them afterwards."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for invoking Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app, init_database):
    """Fixture that creates and persists a test user."""
    with app.app_context():
        user = User(username='testengineer', email='engineer@webpulse.com')
        user.set_password('SecurePass123!')
        db.session.add(user)
        db.session.commit()
        # Re-query inside context
        return User.query.filter_by(username='testengineer').first()
