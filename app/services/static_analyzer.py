"""
Static Source Analysis Engine for WebPulse.
Performs deep inspection of HTML, CSS, JavaScript, and asset files.
Identifies performance, accessibility, SEO, and best-practice findings.
"""

import os
import re
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

class FindingCollector:
    def __init__(self):
        self.findings = []

    def add(self, finding_code, category, severity, title, explanation,
            affected_file_rel, line_number=None, evidence="",
            recommended_action="", confidence="high", estimated_impact="medium"):
        self.findings.append({
            'finding_code': finding_code,
            'category': category,
            'severity': severity,
            'title': title,
            'explanation': explanation,
            'affected_file_rel': affected_file_rel,
            'line_number': line_number,
            'evidence': evidence,
            'recommended_action': recommended_action,
            'confidence': confidence,
            'estimated_impact': estimated_impact,
        })

class StaticAnalyzer:
    def __init__(self, root_dir: Path, files_map: dict):
        """
        root_dir: Path to extracted project root
        files_map: dict mapping relative_path -> ProjectFile model or metadata dict
        """
        self.root_dir = Path(root_dir)
        self.files_map = files_map
        self.collector = FindingCollector()
        self.existing_rel_paths = set(files_map.keys())
        self.hash_to_files = {}

    def run_all_checks(self) -> list:
        # 1. Asset & Image Analysis (including duplicate detection via SHA256)
        self._analyze_assets()

        # 2. Inspect each file based on its type
        for rel_path, file_data in self.files_map.items():
            full_path = self.root_dir / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue

            file_type = file_data.get('file_type', '')
            ext = full_path.suffix.lower()
            if not file_type or file_type == 'other':
                if ext in ('.html', '.htm'):
                    file_type = 'html'
                elif ext == '.css':
                    file_type = 'css'
                elif ext in ('.js', '.mjs', '.cjs'):
                    file_type = 'javascript'
                elif ext in ('.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif'):
                    file_type = 'image'
                elif ext == '.svg':
                    file_type = 'svg'

            if file_type == 'html':
                self._analyze_html(rel_path, full_path)
            elif file_type == 'css':
                self._analyze_css(rel_path, full_path)
            elif file_type == 'javascript':
                self._analyze_javascript(rel_path, full_path)

        return self.collector.findings

    # -------------------------------------------------------------
    # 1. Asset & Image Analysis
    # -------------------------------------------------------------
    def _analyze_assets(self):
        for rel_path, file_data in self.files_map.items():
            full_path = self.root_dir / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue

            file_type = file_data.get('file_type', '')
            ext = full_path.suffix.lower()
            if not file_type or file_type == 'other':
                if ext in ('.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif'):
                    file_type = 'image'
                elif ext == '.svg':
                    file_type = 'svg'

            size = file_data.get('file_size_bytes') or file_data.get('size_bytes') or full_path.stat().st_size
            sha = file_data.get('sha256_hash', '')

            # Track duplicates
            if sha:
                self.hash_to_files.setdefault(sha, []).append(rel_path)

            # Image checks
            if file_type == 'image':
                ext = full_path.suffix.lower()
                # A. Large image file size
                if size > 1024 * 1024: # > 1MB
                    self.collector.add(
                        finding_code='IMG_OVERSIZED_CRITICAL',
                        category='performance',
                        severity='critical',
                        title=f"Oversized Image File ({size / (1024*1024):.2f} MB)",
                        explanation="Heavy image assets significantly increase page load times and data consumption on mobile devices.",
                        affected_file_rel=rel_path,
                        evidence=f"File '{rel_path}' is {size / (1024*1024):.2f} MB.",
                        recommended_action="Compress the image, resize to target display resolution, or convert to WebP / AVIF format.",
                        confidence='high',
                        estimated_impact='high'
                    )
                elif size > 400 * 1024: # > 400KB
                    self.collector.add(
                        finding_code='IMG_OVERSIZED_WARNING',
                        category='performance',
                        severity='warning',
                        title=f"Uncompressed Image File ({size / 1024:.1f} KB)",
                        explanation="Image asset exceeds recommended web budget of 400 KB.",
                        affected_file_rel=rel_path,
                        evidence=f"File '{rel_path}' is {size / 1024:.1f} KB.",
                        recommended_action="Run image through an optimization pipeline to compress without perceptual quality loss.",
                        confidence='high',
                        estimated_impact='medium'
                    )

                # B. Inspect image dimensions and transparency
                try:
                    with Image.open(full_path) as img:
                        w, h = img.size
                        has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
                        
                        # High resolution alert
                        if w > 2400 or h > 2400:
                            self.collector.add(
                                finding_code='IMG_EXCESSIVE_DIMENSIONS',
                                category='performance',
                                severity='warning',
                                title=f"Excessive Image Dimensions ({w}x{h} px)",
                                explanation="Serving images with excessive pixel dimensions forces the browser to decode and scale down high-density bitmaps in memory.",
                                affected_file_rel=rel_path,
                                evidence=f"Resolution is {w}x{h} pixels.",
                                recommended_action=f"Scale down image to maximum intended display dimension (e.g., max 1920px for hero images, or 800px for content).",
                                confidence='high',
                                estimated_impact='medium'
                            )

                        # Modern format recommendation
                        if ext in ('.jpg', '.jpeg', '.png') and size > 150 * 1024:
                            rec_format = "WebP (with alpha channel support)" if has_alpha else "WebP or AVIF"
                            self.collector.add(
                                finding_code='IMG_MODERN_FORMAT',
                                category='performance',
                                severity='info',
                                title=f"Legacy Image Format ({ext.upper()})",
                                explanation=f"Using legacy formats ({ext}) instead of next-generation formats misses potential 25-50% file size savings.",
                                affected_file_rel=rel_path,
                                evidence=f"Format is {ext.upper()} with size {size/1024:.1f} KB. Alpha transparency: {has_alpha}.",
                                recommended_action=f"Convert to modern {rec_format} format while verifying alpha preservation.",
                                confidence='medium',
                                estimated_impact='medium'
                            )
                except Exception:
                    # Not a valid image or unsupported format
                    pass

            # SVG checks
            elif file_type == 'svg' and size > 80 * 1024:
                self.collector.add(
                    finding_code='SVG_OVERSIZED',
                    category='performance',
                    severity='info',
                    title=f"Oversized Vector Graphic ({size / 1024:.1f} KB)",
                    explanation="SVG file contains extensive embedded paths, metadata, or unoptimized vector nodes.",
                    affected_file_rel=rel_path,
                    evidence=f"SVG file size is {size / 1024:.1f} KB.",
                    recommended_action="Clean SVG using an optimizer like SVGO to strip editor metadata and round coordinates.",
                    confidence='high',
                    estimated_impact='low'
                )

        # C. Duplicate file check across all assets
        for sha, paths in self.hash_to_files.items():
            if len(paths) > 1:
                first = paths[0]
                others = ", ".join(paths[1:])
                self.collector.add(
                    finding_code='DUPLICATE_ASSET_HASH',
                    category='best_practices',
                    severity='warning',
                    title=f"Identical Duplicate Files Detected ({len(paths)} copies)",
                    explanation="Multiple files have identical cryptographic hashes, causing redundant downloads and wasted storage.",
                    affected_file_rel=first,
                    evidence=f"Identical content exists in: {others}",
                    recommended_action="Consolidate duplicate files into a single shared resource and update references.",
                    confidence='high',
                    estimated_impact='medium'
                )

    # -------------------------------------------------------------
    # 2. HTML Analysis
    # -------------------------------------------------------------
    def _analyze_html(self, rel_path: str, full_path: Path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        soup = BeautifulSoup(content, 'html.parser')

        # A. Page Title Check
        title_tag = soup.find('title')
        if not title_tag or not title_tag.string or not title_tag.string.strip():
            self.collector.add(
                finding_code='HTML_MISSING_TITLE',
                category='seo',
                severity='warning',
                title="Missing or Empty Page Title",
                explanation="The <title> element is critical for search engine results, browser tabs, and accessibility bookmarks.",
                affected_file_rel=rel_path,
                evidence="<title> tag is absent or blank.",
                recommended_action="Add a descriptive, concise <title> inside the <head> element.",
                confidence='high',
                estimated_impact='medium'
            )

        # B. Viewport Meta Check
        viewport_meta = soup.find('meta', attrs={'name': re.compile(r'^viewport$', re.I)})
        if not viewport_meta or not viewport_meta.get('content'):
            self.collector.add(
                finding_code='HTML_MISSING_VIEWPORT',
                category='best_practices',
                severity='critical',
                title="Missing Mobile Viewport Meta Tag",
                explanation="Without a viewport meta tag, mobile browsers render pages at desktop width (typically 980px) and scale down, breaking responsiveness.",
                affected_file_rel=rel_path,
                evidence="No <meta name='viewport' content='width=device-width, initial-scale=1.0'> found.",
                recommended_action="Add <meta name='viewport' content='width=device-width, initial-scale=1.0'> in <head>.",
                confidence='high',
                estimated_impact='high'
            )

        # C. Image Tags Inspection (Alt attributes & explicit dimensions)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt')
            width = img.get('width')
            height = img.get('height')

            # Missing Alt
            if alt is None:
                self.collector.add(
                    finding_code='IMG_MISSING_ALT',
                    category='accessibility',
                    severity='warning',
                    title="Image Missing Accessible Alt Attribute",
                    explanation="Screen readers and assistive technologies require the alt attribute to convey image context to visually impaired users.",
                    affected_file_rel=rel_path,
                    evidence=f"Tag: {str(img)[:120]}...",
                    recommended_action=f"Add descriptive alt='...' text or alt='' if purely decorative for image '{src}'.",
                    confidence='high',
                    estimated_impact='medium'
                )

            # Missing Dimensions (CLS risk)
            if not width or not height:
                self.collector.add(
                    finding_code='IMG_MISSING_DIMENSIONS',
                    category='performance',
                    severity='warning',
                    title="Image Missing Explicit Dimensions (CLS Risk)",
                    explanation="Images without explicit width and height attributes cause layout shifts while loading, degrading Cumulative Layout Shift (CLS).",
                    affected_file_rel=rel_path,
                    evidence=f"Tag: {str(img)[:120]}...",
                    recommended_action="Specify explicit width and height attributes or CSS aspect-ratio to reserve space before the image loads.",
                    confidence='high',
                    estimated_impact='high'
                )

            # Local resource resolution check
            if src and not src.startswith(('http://', 'https://', 'data:', '//', '#', 'mailto:')):
                resolved = self._resolve_local_ref(rel_path, src)
                if not resolved:
                    self.collector.add(
                        finding_code='BROKEN_LOCAL_REF_IMG',
                        category='best_practices',
                        severity='critical',
                        title=f"Broken Local Image Reference: '{src}'",
                        explanation="The HTML document references a local image file that does not exist in the project files.",
                        affected_file_rel=rel_path,
                        evidence=f"Image src='{src}' could not be resolved from '{rel_path}'.",
                        recommended_action="Ensure the referenced image is included in the project and the file path/casing matches exactly.",
                        confidence='high',
                        estimated_impact='high'
                    )

        # D. Script Inspection (Render-blocking in <head>)
        head_tag = soup.find('head')
        seen_scripts = set()
        if head_tag:
            for script in head_tag.find_all('script'):
                src = script.get('src')
                if src:
                    # Check duplicate scripts
                    if src in seen_scripts:
                        self.collector.add(
                            finding_code='DUPLICATE_RESOURCE_SCRIPT',
                            category='performance',
                            severity='warning',
                            title=f"Duplicate Script Included: '{src}'",
                            explanation="The exact same script file is included multiple times in the document.",
                            affected_file_rel=rel_path,
                            evidence=f"Script src='{src}' loaded repeatedly.",
                            recommended_action="Remove duplicate <script> tag to eliminate redundant network requests.",
                            confidence='high',
                            estimated_impact='medium'
                        )
                    seen_scripts.add(src)

                    # Check blocking script (no async, no defer, not type=module)
                    is_async = script.has_attr('async')
                    is_defer = script.has_attr('defer')
                    is_module = script.get('type') == 'module'
                    if not (is_async or is_defer or is_module):
                        self.collector.add(
                            finding_code='JS_BLOCKING_SCRIPT',
                            category='performance',
                            severity='warning',
                            title=f"Render-Blocking Script in <head>: '{src}'",
                            explanation="Synchronous scripts in the document <head> pause the HTML parser until downloaded and executed, delaying First Contentful Paint.",
                            affected_file_rel=rel_path,
                            evidence=f"<script src='{src}'> lacks 'defer' or 'async'.",
                            recommended_action="Add 'defer' attribute to execute after HTML parsing, or 'async' if independent.",
                            confidence='high',
                            estimated_impact='high'
                        )

                    # Broken script reference
                    if not src.startswith(('http://', 'https://', '//')):
                        if not self._resolve_local_ref(rel_path, src):
                            self.collector.add(
                                finding_code='BROKEN_LOCAL_REF_SCRIPT',
                                category='best_practices',
                                severity='critical',
                                title=f"Broken Local Script Reference: '{src}'",
                                explanation="The HTML document references a local script that does not exist in the project.",
                                affected_file_rel=rel_path,
                                evidence=f"Script src='{src}' not found.",
                                recommended_action="Verify script filename, case-sensitivity, and relative path.",
                                confidence='high',
                                estimated_impact='high'
                            )

        # E. Stylesheet Links
        seen_css = set()
        for link in soup.find_all('link', rel=lambda r: r and 'stylesheet' in r):
            href = link.get('href', '')
            if href:
                if href in seen_css:
                    self.collector.add(
                        finding_code='DUPLICATE_RESOURCE_CSS',
                        category='performance',
                        severity='warning',
                        title=f"Duplicate Stylesheet Included: '{href}'",
                        explanation="The exact same stylesheet is linked multiple times.",
                        affected_file_rel=rel_path,
                        evidence=f"Stylesheet href='{href}' referenced multiple times.",
                        recommended_action="Remove duplicate stylesheet link.",
                        confidence='high',
                        estimated_impact='medium'
                    )
                seen_css.add(href)

                if not href.startswith(('http://', 'https://', '//', 'data:')):
                    if not self._resolve_local_ref(rel_path, href):
                        self.collector.add(
                            finding_code='BROKEN_LOCAL_REF_CSS',
                            category='best_practices',
                            severity='critical',
                            title=f"Broken Local Stylesheet: '{href}'",
                            explanation="A linked CSS stylesheet could not be found in the project directory.",
                            affected_file_rel=rel_path,
                            evidence=f"CSS link href='{href}' unresolved.",
                            recommended_action="Verify CSS filename, casing, and relative folder hierarchy.",
                            confidence='high',
                            estimated_impact='high'
                        )

        # F. Large embedded Data URLs in HTML
        data_urls = re.findall(r'src=["\'](data:[^"\']{2000,})["\']', content)
        if data_urls:
            self.collector.add(
                finding_code='EMBEDDED_DATA_URL_OVERSIZED',
                category='performance',
                severity='warning',
                title=f"Oversized Embedded Data URL in HTML ({len(data_urls)} instances)",
                explanation="Inlining large base64 resources inside HTML bloats the initial document transfer size and prevents parallel browser caching.",
                affected_file_rel=rel_path,
                evidence=f"Found {len(data_urls)} embedded data URI(s) exceeding 2KB each.",
                recommended_action="Extract embedded base64 data URLs into external asset files so the browser can cache them separately.",
                confidence='high',
                estimated_impact='medium'
            )

    # -------------------------------------------------------------
    # 3. CSS Analysis
    # -------------------------------------------------------------
    def _analyze_css(self, rel_path: str, full_path: Path):
        size = full_path.stat().st_size
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        # A. Large Stylesheet
        if size > 150 * 1024:
            self.collector.add(
                finding_code='CSS_OVERSIZED',
                category='performance',
                severity='warning',
                title=f"Large Stylesheet File ({size / 1024:.1f} KB)",
                explanation="Large CSS files delay First Contentful Paint because CSS is render-blocking by default.",
                affected_file_rel=rel_path,
                evidence=f"File size is {size / 1024:.1f} KB.",
                recommended_action="Minify stylesheet, purge unused selectors, and consider splitting critical CSS from non-critical rules.",
                confidence='high',
                estimated_impact='medium'
            )

        # B. CSS @import statements
        import_matches = re.findall(r'@import\s+["\']([^"\']+)["\'];?', content)
        if import_matches:
            self.collector.add(
                finding_code='CSS_IMPORT_FOUND',
                category='performance',
                severity='warning',
                title=f"CSS @import Rules Detected ({len(import_matches)} imports)",
                explanation="Using @import inside CSS creates serial request waterfalls because the browser must parse the parent CSS before discovering the imported file.",
                affected_file_rel=rel_path,
                evidence=f"Found @import: {', '.join(import_matches[:3])}",
                recommended_action="Replace @import rules with standard <link rel='stylesheet'> tags in HTML or bundle stylesheets together.",
                confidence='high',
                estimated_impact='high'
            )

        # C. Broken url(...) assets in CSS
        url_matches = re.findall(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', content)
        broken_urls = []
        for url in url_matches:
            clean_url = url.split('#')[0].split('?')[0].strip()
            if clean_url and not clean_url.startswith(('http://', 'https://', 'data:', '//')):
                if not self._resolve_local_ref(rel_path, clean_url):
                    broken_urls.append(clean_url)

        if broken_urls:
            unique_broken = list(set(broken_urls))[:5]
            self.collector.add(
                finding_code='CSS_BROKEN_ASSET_REF',
                category='best_practices',
                severity='critical',
                title=f"Broken Local Asset References in CSS ({len(broken_urls)} broken)",
                explanation="Stylesheets reference background images or fonts that do not exist relative to the CSS file location.",
                affected_file_rel=rel_path,
                evidence=f"Unresolved URLs: {', '.join(unique_broken)}",
                recommended_action="Check relative paths in url(...) statements. Remember paths are relative to the CSS file's directory.",
                confidence='high',
                estimated_impact='high'
            )

        # D. Duplicate rules / declarations check (heuristic check for identical repeated selector blocks)
        selectors = re.findall(r'([^{]+)\s*\{([^}]+)\}', content)
        seen_selectors = {}
        duplicates = []
        for sel, body in selectors:
            sel_clean = sel.strip()
            if len(sel_clean) > 2 and not sel_clean.startswith('@'):
                if sel_clean in seen_selectors:
                    duplicates.append(sel_clean)
                else:
                    seen_selectors[sel_clean] = True

        if len(duplicates) > 3:
            self.collector.add(
                finding_code='CSS_DUPLICATE_DECLARATION',
                category='best_practices',
                severity='info',
                title=f"Duplicate CSS Selector Blocks ({len(duplicates)} repeated)",
                explanation="The stylesheet repeats the same CSS selector block multiple times, increasing file size and specificity conflicts.",
                affected_file_rel=rel_path,
                evidence=f"Repeated selectors: {', '.join(duplicates[:4])}",
                recommended_action="Consolidate duplicate selector declarations into unified rule blocks.",
                confidence='medium',
                estimated_impact='low'
            )

    # -------------------------------------------------------------
    # 4. JavaScript Analysis
    # -------------------------------------------------------------
    def _analyze_javascript(self, rel_path: str, full_path: Path):
        size = full_path.stat().st_size
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        # A. Large JS bundle
        if size > 300 * 1024:
            self.collector.add(
                finding_code='JS_OVERSIZED',
                category='performance',
                severity='warning',
                title=f"Large JavaScript File ({size / 1024:.1f} KB)",
                explanation="JavaScript files over 300 KB demand substantial parsing and compilation overhead on mobile CPUs.",
                affected_file_rel=rel_path,
                evidence=f"File size is {size / 1024:.1f} KB.",
                recommended_action="Minify code, remove unused libraries, and implement code splitting or dynamic import().",
                confidence='high',
                estimated_impact='high'
            )

        # B. Dev artifacts (console.log / debugger)
        debugger_count = len(re.findall(r'\bdebugger\b', content))
        console_log_count = len(re.findall(r'\bconsole\.log\(', content))
        if debugger_count > 0 or console_log_count > 10:
            evidence = []
            if debugger_count: evidence.append(f"{debugger_count} 'debugger' statement(s)")
            if console_log_count: evidence.append(f"{console_log_count} 'console.log' call(s)")
            self.collector.add(
                finding_code='JS_DEV_ARTIFACTS',
                category='best_practices',
                severity='info',
                title="Development Artifacts Detected in JavaScript",
                explanation="Production JavaScript should not contain active debugger statements or excessive console logging.",
                affected_file_rel=rel_path,
                evidence=", ".join(evidence),
                recommended_action="Strip debuggers and console logs during the build or minification step.",
                confidence='high',
                estimated_impact='low'
            )

        # C. Unresolved ES Module Imports
        import_statements = re.findall(r'import\s+(?:[\w*\s{},]+from\s+)?[\'"](\./[^\'"]+|\.\./[^\'"]+)[\'"]', content)
        broken_imports = []
        for imp in import_statements:
            if not self._resolve_local_ref(rel_path, imp):
                # Try appending .js if missing
                if not self._resolve_local_ref(rel_path, imp + '.js'):
                    broken_imports.append(imp)

        if broken_imports:
            self.collector.add(
                finding_code='JS_UNRESOLVED_IMPORT',
                category='best_practices',
                severity='critical',
                title=f"Unresolved ES Module Imports ({len(broken_imports)} broken)",
                explanation="JavaScript file attempts to import relative modules that do not exist on disk.",
                affected_file_rel=rel_path,
                evidence=f"Unresolved import(s): {', '.join(broken_imports[:3])}",
                recommended_action="Check module export names, file paths, and ensure target files are included.",
                confidence='high',
                estimated_impact='high'
            )

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------
    def _resolve_local_ref(self, current_file_rel: str, target_ref: str) -> bool:
        """
        Safely resolves a relative path reference against the existing file set.
        """
        clean_target = target_ref.split('?')[0].split('#')[0].strip()
        if not clean_target:
            return True

        if clean_target.startswith('/'):
            # Root-relative path
            test_path = clean_target.lstrip('/')
        else:
            # File-relative path
            parent = os.path.dirname(current_file_rel)
            test_path = os.path.normpath(os.path.join(parent, clean_target)).replace('\\', '/')

        # Check exact or with case-insensitive fallback
        if test_path in self.existing_rel_paths:
            return True

        # Check with index.html if target is directory
        if f"{test_path}/index.html" in self.existing_rel_paths:
            return True

        # Check physical existence on filesystem
        full = (self.root_dir / test_path).resolve()
        if str(full).startswith(str(self.root_dir.resolve())) and full.exists():
            return True

        return False
