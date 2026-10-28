"""
Static Analysis and Dependency Graph Routes
Runs static audits, persists findings, extracts dependency networks, and serves Cytoscape data.
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.project import Project, ProjectVersion
from app.models.analysis import ProjectFile, AnalysisRun, Finding, DependencyEdge
from app.analysis import analysis_bp
from app.services.static_analyzer import StaticAnalyzer
from app.services.dependency_mapper import DependencyMapper
from app.services.recommendation_engine import RecommendationEngine


def get_user_version_or_404(version_id: int) -> ProjectVersion:
    """Ensure version exists and belongs to current user."""
    version = db.session.get(ProjectVersion, version_id)
    if not version:
        abort(404)
    if version.project.user_id != current_user.id:
        abort(403)
    return version


@analysis_bp.route('/<int:version_id>/analyze', methods=['POST'])
@login_required
def run_analysis(version_id: int):
    """Executes the Static Analysis Engine on the specified version."""
    version = get_user_version_or_404(version_id)
    base_storage = Path(current_app.config['STORAGE_DIR'])
    extracted_dir = base_storage / version.storage_path

    if not extracted_dir.exists():
        flash("Extracted project directory is missing on server storage.", 'danger')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    # Initialize or reset AnalysisRun
    analysis_run = version.analysis
    if not analysis_run:
        analysis_run = AnalysisRun(version_id=version.id, status='running')
        db.session.add(analysis_run)
    else:
        # Clear existing findings for clean re-analysis
        Finding.query.filter_by(analysis_run_id=analysis_run.id).delete()
        DependencyEdge.query.filter_by(version_id=version.id).delete()
        analysis_run.status = 'running'
        analysis_run.started_at = datetime.now(timezone.utc)

    db.session.commit()

    start_time = time.time()

    # 1. Map files for analyzer
    files_map = {}
    path_to_file_record = {}
    for pf in version.files:
        files_map[pf.relative_path] = {
            'file_type': pf.file_type,
            'file_size_bytes': pf.file_size_bytes,
            'sha256_hash': pf.sha256_hash,
            'is_entry_point': pf.is_entry_point
        }
        path_to_file_record[pf.relative_path] = pf

    # 2. Run Static Analyzer
    analyzer = StaticAnalyzer(extracted_dir, files_map)
    raw_findings = analyzer.run_all_checks()

    # 3. Persist Findings
    summary_counts = {'critical': 0, 'warning': 0, 'info': 0, 'total': 0}
    findings_to_create = []

    for rf in raw_findings:
        sev = rf.get('severity', 'warning').lower()
        if sev in summary_counts:
            summary_counts[sev] += 1
        summary_counts['total'] += 1

        aff_file_rec = path_to_file_record.get(rf.get('affected_file_rel'))

        finding = Finding(
            analysis_run_id=analysis_run.id,
            affected_file_id=aff_file_rec.id if aff_file_rec else None,
            finding_code=rf.get('finding_code', 'CUSTOM_CHECK'),
            category=rf.get('category', 'performance'),
            severity=sev,
            title=rf.get('title', 'Static Finding'),
            explanation=rf.get('explanation', ''),
            line_number=rf.get('line_number'),
            evidence=rf.get('evidence', ''),
            recommended_action=rf.get('recommended_action', ''),
            confidence=rf.get('confidence', 'high'),
            estimated_impact=rf.get('estimated_impact', 'medium'),
            is_runtime_confirmed=False
        )
        findings_to_create.append(finding)

    db.session.add_all(findings_to_create)

    # 4. Extract and persist Dependency Graph
    mapper = DependencyMapper(extracted_dir, files_map)
    raw_edges = mapper.extract_dependencies()
    edges_to_create = []

    for re_edge in raw_edges:
        source_path = re_edge.get('source_path') or re_edge.get('source')
        target_path = re_edge.get('target_path') or re_edge.get('target')
        rel_type = re_edge.get('relationship_type') or re_edge.get('type', 'link')
        is_broken = re_edge.get('is_broken', False)
        evidence = re_edge.get('evidence', '')

        source_rec = path_to_file_record.get(source_path)
        target_rec = path_to_file_record.get(target_path)

        if source_rec:
            edge = DependencyEdge(
                version_id=version.id,
                source_file_id=source_rec.id,
                target_file_id=target_rec.id if target_rec else None,
                target_path_raw=target_path or '',
                relationship_type=rel_type,
                is_broken=is_broken,
                evidence=evidence
            )
            edges_to_create.append(edge)

    db.session.add_all(edges_to_create)

    # 5. Complete AnalysisRun
    duration_ms = int((time.time() - start_time) * 1000)
    analysis_run.status = 'completed'
    analysis_run.completed_at = datetime.now(timezone.utc)
    analysis_run.duration_ms = duration_ms
    analysis_run.summary_counts = summary_counts
    db.session.commit()

    # 6. Generate Recommendations automatically
    rec_engine = RecommendationEngine(version)
    rec_engine.generate_recommendations()

    flash(f"Static Analysis Complete in {duration_ms} ms! Found {summary_counts['total']} findings ({summary_counts['critical']} critical).", 'success')
    return redirect(url_for('analysis.findings', version_id=version.id))


@analysis_bp.route('/<int:version_id>/findings')
@login_required
def findings(version_id: int):
    """View static analysis findings with search and filters."""
    version = get_user_version_or_404(version_id)
    if not version.analysis or version.analysis.status != 'completed':
        flash("Static analysis has not yet been executed for this version.", 'warning')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    category_filter = request.args.get('category', '').lower()
    severity_filter = request.args.get('severity', '').lower()
    search_query = request.args.get('q', '').strip().lower()

    findings_query = Finding.query.filter_by(analysis_run_id=version.analysis.id)

    if category_filter:
        findings_query = findings_query.filter_by(category=category_filter)
    if severity_filter:
        findings_query = findings_query.filter_by(severity=severity_filter)

    all_findings = findings_query.all()

    if search_query:
        all_findings = [
            f for f in all_findings
            if search_query in f.title.lower() or search_query in f.explanation.lower() or (f.affected_file and search_query in f.affected_file.relative_path.lower())
        ]

    return render_template(
        'analysis/findings.html',
        title=f"Static Findings — {version.project.name} ({version.version_label})",
        version=version,
        analysis=version.analysis,
        findings=all_findings,
        category_filter=category_filter,
        severity_filter=severity_filter,
        search_query=search_query
    )


@analysis_bp.route('/<int:version_id>/graph')
@login_required
def graph(version_id: int):
    """Cytoscape.js interactive dependency graph view."""
    version = get_user_version_or_404(version_id)
    if not version.analysis or version.analysis.status != 'completed':
        flash("Please run static analysis first to extract dependency relationships.", 'warning')
        return redirect(url_for('projects.version_detail', project_id=version.project_id, version_id=version.id))

    return render_template(
        'analysis/graph.html',
        title=f"Dependency Graph — {version.project.name} ({version.version_label})",
        version=version
    )


@analysis_bp.route('/api/<int:version_id>/graph-data')
@login_required
def graph_data(version_id: int):
    """API endpoint providing Cytoscape.js formatted node and edge data."""
    version = get_user_version_or_404(version_id)
    nodes = []
    edges = []
    node_ids = set()

    # 1. Add File Nodes
    for pf in version.files:
        node_id = f"file_{pf.id}"
        node_ids.add(node_id)
        nodes.append({
            'data': {
                'id': node_id,
                'label': pf.relative_path.split('/')[-1],
                'full_path': pf.relative_path,
                'file_type': pf.file_type,
                'size_kb': pf.file_size_kb,
                'is_entry': pf.is_entry_point
            }
        })

    # 2. Add Dependency Edges
    for idx, de in enumerate(version.dependency_edges):
        source_id = f"file_{de.source_file_id}"
        target_id = f"file_{de.target_file_id}" if de.target_file_id else f"broken_{idx}"

        # If broken target node doesn't exist yet, add a virtual missing node
        if de.is_broken and target_id not in node_ids:
            node_ids.add(target_id)
            nodes.append({
                'data': {
                    'id': target_id,
                    'label': de.target_path_raw.split('/')[-1] or de.target_path_raw,
                    'full_path': de.target_path_raw,
                    'file_type': 'broken_missing',
                    'size_kb': 0,
                    'is_entry': False
                }
            })

        edges.append({
            'data': {
                'id': f"edge_{de.id}",
                'source': source_id,
                'target': target_id,
                'relationship': de.relationship_type,
                'is_broken': de.is_broken
            }
        })

    return jsonify({
        'elements': {
            'nodes': nodes,
            'edges': edges
        }
    })
