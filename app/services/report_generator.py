"""
Report Generator and Version Comparison Service for WebPulse.
Exports comprehensive standalone HTML, CSV, and JSON audit reports.
Computes before-and-after comparison between two project versions.
"""

from datetime import datetime, timezone
from app.models.project import ProjectVersion


class ReportGenerator:
    def __init__(self, version: ProjectVersion):
        self.version = version
        self.project = version.project

    def generate_json_export(self) -> dict:
        analysis = self.version.analysis
        latest_test = self.version.latest_test_run

        data = {
            'project_name': self.project.name,
            'project_id': str(self.project.id),
            'version_number': self.version.version_number,
            'version_label': self.version.version_label,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_files': self.version.total_files,
                'total_size_bytes': self.version.total_size_bytes,
                'entry_point': self.project.entry_point,
                'performance_score': latest_test.performance_score if latest_test else None,
            },
            'performance_metrics': {},
            'findings': [],
            'recommendations': [],
            'resources': []
        }

        if latest_test:
            data['performance_metrics'] = {
                'fcp_ms': latest_test.fcp_ms,
                'lcp_ms': latest_test.lcp_ms,
                'cls_score': latest_test.cls_score,
                'ttfb_ms': latest_test.ttfb_ms,
                'dom_content_loaded_ms': latest_test.dom_content_loaded_ms,
                'load_event_ms': latest_test.load_event_ms,
                'total_requests': latest_test.total_requests,
                'failed_requests': latest_test.failed_requests,
                'total_transferred_bytes': latest_test.total_transferred_bytes,
                'console_error_count': latest_test.console_error_count,
            }
            for res in latest_test.resources:
                data['resources'].append({
                    'name': res.resource_name,
                    'type': res.resource_type,
                    'status': res.status_code,
                    'duration_ms': res.duration_ms,
                    'transfer_size_bytes': res.transfer_size_bytes,
                    'is_failed': res.is_failed,
                })

        if analysis:
            for f in analysis.findings:
                data['findings'].append({
                    'code': f.finding_code,
                    'title': f.title,
                    'severity': f.severity,
                    'category': f.category,
                    'affected_file': f.affected_file.relative_path if f.affected_file else None,
                    'line_number': f.line_number,
                    'explanation': f.explanation,
                    'action': f.recommended_action,
                })

        for rec in self.version.recommendations:
            data['recommendations'].append({
                'title': rec.title,
                'priority': rec.priority,
                'score': rec.priority_score,
                'action_plan': rec.action_plan,
                'benefit': rec.potential_benefit,
                'resource': rec.affected_resource,
            })

        return data

    def generate_standalone_html_report(self) -> str:
        """Renders a self-contained, printable HTML report view with instant PDF print capabilities."""
        json_data = self.generate_json_export()
        p_name = json_data['project_name']
        v_label = json_data['version_label']
        score = json_data['summary']['performance_score']
        score_text = f"{score} / 100" if score is not None else "Not Benchmarked"
        metrics = json_data.get('performance_metrics', {})

        findings_rows = ""
        for f in json_data.get('findings', []):
            sev_color = '#ef4444' if f['severity'] == 'critical' else ('#f59e0b' if f['severity'] == 'warning' else '#38bdf8')
            findings_rows += f"""
            <tr>
                <td><span style="color:{sev_color}; font-weight:bold; text-transform:uppercase;">{f['severity']}</span></td>
                <td>{f['category']}</td>
                <td><strong>{f['title']}</strong><br><small style="color:#94a3b8;">{f['explanation']}</small></td>
                <td><code>{f['affected_file'] or 'Project Root'}</code> {f"line {f['line_number']}" if f['line_number'] else ''}</td>
                <td>{f['action']}</td>
            </tr>
            """

        recs_html = ""
        for rec in json_data.get('recommendations', []):
            badge_color = '#ef4444' if rec['priority'] == 'high' else ('#f59e0b' if rec['priority'] == 'medium' else '#38bdf8')
            recs_html += f"""
            <div class="recommendation-card" style="background:#131d31; border-left:4px solid {badge_color}; border-radius:6px; padding:14px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <strong style="color:#f8fafc; font-size:15px;">{rec['title']}</strong>
                    <span style="color:{badge_color}; font-size:12px; font-weight:bold; text-transform:uppercase;">Priority: {rec['priority']} ({rec['score']:.0f} pts)</span>
                </div>
                <div style="font-size:13px; color:#cbd5e1; white-space:pre-line; margin-bottom:8px;">{rec['action_plan']}</div>
                <div style="font-size:12px; color:#38bdf8;"><strong>Potential Gain:</strong> {rec['benefit']}</div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebPulse Performance Audit — {p_name} ({v_label})</title>
    <style>
        body {{
            background-color: #0b1120;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 30px 20px 60px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            border-bottom: 1px solid #1e293b;
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{ margin: 0 0 6px 0; font-size: 26px; color: #38bdf8; }}
        .score-box {{
            background: #1e293b;
            padding: 12px 24px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .score-val {{ font-size: 32px; font-weight: 800; color: #10b981; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 30px; }}
        .card {{ background: #131d31; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; }}
        .card-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }}
        .card-value {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: #131d31; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #1e293b; }}
        th {{ background: #1e293b; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
        code {{ background: #0b1120; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #38bdf8; }}

        /* Top Action Bar for PDF & Export */
        .print-toolbar {{
            background: #1e293b;
            border-bottom: 1px solid #334155;
            padding: 12px 24px;
            position: sticky;
            top: 0;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin: -30px -20px 24px -20px;
        }}
        .toolbar-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
            border: none;
        }}
        .btn-print {{ background: #0ea5e9; color: #ffffff; }}
        .btn-print:hover {{ background: #0284c7; color: #ffffff; }}
        .btn-json {{ background: #334155; color: #f1f5f9; }}
        .btn-json:hover {{ background: #475569; }}
        .btn-back {{ background: transparent; color: #94a3b8; }}
        .btn-back:hover {{ color: #ffffff; }}

        /* Professional Print & PDF Media Styling */
        @media print {{
            .no-print, .print-toolbar {{ display: none !important; }}
            body {{
                background-color: #ffffff !important;
                color: #0f172a !important;
                padding: 0 !important;
                font-size: 12pt !important;
            }}
            .container {{ max-width: 100% !important; margin: 0 !important; }}
            header {{
                border-bottom: 2px solid #0f172a !important;
                margin-bottom: 15px !important;
            }}
            h1 {{ color: #0f172a !important; font-size: 20pt !important; }}
            h2 {{ color: #0f172a !important; font-size: 14pt !important; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }}
            .score-box {{
                background: #f8fafc !important;
                border: 2px solid #0f172a !important;
                color: #0f172a !important;
            }}
            .score-val {{ color: #059669 !important; font-size: 24pt !important; }}
            .card {{
                background: #f8fafc !important;
                border: 1px solid #cbd5e1 !important;
                page-break-inside: avoid;
            }}
            .card-label {{ color: #64748b !important; }}
            .card-value {{ color: #0f172a !important; }}
            table {{
                background: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                page-break-inside: avoid;
            }}
            th {{
                background: #f1f5f9 !important;
                color: #334155 !important;
                border-bottom: 2px solid #cbd5e1 !important;
            }}
            td {{
                border-bottom: 1px solid #e2e8f0 !important;
                color: #1e293b !important;
            }}
            code {{
                background: #f1f5f9 !important;
                color: #0f172a !important;
                border: 1px solid #e2e8f0;
            }}
            .recommendation-card {{
                background: #f8fafc !important;
                border: 1px solid #cbd5e1 !important;
                color: #0f172a !important;
                page-break-inside: avoid;
            }}
            @page {{
                size: A4;
                margin: 15mm;
            }}
        }}
    </style>
</head>
<body>
    <!-- Interactive Toolbar (Hidden When Printed / Saved to PDF) -->
    <div class="print-toolbar no-print">
        <div style="display:flex; align-items:center; gap:16px;">
            <a href="/projects/{self.project.id}/versions/{self.version.id}" class="toolbar-btn btn-back">
                &larr; Back to Project Version
            </a>
            <span style="color:#64748b;">|</span>
            <span style="color:#cbd5e1; font-weight:500; font-size:14px;">WebPulse Formal Audit Dossier</span>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <a href="/reports/{self.version.id}/json" download="webpulse_audit_{self.project.id}_v{self.version.version_number}.json" class="toolbar-btn btn-json">
                Download JSON Data
            </a>
            <button onclick="window.print()" class="toolbar-btn btn-print">
                Print / Save as PDF
            </button>
        </div>
    </div>

    <div class="container">
        <header>
            <div>
                <h1>WebPulse Audit Report</h1>
                <div style="color: #94a3b8; font-size: 14px;">
                    <strong>Project:</strong> {p_name} &bull; 
                    <strong>Version:</strong> {v_label} &bull; 
                    <strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}
                </div>
            </div>
            <div class="score-box">
                <div class="score-val">{score if score is not None else '—'}</div>
                <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase;">WebPulse Score</div>
            </div>
        </header>

        <section>
            <h2>Performance & Core Web Vitals Summary</h2>
            <div class="cards">
                <div class="card">
                    <div class="card-label">First Contentful (FCP)</div>
                    <div class="card-value">{f"{metrics['fcp_ms']:.0f} ms" if metrics.get('fcp_ms') else 'N/A'}</div>
                </div>
                <div class="card">
                    <div class="card-label">Largest Contentful (LCP)</div>
                    <div class="card-value">{f"{metrics['lcp_ms']:.0f} ms" if metrics.get('lcp_ms') else 'N/A'}</div>
                </div>
                <div class="card">
                    <div class="card-label">Layout Shift (CLS)</div>
                    <div class="card-value">{f"{metrics['cls_score']:.3f}" if metrics.get('cls_score') is not None else 'N/A'}</div>
                </div>
                <div class="card">
                    <div class="card-label">Load Event Time</div>
                    <div class="card-value">{f"{metrics['load_event_ms']:.0f} ms" if metrics.get('load_event_ms') else 'N/A'}</div>
                </div>
                <div class="card">
                    <div class="card-label">Total Requests</div>
                    <div class="card-value">{metrics.get('total_requests', 'N/A')}</div>
                </div>
                <div class="card">
                    <div class="card-label">Transferred Size</div>
                    <div class="card-value">{f"{metrics['total_transferred_bytes']/1024:.1f} KB" if metrics.get('total_transferred_bytes') else 'N/A'}</div>
                </div>
            </div>
        </section>

        <section>
            <h2>Prioritized Optimization Recommendations</h2>
            {recs_html or '<p style="color:#94a3b8;">No recommendations generated. Run static analysis first to extract recommendations.</p>'}
        </section>

        <section style="margin-top: 30px;">
            <h2>Static Analysis Findings ({len(json_data.get('findings', []))})</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 100px;">Severity</th>
                        <th style="width: 120px;">Category</th>
                        <th>Issue</th>
                        <th style="width: 180px;">Affected File</th>
                        <th>Action Required</th>
                    </tr>
                </thead>
                <tbody>
                    {findings_rows or '<tr><td colspan="5" style="text-align:center; color:#94a3b8; padding: 24px;">No static issues discovered! Excellent work.</td></tr>'}
                </tbody>
            </table>
        </section>

        <footer style="margin-top: 40px; text-align: center; color: #64748b; font-size: 13px; border-top: 1px solid #1e293b; padding-top: 20px;">
            Generated automatically by WebPulse — Website Performance Analyzer & Optimization Lab.
        </footer>
    </div>

    <script>
        // Auto-trigger print dialog if requested in query parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('print') === '1' || urlParams.get('pdf') === '1') {{
            window.addEventListener('load', () => {{
                setTimeout(() => window.print(), 350);
            }});
        }}
    </script>
</body>
</html>"""
        return html


class VersionComparator:
    """
    Compares two ProjectVersions (Base vs Target / Before vs After)
    to calculate delta improvements, resolved/new findings, and metrics changes.
    Guarantees graceful, safe fallback if either version has not completed audits.
    """
    def __init__(self, v_before: ProjectVersion, v_after: ProjectVersion):
        self.v_before = v_before
        self.v_after = v_after

    def compare(self) -> dict:
        size_before = self.v_before.total_size_bytes or 0
        size_after = self.v_after.total_size_bytes or 0
        size_diff = size_after - size_before

        files_before = self.v_before.total_files or 0
        files_after = self.v_after.total_files or 0
        files_diff = files_after - files_before

        # Analysis status
        has_analysis_before = bool(self.v_before.analysis and self.v_before.analysis.status == 'completed')
        has_analysis_after = bool(self.v_after.analysis and self.v_after.analysis.status == 'completed')
        has_both_analysis = has_analysis_before and has_analysis_after

        findings_before = {f.finding_code: f for f in self.v_before.analysis.findings} if has_analysis_before else {}
        findings_after = {f.finding_code: f for f in self.v_after.analysis.findings} if has_analysis_after else {}

        resolved_codes = set(findings_before.keys()) - set(findings_after.keys())
        new_codes = set(findings_after.keys()) - set(findings_before.keys())
        persistent_codes = set(findings_before.keys()) & set(findings_after.keys())

        resolved_findings = [findings_before[c] for c in resolved_codes]
        new_findings = [findings_after[c] for c in new_codes]
        persistent_findings = [findings_after[c] for c in persistent_codes]

        # Performance test status
        t_before = self.v_before.latest_test_run
        t_after = self.v_after.latest_test_run

        has_performance_before = bool(t_before and t_before.status == 'completed')
        has_performance_after = bool(t_after and t_after.status == 'completed')
        has_both_performance = has_performance_before and has_performance_after

        # Pre-initialize all metric keys with None so Jinja templates never hit UndefinedError
        metrics_diff = {
            'score_before': None,
            'score_after': None,
            'score_delta': None,
            'fcp_before': None,
            'fcp_after': None,
            'fcp_delta': None,
            'lcp_before': None,
            'lcp_after': None,
            'lcp_delta': None,
            'cls_before': None,
            'cls_after': None,
            'cls_delta': None,
            'load_before': None,
            'load_after': None,
            'load_delta': None,
            'requests_before': None,
            'requests_after': None,
            'requests_delta': None,
            'bytes_before': None,
            'bytes_after': None,
            'bytes_delta': None,
        }

        if has_both_performance:
            def delta(a, b):
                if a is not None and b is not None:
                    return round(b - a, 2)
                return None

            metrics_diff = {
                'score_before': t_before.performance_score,
                'score_after': t_after.performance_score,
                'score_delta': delta(t_before.performance_score, t_after.performance_score),

                'fcp_before': t_before.fcp_ms,
                'fcp_after': t_after.fcp_ms,
                'fcp_delta': delta(t_before.fcp_ms, t_after.fcp_ms),

                'lcp_before': t_before.lcp_ms,
                'lcp_after': t_after.lcp_ms,
                'lcp_delta': delta(t_before.lcp_ms, t_after.lcp_ms),

                'cls_before': t_before.cls_score,
                'cls_after': t_after.cls_score,
                'cls_delta': delta(t_before.cls_score, t_after.cls_score),

                'load_before': t_before.load_event_ms,
                'load_after': t_after.load_event_ms,
                'load_delta': delta(t_before.load_event_ms, t_after.load_event_ms),

                'requests_before': t_before.total_requests,
                'requests_after': t_after.total_requests,
                'requests_delta': (t_after.total_requests or 0) - (t_before.total_requests or 0),

                'bytes_before': t_before.total_transferred_bytes,
                'bytes_after': t_after.total_transferred_bytes,
                'bytes_delta': (t_after.total_transferred_bytes or 0) - (t_before.total_transferred_bytes or 0),
            }

        return {
            'version_before': self.v_before,
            'version_after': self.v_after,
            'has_analysis_before': has_analysis_before,
            'has_analysis_after': has_analysis_after,
            'has_both_analysis': has_both_analysis,
            'has_performance_before': has_performance_before,
            'has_performance_after': has_performance_after,
            'has_both_performance': has_both_performance,
            'size_diff_bytes': size_diff,
            'files_diff': files_diff,
            'resolved_findings': resolved_findings,
            'new_findings': new_findings,
            'persistent_findings': persistent_findings,
            'resolved_count': len(resolved_findings),
            'new_count': len(new_findings),
            'persistent_count': len(persistent_findings),
            'metrics_diff': metrics_diff,
        }
