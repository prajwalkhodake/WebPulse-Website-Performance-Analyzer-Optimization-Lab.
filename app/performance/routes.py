"""
Browser Performance Testing Routes
Executes sandboxed Playwright runs, captures Core Web Vitals, and displays waterfall traces.
"""

from pathlib import Path
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.project import ProjectVersion
from app.models.performance import PerformanceTestRun, ResourceMetric
from app.performance import performance_bp
from app.services.browser_runner import BrowserRunner


def get_user_version_or_404(version_id: int) -> ProjectVersion:
    version = db.session.get(ProjectVersion, version_id)
    if not version:
        abort(404)
    if version.project.user_id != current_user.id:
        abort(403)
    return version


@performance_bp.route('/<int:version_id>/test', methods=['POST'])
@login_required
def run_test(version_id: int):
    """Executes a headless Chromium performance audit in an isolated sandbox."""
    version = get_user_version_or_404(version_id)
    base_storage = Path(current_app.config['STORAGE_DIR'])
    extracted_dir = base_storage / version.storage_path

    if not extracted_dir.exists():
        flash("Extracted project directory is missing on server storage.", 'danger')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    entry_page = version.project.entry_point or 'index.html'
    preset = request.form.get('preset', 'desktop')

    runner = BrowserRunner(project_dir=extracted_dir, entry_page=entry_page, preset=preset)

    try:
        metrics = runner.run_performance_test()
    except Exception as e:
        flash(f"Browser performance test encountered an error: {str(e)}", 'danger')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    # Create PerformanceTestRun record
    test_run = PerformanceTestRun(
        version_id=version.id,
        test_name=f"Performance Audit ({preset.capitalize()})",
        status=metrics.get('status', 'completed'),
        preset=preset,
        viewport_width=metrics.get('viewport_width', 1280),
        viewport_height=metrics.get('viewport_height', 800),
        ttfb_ms=metrics.get('ttfb_ms'),
        dom_content_loaded_ms=metrics.get('dom_content_loaded_ms'),
        load_event_ms=metrics.get('load_event_ms'),
        fcp_ms=metrics.get('fcp_ms'),
        lcp_ms=metrics.get('lcp_ms'),
        cls_score=metrics.get('cls_score'),
        total_requests=metrics.get('total_requests', 0),
        failed_requests=metrics.get('failed_requests', 0),
        total_transferred_bytes=metrics.get('total_transferred_bytes', 0),
        console_error_count=len(metrics.get('console_errors', [])),
        console_errors=metrics.get('console_errors', [])
    )
    test_run.calculate_performance_score()
    db.session.add(test_run)
    db.session.flush()

    # Save resource waterfalls
    resources_to_add = []
    for rm in metrics.get('resources', []):
        res = ResourceMetric(
            test_run_id=test_run.id,
            url=rm.get('url', ''),
            resource_name=rm.get('resource_name', ''),
            resource_type=rm.get('resource_type', 'other'),
            status_code=rm.get('status_code'),
            start_time_ms=rm.get('start_time_ms', 0.0),
            duration_ms=rm.get('duration_ms', 0.0),
            transfer_size_bytes=rm.get('transfer_size_bytes', 0),
            is_failed=rm.get('is_failed', False),
            error_text=rm.get('error_text', ''),
            timing_breakdown=rm.get('timing_breakdown', {})
        )
        resources_to_add.append(res)

    db.session.add_all(resources_to_add)
    db.session.commit()

    flash(f"Browser Audit Complete! Score: {test_run.performance_score}/100 (Load: {test_run.load_event_ms or 0:.0f}ms).", 'success')
    return redirect(url_for('performance.audit', version_id=version.id))


@performance_bp.route('/<int:version_id>/audit')
@login_required
def audit(version_id: int):
    """View performance audit metrics, Core Web Vitals, and resource waterfall."""
    version = get_user_version_or_404(version_id)
    latest_run = version.latest_test_run

    if not latest_run:
        flash("No performance test runs found for this version. Run an audit first.", 'warning')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    return render_template(
        'performance/audit.html',
        title=f"Performance Audit — {version.project.name} ({version.version_label})",
        version=version,
        test_run=latest_run,
        resources=latest_run.resources
    )
