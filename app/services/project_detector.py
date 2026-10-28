"""
Project Detector Service for WebPulse.
Inspects extracted project files to detect:
- Project architecture (Static HTML/CSS/JS, Vite build project, generic)
- Likely entry point (index.html or main document)
- File distribution counts by category (HTML, CSS, JS, images, fonts, etc.)
- Total size and largest assets
- Runtime test availability
"""

import os
import json
from pathlib import Path

CATEGORY_MAPPING = {
    'html': {'.html', '.htm'},
    'css': {'.css'},
    'javascript': {'.js', '.mjs', '.cjs'},
    'image': {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.bmp'},
    'svg': {'.svg'},
    'font': {'.woff', '.woff2', '.ttf', '.otf', '.eot'},
    'json': {'.json'},
    'media': {'.mp4', '.webm', '.ogg', '.mp3', '.wav'},
}


def get_file_category(ext: str) -> str:
    ext_lower = ext.lower()
    for cat, exts in CATEGORY_MAPPING.items():
        if ext_lower in exts:
            return cat
    return 'other'


class ProjectDetector:
    get_file_category = staticmethod(get_file_category)

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)

    def detect(self) -> dict:
        total_files = 0
        total_size = 0
        categories = {k: 0 for k in list(CATEGORY_MAPPING.keys()) + ['other']}
        file_list = []
        entry_point = None
        has_package_json = False
        package_info = {}

        for dirpath, _, filenames in os.walk(self.root_dir):
            for filename in filenames:
                full_path = Path(dirpath) / filename
                if not full_path.is_file():
                    continue

                rel_path = str(full_path.relative_to(self.root_dir)).replace('\\', '/')
                size = full_path.stat().st_size
                ext = full_path.suffix.lower()
                cat = get_file_category(ext)

                total_files += 1
                total_size += size
                categories[cat] += 1

                file_list.append({
                    'relative_path': rel_path,
                    'size_bytes': size,
                    'category': cat,
                    'extension': ext
                })

                if rel_path.lower() == 'index.html':
                    entry_point = rel_path
                elif entry_point is None and ext in ('.html', '.htm'):
                    entry_point = rel_path

                if rel_path.lower() == 'package.json':
                    has_package_json = True
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            package_info = {
                                'name': data.get('name', 'unnamed'),
                                'scripts': list(data.get('scripts', {}).keys()),
                                'dependencies': list(data.get('dependencies', {}).keys()),
                                'devDependencies': list(data.get('devDependencies', {}).keys()),
                            }
                    except Exception:
                        package_info = {'error': 'Could not parse package.json'}

        file_list.sort(key=lambda x: x['size_bytes'], reverse=True)
        largest_files = file_list[:8]

        project_type = 'static_html'
        runtime_supported = True
        notes = []

        if has_package_json:
            dev_deps = package_info.get('devDependencies', []) + package_info.get('dependencies', [])
            if any('vite' in dep.lower() for dep in dev_deps):
                project_type = 'vite_frontend'
                notes.append("Vite build configuration detected.")
            else:
                project_type = 'generic'
                notes.append("Node/npm package manifest detected.")

        if not entry_point:
            if categories['html'] > 0:
                for item in file_list:
                    if item['category'] == 'html':
                        entry_point = item['relative_path']
                        break
            else:
                runtime_supported = False
                notes.append("No HTML entry point detected; browser runtime testing disabled.")

        return {
            'project_type': project_type,
            'entry_point': entry_point or '',
            'total_files': total_files,
            'total_size_bytes': total_size,
            'categories': categories,
            'largest_files': largest_files,
            'runtime_supported': runtime_supported,
            'package_info': package_info,
            'notes': notes
        }
