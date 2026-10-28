"""
User Database Model
Represents registered users with secure password hashing and authentication hooks.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to projects (cascades on user deletion)
    projects = db.relationship('Project', back_populates='user', cascade='all, delete-orphan', order_by='desc(Project.updated_at)')

    def set_password(self, password: str) -> None:
        """Hash the user password securely with Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored cryptographic hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"


@login_manager.user_loader
def load_user(user_id: str):
    """Flask-Login user loader callback."""
    return db.session.get(User, int(user_id))
