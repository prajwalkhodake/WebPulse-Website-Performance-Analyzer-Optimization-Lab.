"""
Reporting and Export Routes
Generates standalone printable HTML reports and downloadable JSON audit payloads.
"""

from flask import Response, abort, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.project import ProjectVersion
from app.reports import reports_bp
from app.services.report_generator import ReportGenerator


def get_user_version_or_404(version_id: int) -> ProjectVersion:
    version = db.session.get(ProjectVersion, version_id)
    if not version:
        abort(404)
    if version.project.user_id != current_user.id:
        abort(403)
    return version


@reports_bp.route('/<int:version_id>/html')
@login_required
def html_report(version_id: int):
    """Serve standalone printable HTML audit report."""
    version = get_user_version_or_404(version_id)
    generator = ReportGenerator(version)
    html_content = generator.generate_standalone_html_report()
    return Response(html_content, mimetype='text/html')


@reports_bp.route('/<int:version_id>/json')
@login_required
def json_report(version_id: int):
    """Serve downloadable JSON audit data."""
    version = get_user_version_or_404(version_id)
    generator = ReportGenerator(version)
    return jsonify(generator.generate_json_export())
