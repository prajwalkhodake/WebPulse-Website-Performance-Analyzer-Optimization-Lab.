"""
Public Routes and System Security Tests
Verifies landing, features, about, error pages, and HTTP security response headers.
"""


def test_landing_page(client):
    """Test that landing page renders successfully with proper branding."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'WebPulse' in response.data
    assert b'Analyze, Benchmark &amp; Optimize Websites' in response.data or b'Analyze, Benchmark & Optimize Websites' in response.data


def test_features_page(client):
    """Test that features page renders all 4 key engine sections."""
    response = client.get('/features')
    assert response.status_code == 200
    assert b'Comprehensive Lab Suite' in response.data
    assert b'Rule-Based Static Analysis' in response.data
    assert b'Cytoscape Dependency Mapping' in response.data
    assert b'Playwright Sandbox Testing' in response.data


def test_about_page(client):
    """Test that academic documentation page renders correctly."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b'Engineering Rationale &amp; System Architecture' in response.data or b'Engineering Rationale & System Architecture' in response.data
    assert b'Problem Statement' in response.data
    assert b'Python Flask 3' in response.data


def test_404_error_page(client):
    """Test that non-existent routes render custom 404 page."""
    response = client.get('/non-existent-route-for-testing-404')
    assert response.status_code == 404
    assert b'404' in response.data
    assert b'Lost in the Pipeline' in response.data


def test_security_headers(client):
    """Verify essential security headers are attached to responses."""
    response = client.get('/')
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
