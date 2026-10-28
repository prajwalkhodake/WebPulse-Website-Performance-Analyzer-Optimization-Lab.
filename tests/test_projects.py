"""
Project Management and Archive Ingestion Tests
Verifies project CRUD, anti-Zip-Slip validation, private extraction, and file inventory.
"""

import io
import zipfile
from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.analysis import ProjectFile


def create_test_zip(files: dict) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    buf.seek(0)
    return buf


def test_project_creation(client, test_user, app):
    """Test user can create a project."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    response = client.post('/projects/new', data={
        'name': 'E-Commerce Redesign',
        'description': 'Online storefront redesign project',
        'entry_point': 'index.html'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        p = Project.query.filter_by(name='E-Commerce Redesign').first()
        assert p is not None
        assert p.user_id == test_user.id
        assert p.entry_point == 'index.html'


def test_valid_archive_upload_and_inventory(client, test_user, app):
    """Test uploading a valid ZIP archive and verifying file inventory."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Test Site', entry_point='index.html')
        db.session.add(p)
        db.session.commit()
        project_id = p.id

    zip_data = create_test_zip({
        'index.html': '<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>',
        'css/style.css': 'body { background: #000; }',
        'js/app.js': 'console.log("ready");'
    })

    response = client.post(f'/projects/{project_id}/versions/new', data={
        'archive': (zip_data, 'test_site.zip'),
        'version_label': 'v1.0 — Test Upload',
        'notes': 'Initial automated test version'
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    assert b'3 files inventoried' in response.data

    with app.app_context():
        v = ProjectVersion.query.filter_by(project_id=project_id, version_number=1).first()
        assert v is not None
        assert v.total_files == 3
        files = ProjectFile.query.filter_by(version_id=v.id).all()
        assert len(files) == 3
        paths = [f.relative_path for f in files]
        assert 'index.html' in paths
        assert 'css/style.css' in paths
        assert 'js/app.js' in paths


def test_zip_slip_rejection(client, test_user, app):
    """Test that malicious path traversal archives (../) are rejected."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    with app.app_context():
        p = Project(user_id=test_user.id, name='Security Test', entry_point='index.html')
        db.session.add(p)
        db.session.commit()
        project_id = p.id

    # Craft zip with traversal entry
    malicious_zip = create_test_zip({
        '../../etc/passwd': 'root:x:0:0:',
        'index.html': '<h1>Safe</h1>'
    })

    response = client.post(f'/projects/{project_id}/versions/new', data={
        'archive': (malicious_zip, 'exploit.zip'),
        'version_label': 'v1.0'
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    assert b'Malicious path traversal' in response.data or b'Validation Failed' in response.data


def test_seed_demo_project(client, test_user, app):
    """Test that seeding a demo project creates both v1 and v2 with files."""
    client.post('/auth/login', data={'username_or_email': 'testengineer', 'password': 'SecurePass123!'}, follow_redirects=True)

    response = client.post('/projects/seed-demo', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sample demo project created' in response.data

    with app.app_context():
        demo_p = Project.query.filter_by(is_demo=True, user_id=test_user.id).first()
        assert demo_p is not None
        assert demo_p.version_count == 2
