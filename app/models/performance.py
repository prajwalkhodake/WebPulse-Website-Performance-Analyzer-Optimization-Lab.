"""
Performance Test Run & Resource Timing Models
Tracks Playwright headless browser runs, Core Web Vitals, and network traces.
"""
from datetime import datetime, timezone
from app.extensions import db


class PerformanceTestRun(db.Model):
    __tablename__ = 'performance_test_runs'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('project_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    test_name = db.Column(db.String(100), default='Performance Audit')
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    preset = db.Column(db.String(20), default='desktop')  # desktop, mobile
    viewport_width = db.Column(db.Integer, default=1280)
    viewport_height = db.Column(db.Integer, default=800)
    browser_info = db.Column(db.String(100), default='Chromium (Playwright Sandbox)')
    entry_page = db.Column(db.String(255), default='index.html')

    # Core Web Vitals & Loading Timings (milliseconds, CLS unitless)
    ttfb_ms = db.Column(db.Float, nullable=True)
    dom_content_loaded_ms = db.Column(db.Float, nullable=True)
    load_event_ms = db.Column(db.Float, nullable=True)
    fcp_ms = db.Column(db.Float, nullable=True)
    lcp_ms = db.Column(db.Float, nullable=True)
    cls_score = db.Column(db.Float, nullable=True)

    # Request statistics
    total_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    total_transferred_bytes = db.Column(db.BigInteger, default=0)
    console_error_count = db.Column(db.Integer, default=0)
    console_errors = db.Column(db.JSON, default=list)

    # Calculated performance score (0-100)
    performance_score = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, default='')
    error_message = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    version = db.relationship('ProjectVersion', back_populates='test_runs')
    resources = db.relationship('ResourceMetric', back_populates='test_run', cascade='all, delete-orphan', order_by='ResourceMetric.start_time_ms')

    @property
    def total_transferred_kb(self):
        return round(self.total_transferred_bytes / 1024, 1)

    def calculate_performance_score(self):
        """
        Deterministic, transparent 0-100 calculation:
        - FCP: <1800ms (30pts), <3000ms (18pts), else 6pts
        - LCP: <2500ms (35pts), <4000ms (20pts), else 8pts
        - CLS: <0.10 (25pts), <0.25 (14pts), else 5pts
        - Load: <2500ms (10pts), <5000ms (6pts), else 2pts
        - Penalties: -5 pts per failed request, -3 pts per console error (up to 20 pts max penalty)
        """
        score = 0
        if self.fcp_ms is not None:
            if self.fcp_ms <= 1800:
                score += 30
            elif self.fcp_ms <= 3000:
                score += 18
            else:
                score += 6
        else:
            score += 15

        if self.lcp_ms is not None:
            if self.lcp_ms <= 2500:
                score += 35
            elif self.lcp_ms <= 4000:
                score += 20
            else:
                score += 8
        else:
            score += 20

        if self.cls_score is not None:
            if self.cls_score <= 0.1:
                score += 25
            elif self.cls_score <= 0.25:
                score += 14
            else:
                score += 5
        else:
            score += 15

        if self.load_event_ms is not None:
            if self.load_event_ms <= 2500:
                score += 10
            elif self.load_event_ms <= 5000:
                score += 6
            else:
                score += 2
        else:
            score += 5

        penalties = min(20, (self.failed_requests * 5) + (self.console_error_count * 3))
        self.performance_score = max(5, min(100, score - penalties))
        return self.performance_score

    def __repr__(self):
        return f"<PerformanceTestRun id={self.id} score={self.performance_score}>"


class ResourceMetric(db.Model):
    __tablename__ = 'resource_metrics'

    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.Integer, db.ForeignKey('performance_test_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    url = db.Column(db.String(1000), nullable=False)
    resource_name = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(30), default='other')
    status_code = db.Column(db.Integer, nullable=True)
    start_time_ms = db.Column(db.Float, default=0.0)
    duration_ms = db.Column(db.Float, default=0.0)
    transfer_size_bytes = db.Column(db.BigInteger, default=0)
    is_failed = db.Column(db.Boolean, default=False)
    error_text = db.Column(db.String(255), default='')
    timing_breakdown = db.Column(db.JSON, default=dict)

    test_run = db.relationship('PerformanceTestRun', back_populates='resources')

    @property
    def transfer_size_kb(self):
        return round(self.transfer_size_bytes / 1024, 1)

    def __repr__(self):
        return f"<ResourceMetric name='{self.resource_name}' duration={self.duration_ms:.1f}ms>"
