"""
Dependency Mapper Service for WebPulse.
Extracts project-wide file relationships and builds Cytoscape.js dependency graph data.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

class DependencyMapper:
    def __init__(self, root_dir: Path, files_map: dict):
        """
        root_dir: project folder
        files_map: dict of relative_path -> metadata/model dict
        """
        self.root_dir = Path(root_dir)
        self.files_map = files_map
        self.edges = []
        self.missing_nodes = {} # path -> missing node info

    def extract_dependencies(self) -> list:
        for rel_path, file_data in self.files_map.items():
            full_path = self.root_dir / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue

            file_type = file_data.get('file_type', '')

            if file_type == 'html':
                self._extract_from_html(rel_path, full_path)
            elif file_type == 'css':
                self._extract_from_css(rel_path, full_path)
            elif file_type == 'javascript':
                self._extract_from_js(rel_path, full_path)

        return self.edges

    def _resolve_target(self, source_rel: str, raw_ref: str):
        """
        Resolves reference to a target relative path within the project.
        Returns (resolved_rel_path, is_broken)
        """
        clean_ref = raw_ref.split('?')[0].split('#')[0].strip()
        if not clean_ref or clean_ref.startswith(('http://', 'https://', 'data:', '//', 'mailto:', 'tel:')):
            return None, False

        if clean_ref.startswith('/'):
            target_rel = clean_ref.lstrip('/')
        else:
            parent = os.path.dirname(source_rel)
            target_rel = os.path.normpath(os.path.join(parent, clean_ref)).replace('\\', '/')

        if target_rel in self.files_map:
            return target_rel, False

        if f"{target_rel}/index.html" in self.files_map:
            return f"{target_rel}/index.html", False

        # Physical file check
        full = (self.root_dir / target_rel).resolve()
        if str(full).startswith(str(self.root_dir.resolve())) and full.exists() and full.is_file():
            return target_rel, False

        # Broken local reference
        return target_rel, True

    def _extract_from_html(self, rel_path: str, full_path: Path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        soup = BeautifulSoup(content, 'html.parser')

        # Stylesheets
        for link in soup.find_all('link', rel=lambda r: r and 'stylesheet' in r):
            href = link.get('href')
            if href:
                target_rel, is_broken = self._resolve_target(rel_path, href)
                if target_rel:
                    self.edges.append({
                        'source_path': rel_path,
                        'target_path': target_rel,
                        'relationship_type': 'stylesheet',
                        'is_broken': is_broken,
                        'evidence': f"<link rel='stylesheet' href='{href}'>"
                    })

        # Scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                target_rel, is_broken = self._resolve_target(rel_path, src)
                if target_rel:
                    self.edges.append({
                        'source_path': rel_path,
                        'target_path': target_rel,
                        'relationship_type': 'script',
                        'is_broken': is_broken,
                        'evidence': f"<script src='{src}'>"
                    })

        # Images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                target_rel, is_broken = self._resolve_target(rel_path, src)
                if target_rel:
                    self.edges.append({
                        'source_path': rel_path,
                        'target_path': target_rel,
                        'relationship_type': 'image',
                        'is_broken': is_broken,
                        'evidence': f"<img src='{src}'>"
                    })

        # Favicon / icons
        for icon in soup.find_all('link', rel=lambda r: r and 'icon' in r):
            href = icon.get('href')
            if href:
                target_rel, is_broken = self._resolve_target(rel_path, href)
                if target_rel:
                    self.edges.append({
                        'source_path': rel_path,
                        'target_path': target_rel,
                        'relationship_type': 'image',
                        'is_broken': is_broken,
                        'evidence': f"<link rel='icon' href='{href}'>"
                    })

    def _extract_from_css(self, rel_path: str, full_path: Path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        # url(...)
        url_matches = re.findall(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', content)
        for url in url_matches:
            target_rel, is_broken = self._resolve_target(rel_path, url)
            if target_rel:
                ext = os.path.splitext(target_rel)[1].lower()
                rel_type = 'font' if ext in ('.woff', '.woff2', '.ttf', '.otf', '.eot') else 'image'
                self.edges.append({
                    'source_path': rel_path,
                    'target_path': target_rel,
                    'relationship_type': rel_type,
                    'is_broken': is_broken,
                    'evidence': f"url('{url}')"
                })

        # @import
        imports = re.findall(r'@import\s+["\']([^"\']+)["\'];?', content)
        for imp in imports:
            target_rel, is_broken = self._resolve_target(rel_path, imp)
            if target_rel:
                self.edges.append({
                    'source_path': rel_path,
                    'target_path': target_rel,
                    'relationship_type': 'import',
                    'is_broken': is_broken,
                    'evidence': f"@import '{imp}'"
                })

    def _extract_from_js(self, rel_path: str, full_path: Path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        # static ES module imports
        imports = re.findall(r'import\s+(?:[\w*\s{},]+from\s+)?[\'"](\./[^\'"]+|\.\./[^\'"]+)[\'"]', content)
        for imp in imports:
            target_rel, is_broken = self._resolve_target(rel_path, imp)
            if is_broken and not target_rel.endswith('.js'):
                # try with .js
                t2, b2 = self._resolve_target(rel_path, imp + '.js')
                if not b2:
                    target_rel, is_broken = t2, b2

            if target_rel:
                self.edges.append({
                    'source_path': rel_path,
                    'target_path': target_rel,
                    'relationship_type': 'import',
                    'is_broken': is_broken,
                    'evidence': f"import from '{imp}'"
                })

    def build_cytoscape_elements(self, project_files_qs=None, findings_by_path=None) -> list:
        """
        Generates Cytoscape.js compatible list of elements (nodes and edges).
        """
        findings_count = findings_by_path or {}
        elements = []
        node_ids = set()

        # Add existing project file nodes
        for rel_path, file_data in self.files_map.items():
            node_id = rel_path
            node_ids.add(node_id)
            file_name = os.path.basename(rel_path) or rel_path
            file_type = file_data.get('file_type', 'other')
            size_kb = round(file_data.get('size_bytes', 0) / 1024, 1)
            is_entry = file_data.get('is_entry_point', False)
            f_count = findings_count.get(rel_path, 0)

            elements.append({
                'data': {
                    'id': node_id,
                    'label': file_name,
                    'path': rel_path,
                    'type': file_type,
                    'size_kb': size_kb,
                    'is_entry': is_entry,
                    'findings_count': f_count,
                    'is_missing': False,
                }
            })

        # Add edges and missing file nodes
        for idx, edge in enumerate(self.edges):
            source = edge['source_path']
            target = edge['target_path']

            if target not in node_ids:
                # Create a missing/error node
                node_ids.add(target)
                elements.append({
                    'data': {
                        'id': target,
                        'label': f"⚠️ {os.path.basename(target)}",
                        'path': target,
                        'type': 'missing',
                        'size_kb': 0,
                        'is_entry': False,
                        'findings_count': 1,
                        'is_missing': True,
                    }
                })

            elements.append({
                'data': {
                    'id': f"e_{idx}_{edge['relationship_type']}",
                    'source': source,
                    'target': target,
                    'type': edge['relationship_type'],
                    'is_broken': edge['is_broken'],
                    'label': edge['relationship_type']
                }
            })

        return elements
