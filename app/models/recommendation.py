"""
Recommendation Model
Stores prioritized, actionable remediation advice derived from static analysis and performance tests.
"""
from datetime import datetime, timezone
from app.extensions import db


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('project_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    finding_id = db.Column(db.Integer, db.ForeignKey('findings.id', ondelete='SET NULL'), nullable=True, index=True)
    rule_id = db.Column(db.String(60), default='', index=True)
    priority = db.Column(db.String(20), default='medium', index=True)  # high, medium, low
    priority_score = db.Column(db.Float, default=0.0, index=True)
    title = db.Column(db.String(255), nullable=False)
    action_plan = db.Column(db.Text, nullable=False)
    potential_benefit = db.Column(db.String(255), default='')
    affected_resource = db.Column(db.String(500), default='')
    is_verified_fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    version = db.relationship('ProjectVersion', back_populates='recommendations')
    finding = db.relationship('Finding', back_populates='recommendation')

    def __repr__(self):
        return f"<Recommendation priority='{self.priority}' score={self.priority_score:.1f} title='{self.title[:30]}'>"
