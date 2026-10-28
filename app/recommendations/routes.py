"""
Optimization Recommendations Routes
Displays prioritized, actionable remediations tied to findings and browser audits.
"""

from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.project import ProjectVersion
from app.recommendations import recommendations_bp
from app.services.recommendation_engine import RecommendationEngine


def get_user_version_or_404(version_id: int) -> ProjectVersion:
    version = db.session.get(ProjectVersion, version_id)
    if not version:
        abort(404)
    if version.project.user_id != current_user.id:
        abort(403)
    return version


@recommendations_bp.route('/<int:version_id>')
@login_required
def index(version_id: int):
    """View all prioritized recommendations for this version."""
    version = get_user_version_or_404(version_id)
    recs = version.recommendations

    if not recs and version.has_analysis:
        engine = RecommendationEngine(version)
        recs = engine.generate_recommendations()

    return render_template(
        'recommendations/index.html',
        title=f"Optimization Recommendations — {version.project.name} ({version.version_label})",
        version=version,
        recommendations=recs
    )


@recommendations_bp.route('/<int:version_id>/refresh', methods=['POST'])
@login_required
def refresh(version_id: int):
    """Recalculate recommendations from current findings."""
    version = get_user_version_or_404(version_id)
    engine = RecommendationEngine(version)
    recs = engine.generate_recommendations()
    flash(f"Refreshed recommendations: {len(recs)} prioritized action items generated.", 'success')
    return redirect(url_for('recommendations.index', version_id=version.id))
