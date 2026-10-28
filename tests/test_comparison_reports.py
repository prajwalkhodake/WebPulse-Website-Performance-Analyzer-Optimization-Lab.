"""
Comparison, Reporting, and Recommendation Tests
Verifies version diffing, recommendations engine, HTML printable reports, and JSON export.
"""

from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.analysis import AnalysisRun, Finding
from app.models.performance import PerformanceTestRun
from app.models.recommendation import Recommendation
from app.services.report_generator import VersionComparator, ReportGenerator
from app.services.recommendation_engine import RecommendationEngine


def test_version_comparator_and_diffs(client, test_user, app):
    """Test VersionComparator accurately computes resolved findings, new findings, and metrics."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Diff Project')
        db.session.add(p)
        db.session.commit()

        v1 = ProjectVersion(project_id=p.id, version_number=1, version_label='v1.0 - Baseline', storage_path='v1', total_files=5, total_size_bytes=100000)
        v2 = ProjectVersion(project_id=p.id, version_number=2, version_label='v2.0 - Optimized', storage_path='v2', total_files=4, total_size_bytes=50000)
        db.session.add_all([v1, v2])
        db.session.commit()

        # Analysis for v1 (3 findings)
        a1 = AnalysisRun(version_id=v1.id, status='completed')
        db.session.add(a1)
        db.session.commit()
        f1_1 = Finding(analysis_run_id=a1.id, finding_code='IMG_MISSING_ALT', severity='warning', title='Missing Alt')
        f1_2 = Finding(analysis_run_id=a1.id, finding_code='CSS_OVERSIZED', severity='warning', title='Large CSS')
        f1_3 = Finding(analysis_run_id=a1.id, finding_code='PERSISTENT_ISSUE', severity='info', title='Persistent')
        db.session.add_all([f1_1, f1_2, f1_3])

        # Analysis for v2 (resolved CSS_OVERSIZED and IMG_MISSING_ALT, introduced NEW_WARNING, kept PERSISTENT_ISSUE)
        a2 = AnalysisRun(version_id=v2.id, status='completed')
        db.session.add(a2)
        db.session.commit()
        f2_1 = Finding(analysis_run_id=a2.id, finding_code='PERSISTENT_ISSUE', severity='info', title='Persistent')
        f2_2 = Finding(analysis_run_id=a2.id, finding_code='NEW_WARNING', severity='warning', title='New Issue')
        db.session.add_all([f2_1, f2_2])

        # Performance runs
        t1 = PerformanceTestRun(
            version_id=v1.id, test_name='Audit v1', status='completed', preset='desktop',
            performance_score=60, load_event_ms=1200.0, fcp_ms=450.0, lcp_ms=900.0, cls_score=0.15,
            total_requests=10, total_transferred_bytes=100000
        )
        t2 = PerformanceTestRun(
            version_id=v2.id, test_name='Audit v2', status='completed', preset='desktop',
            performance_score=92, load_event_ms=350.0, fcp_ms=150.0, lcp_ms=280.0, cls_score=0.01,
            total_requests=6, total_transferred_bytes=45000
        )
        db.session.add_all([t1, t2])
        db.session.commit()

        # Test comparator logic
        comparator = VersionComparator(v1, v2)
        diff = comparator.compare()

        assert diff['resolved_count'] == 2
        resolved_codes = [f.finding_code for f in diff['resolved_findings']]
        assert 'IMG_MISSING_ALT' in resolved_codes
        assert 'CSS_OVERSIZED' in resolved_codes

        assert diff['new_count'] == 1
        assert diff['new_findings'][0].finding_code == 'NEW_WARNING'

        assert diff['persistent_count'] == 1
        assert diff['persistent_findings'][0].finding_code == 'PERSISTENT_ISSUE'

        # Metrics deltas
        md = diff['metrics_diff']
        assert md['score_delta'] == 32.0  # 92 - 60
        assert md['load_delta'] == -850.0 # 350 - 1200
        assert md['requests_delta'] == -4
        assert md['bytes_delta'] == -55000

        project_id = p.id
        v1_id = v1.id
        v2_id = v2.id

    # Test HTTP compare page
    response = client.get(f'/projects/{project_id}/compare?v1={v1_id}&v2={v2_id}')
    assert response.status_code == 200
    assert b'Version Comparison' in response.data
    assert b'Resolved Findings' in response.data or b'Resolved Issues' in response.data or b'Resolved' in response.data


def test_html_printable_report(client, test_user, app):
    """Test generating a standalone printable HTML report."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Report Project')
        db.session.add(p)
        db.session.commit()

        v = ProjectVersion(project_id=p.id, version_number=1, version_label='v1.0 - Production', storage_path='v1', total_files=3, total_size_bytes=42000)
        db.session.add(v)
        db.session.commit()

        a = AnalysisRun(version_id=v.id, status='completed')
        db.session.add(a)
        db.session.commit()
        f = Finding(analysis_run_id=a.id, finding_code='HTML_NO_VIEWPORT', severity='critical', title='Missing Viewport', recommended_action='Add viewport meta tag')
        db.session.add(f)

        t = PerformanceTestRun(version_id=v.id, test_name='Desktop', status='completed', performance_score=85, load_event_ms=400.0)
        db.session.add(t)

        r = Recommendation(version_id=v.id, title='Add Viewport Meta', priority='P1', priority_score=90, action_plan='Add <meta name=viewport>')
        db.session.add(r)
        db.session.commit()
        version_id = v.id

    response = client.get(f'/reports/{version_id}/html')
    assert response.status_code == 200
    assert response.content_type.startswith('text/html')
    assert b'WebPulse Performance Audit' in response.data or b'Report Project' in response.data
    assert b'Missing Viewport' in response.data
    assert b'Add Viewport Meta' in response.data


def test_json_export_endpoint(client, test_user, app):
    """Test exporting structured JSON audit data."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='API Export Project')
        db.session.add(p)
        db.session.commit()

        v = ProjectVersion(project_id=p.id, version_number=1, version_label='v1.0', storage_path='v1', total_files=2, total_size_bytes=25000)
        db.session.add(v)
        db.session.commit()
        version_id = v.id

    response = client.get(f'/reports/{version_id}/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data['project_name'] == 'API Export Project'
    assert 'summary' in data
    assert 'findings' in data
    assert 'recommendations' in data
    assert 'resources' in data


def test_recommendations_generation_and_view(client, test_user, app):
    """Test recommendation engine creates prioritized recommendations and view displays them."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Rec Project')
        db.session.add(p)
        db.session.commit()

        v = ProjectVersion(project_id=p.id, version_number=1, version_label='v1.0', storage_path='v1')
        db.session.add(v)
        db.session.commit()

        a = AnalysisRun(version_id=v.id, status='completed')
        db.session.add(a)
        db.session.commit()

        # Add critical and warning findings
        f1 = Finding(analysis_run_id=a.id, finding_code='HTML_MISSING_VIEWPORT', severity='critical', title='Missing Viewport', recommended_action='Add viewport')
        f2 = Finding(analysis_run_id=a.id, finding_code='CSS_OVERSIZED', severity='warning', title='Large CSS', recommended_action='Minify CSS')
        db.session.add_all([f1, f2])
        db.session.commit()

        # Run recommendation engine
        engine = RecommendationEngine(v)
        recs = engine.generate_recommendations()
        assert len(recs) >= 2
        priorities = [r.priority for r in recs]
        assert 'high' in priorities

        version_id = v.id

    response = client.get(f'/recommendations/{version_id}')
    assert response.status_code == 200
    assert b'Optimization Action Plan' in response.data or b'Recommendations' in response.data


def test_version_compare_when_audits_are_pending(client, test_user, app):
    """Test version comparison renders gracefully with an informative alert box when audits have not been run."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Unaudited Project')
        db.session.add(p)
        db.session.commit()

        v1 = ProjectVersion(project_id=p.id, version_number=1, version_label='v1.0 - Draft', storage_path='v1')
        v2 = ProjectVersion(project_id=p.id, version_number=2, version_label='v2.0 - Draft', storage_path='v2')
        db.session.add_all([v1, v2])
        db.session.commit()

        p_id = p.id
        v1_id = v1.id
        v2_id = v2.id

    # Access comparison page before running audits
    response = client.get(f'/projects/{p_id}/compare?v1={v1_id}&v2={v2_id}')
    # Must return 200 OK without any Jinja template UndefinedError
    assert response.status_code == 200
    # Must display the helpful notification banner explaining that audits are required
    assert b'Performance Audit / Static Analysis Required' in response.data
    assert b'Trigger Missing Audits Now' in response.data

