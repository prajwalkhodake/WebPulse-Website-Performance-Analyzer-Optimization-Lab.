"""
Custom HTTP Error Handlers
Provides user-friendly error templates with safe diagnostics and clear recovery options.
"""
from flask import render_template
from app.errors import errors_bp
from app.extensions import db


@errors_bp.app_errorhandler(403)
def forbidden(error):
    return render_template(
        'errors/403.html',
        title='403 Forbidden — Access Restricted',
        description='You do not have permission to access the requested resource or project.'
    ), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    return render_template(
        'errors/404.html',
        title='404 Not Found — Resource Missing',
        description='The file, project, or analysis run you requested does not exist or has been removed.'
    ), 404


@errors_bp.app_errorhandler(413)
def request_entity_too_large(error):
    return render_template(
        'errors/413.html',
        title='413 Payload Too Large — Upload Exceeded',
        description='The uploaded archive exceeds the allowed size limit (maximum 50 MB).'
    ), 413


@errors_bp.app_errorhandler(500)
def internal_server_error(error):
    db.session.rollback()
    return render_template(
        'errors/500.html',
        title='500 Internal Error — Unexpected Condition',
        description='An unexpected server error occurred while processing your request. The incident has been recorded.'
    ), 500
