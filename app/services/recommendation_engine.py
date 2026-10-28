"""
Deterministic Recommendation Engine for WebPulse.
Generates prioritized, actionable optimization advice directly linked to
detected findings and runtime performance metrics.
"""

from app.extensions import db
from app.models.project import ProjectVersion
from app.models.analysis import Finding
from app.models.recommendation import Recommendation

SEVERITY_POINTS = {
    'critical': 40.0,
    'warning': 20.0,
    'info': 10.0,
}

IMPACT_POINTS = {
    'high': 30.0,
    'medium': 15.0,
    'low': 5.0,
}

CONFIDENCE_POINTS = {
    'high': 20.0,
    'medium': 10.0,
    'low': 5.0,
}


class RecommendationEngine:
    def __init__(self, version: ProjectVersion):
        self.version = version

    def generate_recommendations(self) -> list:
        """
        Clears older recommendations for this version and deterministically generates
        scored recommendations from findings and performance metrics.
        """
        Recommendation.query.filter_by(version_id=self.version.id).delete()

        if not self.version.analysis:
            db.session.commit()
            return []

        findings = self.version.analysis.findings
        recommendations_to_create = []

        for finding in findings:
            rule_id = finding.finding_code
            severity = finding.severity
            impact = finding.estimated_impact
            confidence = finding.confidence

            base_score = (
                SEVERITY_POINTS.get(severity, 15.0) +
                IMPACT_POINTS.get(impact, 10.0) +
                CONFIDENCE_POINTS.get(confidence, 10.0)
            )

            magnitude_bonus = 0.0
            if 'CRITICAL' in rule_id or 'OVERSIZED' in rule_id:
                magnitude_bonus = 10.0
            elif 'BROKEN' in rule_id:
                magnitude_bonus = 8.0

            priority_score = min(100.0, base_score + magnitude_bonus)

            if priority_score >= 70:
                priority_label = 'high'
            elif priority_score >= 45:
                priority_label = 'medium'
            else:
                priority_label = 'low'

            title, action_plan, benefit = self._get_rule_action_plan(finding)
            affected_res = finding.affected_file.relative_path if finding.affected_file else "Project Root / Configuration"

            rec = Recommendation(
                version_id=self.version.id,
                finding_id=finding.id,
                rule_id=rule_id,
                priority=priority_label,
                priority_score=priority_score,
                title=title,
                action_plan=action_plan,
                potential_benefit=benefit,
                affected_resource=affected_res,
                is_verified_fixed=False
            )
            recommendations_to_create.append(rec)

        db.session.add_all(recommendations_to_create)
        db.session.commit()

        return Recommendation.query.filter_by(version_id=self.version.id).order_by(Recommendation.priority_score.desc()).all()

    def _get_rule_action_plan(self, finding: Finding) -> tuple:
        code = finding.finding_code

        if 'IMG_OVERSIZED' in code:
            title = f"Optimize Image Payload: {finding.affected_file.relative_path if finding.affected_file else 'Image'}"
            action_plan = (
                "1. Resize source bitmap to the actual rendered container dimensions.\n"
                "2. Convert uncompressed PNG/JPEG to modern WebP format with 80-85% quality.\n"
                "3. Use responsive <picture> or srcset for mobile vs desktop displays."
            )
            benefit = "Reduces page weight by 40-75%, drastically speeding up LCP and mobile downloads."
        elif code == 'IMG_MISSING_DIMENSIONS':
            title = "Reserve Image Aspect Ratio to Prevent Layout Shifts"
            action_plan = (
                "1. Add explicit width and height HTML attributes (e.g., width='800' height='600') to <img> tags.\n"
                "2. Alternatively, specify 'aspect-ratio' in your CSS rule for the image class."
            )
            benefit = "Prevents layout jumps during page rendering, achieving a near-zero Cumulative Layout Shift (CLS)."
        elif code == 'JS_BLOCKING_SCRIPT':
            title = "Eliminate Parser-Blocking Scripts in Head"
            action_plan = (
                "1. Add the 'defer' attribute to <script src='...'> tags in <head> so parsing continues unhindered.\n"
                "2. For completely standalone analytics or tracker scripts, use 'async' instead."
            )
            benefit = "Lowers First Contentful Paint (FCP) and Time to Interactive by allowing HTML parsing to finish uninterrupted."
        elif 'BROKEN_LOCAL_REF' in code or 'CSS_BROKEN_ASSET_REF' in code:
            title = f"Resolve Broken Local Asset: {finding.affected_file.relative_path if finding.affected_file else 'Resource'}"
            action_plan = (
                "1. Verify that the requested file exists in the project directory.\n"
                "2. Confirm case sensitivity (e.g. 'Hero.jpg' vs 'hero.jpg').\n"
                "3. Check relative path depth (e.g. '../images/' vs 'images/')."
            )
            benefit = "Eliminates 404 HTTP errors, missing visuals, broken layout styling, and console errors."
        elif code == 'CSS_OVERSIZED':
            title = "Minify and Optimize Stylesheet Payload"
            action_plan = (
                "1. Strip comments, whitespace, and duplicate selectors with a CSS minifier.\n"
                "2. Remove unused utility classes and inline critical styles above the fold."
            )
            benefit = "Accelerates DOM rendering and avoids blocking browser render tree construction."
        elif code == 'HTML_MISSING_VIEWPORT':
            title = "Configure Mobile Viewport Meta Tag"
            action_plan = (
                "Insert <meta name='viewport' content='width=device-width, initial-scale=1.0'> "
                "within the <head> of all HTML pages."
            )
            benefit = "Ensures correct responsive scaling and legible touch target rendering on mobile viewports."
        elif code == 'DUPLICATE_ASSET_HASH':
            title = "Deduplicate Redundant Project Assets"
            action_plan = (
                "1. Remove redundant asset files sharing identical SHA-256 hashes.\n"
                "2. Update referencing files to point to a single canonical file in an assets directory."
            )
            benefit = "Saves bandwidth, decreases build payload size, and optimizes browser cache hit rates."
        else:
            title = finding.title
            action_plan = finding.recommended_action or "Review and address the affected code lines."
            benefit = "Improves overall code hygiene, accessibility standards, and web performance."

        return title, action_plan, benefit
