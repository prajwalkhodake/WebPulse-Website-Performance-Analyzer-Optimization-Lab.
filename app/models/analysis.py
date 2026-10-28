"""
Analysis Database Models
Tracks inventoried files, static audit findings, and dependency graph edges.
"""
from datetime import datetime, timezone
from app.extensions import db


class ProjectFile(db.Model):
    __tablename__ = 'project_files'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('project_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    relative_path = db.Column(db.String(500), nullable=False, index=True)
    file_type = db.Column(db.String(30), default='other', index=True)
    file_size_bytes = db.Column(db.BigInteger, default=0)
    sha256_hash = db.Column(db.String(64), default='', index=True)
    line_count = db.Column(db.Integer, nullable=True)
    is_entry_point = db.Column(db.Boolean, default=False)
    reference_count = db.Column(db.Integer, default=0)
    meta_info = db.Column(db.JSON, default=dict)

    __table_args__ = (
        db.UniqueConstraint('version_id', 'relative_path', name='uq_version_relative_path'),
    )

    version = db.relationship('ProjectVersion', back_populates='files')
    findings = db.relationship('Finding', back_populates='affected_file')
    outgoing_edges = db.relationship('DependencyEdge', foreign_keys='DependencyEdge.source_file_id', back_populates='source_file', cascade='all, delete-orphan')
    incoming_edges = db.relationship('DependencyEdge', foreign_keys='DependencyEdge.target_file_id', back_populates='target_file')

    @property
    def file_size_kb(self):
        return round(self.file_size_bytes / 1024, 1)

    def __repr__(self):
        return f"<ProjectFile id={self.id} path='{self.relative_path}'>"


class AnalysisRun(db.Model):
    __tablename__ = 'analysis_runs'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('project_versions.id', ondelete='CASCADE'), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    analyzer_version = db.Column(db.String(20), default='1.0.0')
    summary_counts = db.Column(db.JSON, default=dict)
    error_message = db.Column(db.Text, default='')

    version = db.relationship('ProjectVersion', back_populates='analysis')
    findings = db.relationship('Finding', back_populates='analysis_run', cascade='all, delete-orphan', order_by='Finding.severity')

    def __repr__(self):
        return f"<AnalysisRun id={self.id} version_id={self.version_id} status='{self.status}'>"


class Finding(db.Model):
    __tablename__ = 'findings'

    id = db.Column(db.Integer, primary_key=True)
    analysis_run_id = db.Column(db.Integer, db.ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    affected_file_id = db.Column(db.Integer, db.ForeignKey('project_files.id', ondelete='SET NULL'), nullable=True, index=True)
    finding_code = db.Column(db.String(60), nullable=False, index=True)
    category = db.Column(db.String(30), default='performance', index=True)
    severity = db.Column(db.String(20), default='warning', index=True)  # critical, warning, info
    title = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, default='', nullable=True)
    line_number = db.Column(db.Integer, nullable=True)
    evidence = db.Column(db.Text, default='')
    recommended_action = db.Column(db.Text, default='', nullable=True)
    confidence = db.Column(db.String(20), default='high')  # high, medium, low
    estimated_impact = db.Column(db.String(20), default='medium')  # high, medium, low
    is_runtime_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    analysis_run = db.relationship('AnalysisRun', back_populates='findings')
    affected_file = db.relationship('ProjectFile', back_populates='findings')
    recommendation = db.relationship('Recommendation', back_populates='finding', uselist=False)

    def __repr__(self):
        return f"<Finding id={self.id} code='{self.finding_code}' severity='{self.severity}'>"


class DependencyEdge(db.Model):
    __tablename__ = 'dependency_edges'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('project_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    source_file_id = db.Column(db.Integer, db.ForeignKey('project_files.id', ondelete='CASCADE'), nullable=False, index=True)
    target_file_id = db.Column(db.Integer, db.ForeignKey('project_files.id', ondelete='SET NULL'), nullable=True, index=True)
    target_path_raw = db.Column(db.String(500), nullable=False)
    relationship_type = db.Column(db.String(30), default='link')  # stylesheet, script, image, font, import, media, link
    is_broken = db.Column(db.Boolean, default=False)
    evidence = db.Column(db.String(500), default='')

    version = db.relationship('ProjectVersion', back_populates='dependency_edges')
    source_file = db.relationship('ProjectFile', foreign_keys=[source_file_id], back_populates='outgoing_edges')
    target_file = db.relationship('ProjectFile', foreign_keys=[target_file_id], back_populates='incoming_edges')

    def __repr__(self):
        return f"<DependencyEdge id={self.id} type='{self.relationship_type}' broken={self.is_broken}>"
