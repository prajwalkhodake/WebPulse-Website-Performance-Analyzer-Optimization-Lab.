"""
Archive Validator Service for WebPulse.
Safely inspects and extracts uploaded ZIP archives with protection against:
- Zip Slip (directory traversal: ../ or absolute paths)
- Decompression bombs (excessive ratio or total uncompressed size)
- Excessive archive entries
- Secret detection (.env, private keys, certificates)
- Dangerous executable files
"""

import os
import zipfile
import shutil
from pathlib import Path
from flask import current_app

SECRET_PATTERNS = {
    '.env', '.env.local', '.env.production', '.env.development',
    'id_rsa', 'id_dsa', 'id_ed25519', '.pem', '.key', 'credentials.json',
    'serviceAccountKey.json', 'client_secret.json'
}

IGNORED_DIRS = {
    '__pycache__', 'node_modules', '.git', '.svn', '.hg',
    '.vscode', '.idea', '.venv', 'venv', '.DS_Store', '__MACOSX'
}

DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.msi', '.com'
}


class ValidationError(Exception):
    pass


class ArchiveValidator:
    def __init__(self, file_storage, user_id, project_id, version_num):
        """
        file_storage: Werkzeug FileStorage object or file-like object
        user_id: user identifier
        project_id: project identifier
        version_num: version integer
        """
        self.file_storage = file_storage
        self.user_id = str(user_id)
        self.project_id = str(project_id)
        self.version_num = version_num
        self.warnings = []
        self.detected_secrets = []
        self.ignored_count = 0
        self.extracted_files = []

    def validate_and_extract(self) -> dict:
        """
        Validates ZIP archive and safely extracts allowed files to private storage.
        Returns a dictionary with status, extraction path, stats, and warnings.
        """
        # Determine upload size
        self.file_storage.seek(0, os.SEEK_END)
        upload_size = self.file_storage.tell()
        self.file_storage.seek(0)

        max_upload = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        if upload_size > max_upload:
            raise ValidationError(
                f"Uploaded archive size ({upload_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {max_upload / (1024*1024):.0f} MB."
            )

        if upload_size == 0:
            raise ValidationError("The uploaded ZIP archive is completely empty (0 bytes).")

        # Open and inspect ZIP structure without extracting
        try:
            zf = zipfile.ZipFile(self.file_storage)
        except (zipfile.BadZipFile, Exception):
            raise ValidationError("The uploaded file is not a valid ZIP archive or is corrupted.")

        infolist = zf.infolist()
        max_entries = 2000
        if len(infolist) > max_entries:
            raise ValidationError(
                f"Archive contains {len(infolist)} entries, exceeding the security limit of {max_entries} files."
            )

        if len(infolist) == 0:
            raise ValidationError("Archive contains no files.")

        # Calculate uncompressed size and check for zip bombs
        max_uncompressed = 150 * 1024 * 1024
        total_uncompressed = 0
        for entry in infolist:
            total_uncompressed += entry.file_size
            if entry.compress_size > 0:
                ratio = entry.file_size / entry.compress_size
                if ratio > 100 and entry.file_size > 5 * 1024 * 1024:
                    raise ValidationError(
                        f"Decompression bomb detected in entry '{entry.filename}' (compression ratio {ratio:.1f}x)."
                    )

        if total_uncompressed > max_uncompressed:
            raise ValidationError(
                f"Total uncompressed project size ({total_uncompressed / (1024*1024):.1f} MB) exceeds maximum allowed limit of {max_uncompressed / (1024*1024):.0f} MB."
            )

        # Check for Zip Slip (path traversal / absolute paths / symlinks)
        for entry in infolist:
            raw_path = entry.filename.replace('\\', '/')
            if raw_path.startswith('/') or '..' in raw_path.split('/'):
                raise ValidationError(
                    f"Malicious path traversal or absolute path detected in archive: '{entry.filename}'"
                )

            # Check for symlink abuse (Unix mode 0o120000)
            if (entry.external_attr >> 16) & 0o120000 == 0o120000:
                raise ValidationError(
                    f"Symbolic link detected in archive: '{entry.filename}'. Symlinks are prohibited for security."
                )

        # Prepare private extraction destination
        base_storage = Path(current_app.config['STORAGE_DIR'])
        dest_dir = base_storage / 'extracted' / f"user_{self.user_id}" / f"project_{self.project_id}" / f"v{self.version_num}"

        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Safe extraction: filter out ignored folders, secret files, dangerous extensions
        extracted_bytes = 0
        for entry in infolist:
            if entry.is_dir():
                continue

            clean_rel = os.path.normpath(entry.filename.replace('\\', '/')).lstrip('/')
            path_parts = clean_rel.split(os.sep)

            if any(part in IGNORED_DIRS for part in path_parts):
                self.ignored_count += 1
                continue

            filename = path_parts[-1]
            ext = os.path.splitext(filename)[1].lower()

            if ext in DANGEROUS_EXTENSIONS:
                self.warnings.append(f"Ignored executable/script file '{clean_rel}' for security.")
                continue

            if filename in SECRET_PATTERNS or filename.startswith('.env') or ext in {'.key', '.pem'}:
                self.detected_secrets.append(clean_rel)
                self.warnings.append(f"Detected and skipped sensitive configuration file: '{clean_rel}'.")
                continue

            target_path = (dest_dir / clean_rel).resolve()
            if not str(target_path).startswith(str(dest_dir.resolve())):
                raise ValidationError(f"Security error: Extracted file path '{target_path}' escapes target directory.")

            target_path.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(entry) as src_file, open(target_path, 'wb') as dst_file:
                shutil.copyfileobj(src_file, dst_file)

            extracted_bytes += entry.file_size
            self.extracted_files.append(clean_rel)

        # Check if archive was extracted into a single wrapper subfolder
        self._normalize_single_root_folder(dest_dir)

        # Save the original ZIP archive copy for provenance
        archive_dest_dir = base_storage / 'uploads' / f"user_{self.user_id}" / f"project_{self.project_id}"
        archive_dest_dir.mkdir(parents=True, exist_ok=True)
        archive_save_path = archive_dest_dir / f"v{self.version_num}.zip"
        self.file_storage.seek(0)
        with open(archive_save_path, 'wb') as dst_zip:
            shutil.copyfileobj(self.file_storage, dst_zip)

        relative_storage = str(dest_dir.relative_to(base_storage))

        return {
            'success': True,
            'storage_path': relative_storage,
            'absolute_path': str(dest_dir),
            'archive_saved_path': str(archive_save_path),
            'extracted_file_count': len(self.extracted_files),
            'total_size_bytes': extracted_bytes,
            'warnings': self.warnings,
            'detected_secrets': self.detected_secrets,
            'ignored_count': self.ignored_count
        }

    def _normalize_single_root_folder(self, dest_dir: Path):
        """If files were wrapped in a single root directory inside zip, hoist to dest_dir."""
        children = list(dest_dir.iterdir())
        if len(children) == 1 and children[0].is_dir():
            single_folder = children[0]
            temp_dir = dest_dir.parent / f"{dest_dir.name}_temp"
            single_folder.rename(temp_dir)
            dest_dir.rmdir()
            temp_dir.rename(dest_dir)
