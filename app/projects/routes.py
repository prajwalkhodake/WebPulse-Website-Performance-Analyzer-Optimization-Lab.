"""
Project Management and Version Ingestion Routes
Handles project creation, archive upload, version explorer, and demo seeding.
"""

import os
from pathlib import Path
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.analysis import ProjectFile, AnalysisRun
from app.projects import projects_bp
from app.projects.forms import ProjectCreateForm, ProjectVersionUploadForm
from app.services.archive_validator import ArchiveValidator, ValidationError
from app.services.project_detector import ProjectDetector, get_file_category
from app.services.static_analyzer import StaticAnalyzer
from app.services.dependency_mapper import DependencyMapper
from app.services.recommendation_engine import RecommendationEngine
from app.services.report_generator import VersionComparator
from app.services.sample_project_seeder import create_sample_project_v1_zip, create_sample_project_v2_zip


def get_user_project_or_404(project_id: int) -> Project:
    """Ensure project exists and belongs to current user."""
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)
    if project.user_id != current_user.id:
        abort(403)
    return project


def get_user_version_or_404(project_id: int, version_id: int) -> ProjectVersion:
    """Ensure version exists and belongs to user's project."""
    project = get_user_project_or_404(project_id)
    version = db.session.get(ProjectVersion, version_id)
    if not version or version.project_id != project.id:
        abort(404)
    return version


@projects_bp.route('/')
@login_required
def index():
    """List all projects belonging to the logged-in user."""
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
    return render_template('projects/index.html', title='Projects & Workspaces', projects=projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project workspace."""
    form = ProjectCreateForm()
    if form.validate_on_submit():
        project = Project(
            user_id=current_user.id,
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else '',
            entry_point=form.entry_point.data.strip() if form.entry_point.data else 'index.html'
        )
        db.session.add(project)
        db.session.commit()
        flash(f"Project '{project.name}' created successfully! Upload your first version archive below.", 'success')
        return redirect(url_for('projects.upload_version', project_id=project.id))

    return render_template('projects/create.html', title='Create New Project', form=form)


@projects_bp.route('/<int:project_id>')
@login_required
def detail(project_id: int):
    """View project details and list of version snapshots."""
    project = get_user_project_or_404(project_id)
    return render_template('projects/detail.html', title=f"Project: {project.name}", project=project)


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id: int):
    """Delete project and associated storage files."""
    project = get_user_project_or_404(project_id)
    project_name = project.name

    # Remove storage files if present
    base_storage = Path(current_app.config['STORAGE_DIR'])
    user_project_dir = base_storage / 'extracted' / f"user_{current_user.id}" / f"project_{project.id}"
    if user_project_dir.exists():
        import shutil
        shutil.rmtree(user_project_dir, ignore_errors=True)

    db.session.delete(project)
    db.session.commit()
    flash(f"Project '{project_name}' and all associated versions were deleted.", 'info')
    return redirect(url_for('projects.index'))


@projects_bp.route('/<int:project_id>/versions/new', methods=['GET', 'POST'])
@login_required
def upload_version(project_id: int):
    """Upload a new project version ZIP archive."""
    project = get_user_project_or_404(project_id)
    form = ProjectVersionUploadForm()

    next_version_num = (project.latest_version.version_number + 1) if project.latest_version else 1

    if form.validate_on_submit():
        uploaded_file = form.archive.data
        orig_filename = secure_filename(uploaded_file.filename) or 'archive.zip'
        v_label = form.version_label.data.strip() if form.version_label.data else f"v{next_version_num}.0"

        validator = ArchiveValidator(
            file_storage=uploaded_file,
            user_id=current_user.id,
            project_id=project.id,
            version_num=next_version_num
        )

        try:
            result = validator.validate_and_extract()
        except ValidationError as e:
            flash(f"Archive Validation Failed: {str(e)}", 'danger')
            return render_template('projects/upload.html', title='Upload Version Archive', project=project, form=form, next_version_num=next_version_num)

        # Detect files and entry point
        extracted_dir = Path(result['absolute_path'])
        detector = ProjectDetector(extracted_dir)
        detection_result = detector.detect()

        # Create ProjectVersion record
        version = ProjectVersion(
            project_id=project.id,
            version_number=next_version_num,
            version_label=v_label,
            notes=form.notes.data.strip() if form.notes.data else '',
            archive_filename=orig_filename,
            storage_path=result['storage_path'],
            total_files=detection_result['total_files'],
            total_size_bytes=detection_result['total_size_bytes']
        )
        db.session.add(version)
        db.session.flush()

        if detection_result.get('entry_point') and not project.entry_point:
            project.entry_point = detection_result['entry_point']

        # Inventory individual files
        files_to_add = []
        for dirpath, _, filenames in os.walk(extracted_dir):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if not file_path.is_file():
                    continue

                rel_path = str(file_path.relative_to(extracted_dir)).replace('\\', '/')
                size = file_path.stat().st_size
                ext = file_path.suffix.lower()
                cat = get_file_category(ext)
                is_entry = (rel_path.lower() == 'index.html' or rel_path == project.entry_point)

                # Compute line count if text
                line_count = None
                if ext in ('.html', '.htm', '.css', '.js', '.json', '.svg', '.md', '.txt'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                    except Exception:
                        pass

                pf = ProjectFile(
                    version_id=version.id,
                    relative_path=rel_path,
                    file_type=cat,
                    file_size_bytes=size,
                    line_count=line_count,
                    is_entry_point=is_entry
                )
                files_to_add.append(pf)

        db.session.add_all(files_to_add)
        db.session.commit()

        flash(f"Successfully uploaded {v_label}! {result['extracted_file_count']} files inventoried.", 'success')
        return redirect(url_for('projects.version_detail', project_id=project.id, version_id=version.id))

    return render_template('projects/upload.html', title='Upload Version Archive', project=project, form=form, next_version_num=next_version_num)


@projects_bp.route('/<int:project_id>/versions/<int:version_id>')
@login_required
def version_detail(project_id: int, version_id: int):
    """View detailed file inventory and actions for a project version."""
    project = get_user_project_or_404(project_id)
    version = get_user_version_or_404(project_id, version_id)
    return render_template('projects/version_detail.html', title=f"{project.name} - {version.version_label}", project=project, version=version)


@projects_bp.route('/<int:project_id>/compare')
@login_required
def compare(project_id: int):
    """Compare two versions of the same project."""
    project = get_user_project_or_404(project_id)
    versions = project.versions
    if len(versions) < 2:
        flash("You need at least 2 versions to run a version comparison diff.", 'warning')
        return redirect(url_for('projects.detail', project_id=project.id))

    v_before_id = request.args.get('v1', type=int)
    v_after_id = request.args.get('v2', type=int)

    if not v_before_id or not v_after_id:
        v_before = versions[1] if len(versions) > 1 else versions[0]
        v_after = versions[0]
    else:
        v_before = get_user_version_or_404(project_id, v_before_id)
        v_after = get_user_version_or_404(project_id, v_after_id)

    comparator = VersionComparator(v_before, v_after)
    comparison_data = comparator.compare()

    return render_template(
        'projects/compare.html',
        title=f"Compare Versions — {project.name}",
        project=project,
        versions=versions,
        v_before=v_before,
        v_after=v_after,
        comp=comparison_data
    )


@projects_bp.route('/seed-demo', methods=['POST'])
@login_required
def seed_demo():
    """Generates a complete sample project with v1.0 (unoptimized) and v2.0 (optimized)."""
    # 1. Create Demo Project
    demo_project = Project(
        user_id=current_user.id,
        name="Aura Architecture (Sample Lab Project)",
        description="A real-world multi-page portfolio website showcasing before-and-after optimization. Includes intentional issues in v1 (oversized images, blocking scripts, missing alt tags) and resolved optimizations in v2.",
        entry_point="index.html",
        is_demo=True
    )
    db.session.add(demo_project)
    db.session.commit()

    # 2. Ingest v1.0
    v1_zip_buf = create_sample_project_v1_zip()
    v1_validator = ArchiveValidator(
        file_storage=v1_zip_buf,
        user_id=current_user.id,
        project_id=demo_project.id,
        version_num=1
    )
    res_v1 = v1_validator.validate_and_extract()
    v1 = ProjectVersion(
        project_id=demo_project.id,
        version_number=1,
        version_label="v1.0 — Baseline (Unoptimized)",
        notes="Initial project build before performance audit. Contains heavy uncompressed hero images, render blocking scripts in <head>, and broken CSS references.",
        archive_filename="aura_architecture_v1_baseline.zip",
        storage_path=res_v1['storage_path'],
        total_files=res_v1['extracted_file_count'],
        total_size_bytes=res_v1['total_size_bytes']
    )
    db.session.add(v1)
    db.session.flush()

    # Inventory v1 files
    dir_v1 = Path(res_v1['absolute_path'])
    for dp, _, fnames in os.walk(dir_v1):
        for fn in fnames:
            fp = Path(dp) / fn
            rel = str(fp.relative_to(dir_v1)).replace('\\', '/')
            ext = fp.suffix.lower()
            pf = ProjectFile(
                version_id=v1.id,
                relative_path=rel,
                file_type='image' if ext in ('.png', '.jpg', '.jpeg') else ('html' if ext in ('.html', '.htm') else ('css' if ext == '.css' else 'javascript')),
                file_size_bytes=fp.stat().st_size,
                is_entry_point=(rel == 'index.html')
            )
            db.session.add(pf)

    # 3. Ingest v2.0
    v2_zip_buf = create_sample_project_v2_zip()
    v2_validator = ArchiveValidator(
        file_storage=v2_zip_buf,
        user_id=current_user.id,
        project_id=demo_project.id,
        version_num=2
    )
    res_v2 = v2_validator.validate_and_extract()
    v2 = ProjectVersion(
        project_id=demo_project.id,
        version_number=2,
        version_label="v2.0 — Fully Optimized",
        notes="Optimized release: WebP image conversion, deferred script loading, explicit image aspect ratios, and pruned CSS.",
        archive_filename="aura_architecture_v2_optimized.zip",
        storage_path=res_v2['storage_path'],
        total_files=res_v2['extracted_file_count'],
        total_size_bytes=res_v2['total_size_bytes']
    )
    db.session.add(v2)
    db.session.flush()

    # Inventory v2 files
    dir_v2 = Path(res_v2['absolute_path'])
    for dp, _, fnames in os.walk(dir_v2):
        for fn in fnames:
            fp = Path(dp) / fn
            rel = str(fp.relative_to(dir_v2)).replace('\\', '/')
            ext = fp.suffix.lower()
            pf = ProjectFile(
                version_id=v2.id,
                relative_path=rel,
                file_type='image' if ext in ('.png', '.jpg', '.jpeg', '.webp') else ('html' if ext in ('.html', '.htm') else ('css' if ext == '.css' else 'javascript')),
                file_size_bytes=fp.stat().st_size,
                is_entry_point=(rel == 'index.html')
            )
            db.session.add(pf)

    db.session.commit()

    flash("Sample demo project created with v1.0 Baseline and v2.0 Optimized versions! You can now analyze either version or compare them.", 'success')
    return redirect(url_for('projects.detail', project_id=demo_project.id))
