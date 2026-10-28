"""
Project & ProjectVersion Models
Represents user workspaces and immutable version snapshots.
"""
from datetime import datetime, timezone
from app.extensions import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    project_type = db.Column(db.String(30), default='static_html')
    entry_point = db.Column(db.String(255), default='index.html')
    is_demo = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='projects')
    versions = db.relationship('ProjectVersion', back_populates='project', cascade='all, delete-orphan', order_by='desc(ProjectVersion.version_number)')

    @property
    def latest_version(self):
        return self.versions[0] if self.versions else None

    @property
    def version_count(self):
        return len(self.versions)

    def __repr__(self):
        return f"<Project id={self.id} name='{self.name}'>"


class ProjectVersion(db.Model):
    __tablename__ = 'project_versions'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    version_label = db.Column(db.String(80), default='v1.0')
    notes = db.Column(db.Text, default='')
    archive_filename = db.Column(db.String(255), default='')
    storage_path = db.Column(db.String(255), nullable=False)
    total_files = db.Column(db.Integer, default=0)
    total_size_bytes = db.Column(db.BigInteger, default=0)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'version_number', name='uq_project_version'),
    )

    # Relationships
    project = db.relationship('Project', back_populates='versions')
    files = db.relationship('ProjectFile', back_populates='version', cascade='all, delete-orphan', order_by='ProjectFile.relative_path')
    analysis = db.relationship('AnalysisRun', back_populates='version', uselist=False, cascade='all, delete-orphan')
    dependency_edges = db.relationship('DependencyEdge', back_populates='version', cascade='all, delete-orphan')
    test_runs = db.relationship('PerformanceTestRun', back_populates='version', cascade='all, delete-orphan', order_by='desc(PerformanceTestRun.created_at)')
    recommendations = db.relationship('Recommendation', back_populates='version', cascade='all, delete-orphan', order_by='desc(Recommendation.priority_score)')

    @property
    def has_analysis(self):
        return self.analysis is not None and self.analysis.status == 'completed'

    @property
    def latest_test_run(self):
        return self.test_runs[0] if self.test_runs else None

    @property
    def total_size_kb(self):
        return round(self.total_size_bytes / 1024, 1)

    def __repr__(self):
        return f"<ProjectVersion id={self.id} project_id={self.project_id} v={self.version_number}>"
