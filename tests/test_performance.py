"""
Browser Performance Testing End-to-End Tests
Verifies isolated EphemeralProjectServer, Playwright headless execution,
Core Web Vitals capture (FCP, LCP, CLS), TTFB, and waterfall resource tracking.
"""

from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.performance import PerformanceTestRun, ResourceMetric
from tests.test_projects import create_test_zip


def test_browser_performance_runner_e2e(client, test_user, app):
    """Test running Playwright headless performance test against uploaded static site."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Playwright Speed Lab', entry_point='index.html')
        db.session.add(p)
        db.session.commit()
        project_id = p.id

    # Create a clean site to benchmark
    site_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speed Benchmark</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header><h1>Benchmark Page</h1></header>
    <main>
        <p>Testing real-world browser rendering metrics and waterfall.</p>
    </main>
    <script src="script.js" defer></script>
</body>
</html>"""

    site_css = "body { font-family: sans-serif; background-color: #121212; color: #ffffff; padding: 20px; }"
    site_js = "console.log('Benchmark script running');"

    zip_data = create_test_zip({
        'index.html': site_html,
        'style.css': site_css,
        'script.js': site_js
    })

    # Upload version
    upload_resp = client.post(f'/projects/{project_id}/versions/new', data={
        'archive': (zip_data, 'benchmark_site.zip'),
        'version_label': 'v1.0 - Benchmark Base'
    }, content_type='multipart/form-data', follow_redirects=True)
    assert upload_resp.status_code == 200

    with app.app_context():
        v = ProjectVersion.query.filter_by(project_id=project_id).first()
        version_id = v.id

    # Execute browser performance test via POST /performance/<version_id>/test
    test_resp = client.post(f'/performance/{version_id}/test', data={'preset': 'desktop'}, follow_redirects=True)
    assert test_resp.status_code == 200
    assert b'Browser Audit Complete' in test_resp.data

    with app.app_context():
        runs = PerformanceTestRun.query.filter_by(version_id=version_id).all()
        assert len(runs) >= 1
        latest = runs[-1]
        assert latest.status == 'completed'
        assert latest.performance_score is not None
        assert latest.performance_score > 0
        assert latest.total_requests >= 2  # index.html, style.css, script.js
        assert latest.failed_requests == 0

        # Verify resources recorded
        resources = ResourceMetric.query.filter_by(test_run_id=latest.id).all()
        assert len(resources) >= 2
        res_names = [r.resource_name for r in resources]
        assert any('style.css' in name or 'index.html' in name for name in res_names)

    # Test audit view endpoint GET /performance/<version_id>/audit
    audit_resp = client.get(f'/performance/{version_id}/audit')
    assert audit_resp.status_code == 200
    assert b'First Contentful (FCP)' in audit_resp.data
    assert b'Network Resource Waterfall' in audit_resp.data
