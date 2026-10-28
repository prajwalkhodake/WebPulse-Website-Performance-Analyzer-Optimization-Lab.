"""
Dashboard Routes
Serves the authenticated user's workspace dashboard and project overview.
"""
from flask import render_template
from flask_login import login_required, current_user
from app.dashboard import dashboard_bp
from app.models.project import Project, ProjectVersion
from app.models.analysis import AnalysisRun, Finding


@dashboard_bp.route('/')
@login_required
def index():
    """User dashboard landing view with real database metrics."""
    user_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
    project_ids = [p.id for p in user_projects]

    total_projects = len(user_projects)

    if project_ids:
        user_versions = ProjectVersion.query.filter(ProjectVersion.project_id.in_(project_ids)).all()
        version_ids = [v.id for v in user_versions]
        total_versions = len(user_versions)

        if version_ids:
            analyses = AnalysisRun.query.filter(AnalysisRun.version_id.in_(version_ids), AnalysisRun.status == 'completed').all()
            total_analyses = len(analyses)
            analysis_ids = [a.id for a in analyses]
            total_findings = Finding.query.filter(Finding.analysis_run_id.in_(analysis_ids)).count() if analysis_ids else 0
        else:
            total_analyses = 0
            total_findings = 0
    else:
        total_versions = 0
        total_analyses = 0
        total_findings = 0

    context = {
        'total_projects': total_projects,
        'total_versions': total_versions,
        'total_analyses': total_analyses,
        'total_findings': total_findings,
        'projects': user_projects,
        'recent_projects': user_projects[:5]
    }
    return render_template('dashboard/index.html', title='Workspace Dashboard', **context)
