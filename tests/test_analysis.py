"""
Static Analysis and Dependency Mapping Tests
Verifies static checks, finding persistence, Cytoscape graph extraction, and recommendations.
"""

from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.analysis import ProjectFile, AnalysisRun, Finding, DependencyEdge
from app.models.recommendation import Recommendation
from tests.test_projects import create_test_zip


def test_static_analysis_and_graph_extraction(client, test_user, app):
    """Test running static analysis extracts HTML issues, broken links, and edges."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Audit Project', entry_point='index.html')
        db.session.add(p)
        db.session.commit()
        project_id = p.id

    # Create project containing intentional issues: missing alt, blocking script, broken link
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <script src="js/heavy-tracker.js"></script>
    <link rel="stylesheet" href="css/missing-styles.css">
</head>
<body>
    <h1>Audit</h1>
    <img src="images/logo.png">
</body>
</html>"""

    zip_data = create_test_zip({
        'index.html': html_content,
        'js/heavy-tracker.js': 'console.log("tracker");',
        'images/logo.png': 'fake-image-bytes'
    })

    # Upload version
    client.post(f'/projects/{project_id}/versions/new', data={
        'archive': (zip_data, 'site.zip'),
        'version_label': 'v1.0'
    }, content_type='multipart/form-data', follow_redirects=True)

    with app.app_context():
        v = ProjectVersion.query.filter_by(project_id=project_id).first()
        version_id = v.id

    # Run static analysis
    response = client.post(f'/analysis/{version_id}/analyze', follow_redirects=True)
    assert response.status_code == 200
    assert b'Static Analysis Complete' in response.data

    with app.app_context():
        analysis = AnalysisRun.query.filter_by(version_id=version_id).first()
        assert analysis is not None
        assert analysis.status == 'completed'
        findings = Finding.query.filter_by(analysis_run_id=analysis.id).all()
        assert len(findings) > 0

        # Verify dependency edges were generated
        edges = DependencyEdge.query.filter_by(version_id=version_id).all()
        assert len(edges) > 0
        broken_edges = [e for e in edges if e.is_broken]
        assert len(broken_edges) > 0

        # Verify recommendations were generated
        recs = Recommendation.query.filter_by(version_id=version_id).all()
        assert len(recs) > 0


def test_cytoscape_api_endpoint(client, test_user, app):
    """Test that graph API endpoint returns valid Cytoscape elements structure."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Graph Site')
        db.session.add(p)
        db.session.commit()
        v = ProjectVersion(project_id=p.id, version_number=1, storage_path='test')
        db.session.add(v)
        db.session.commit()
        pf = ProjectFile(version_id=v.id, relative_path='index.html', file_type='html', is_entry_point=True)
        db.session.add(pf)
        db.session.commit()
        version_id = v.id

    response = client.get(f'/analysis/api/{version_id}/graph-data')
    assert response.status_code == 200
    data = response.get_json()
    assert 'elements' in data
    assert 'nodes' in data['elements']
    assert 'edges' in data['elements']
    assert len(data['elements']['nodes']) >= 1
