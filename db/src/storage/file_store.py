import os
import shutil
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

class FileStore:
    def __init__(self, base_path: str = "db/drawers"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(os.path.join(base_path, "cache", "embeddings"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "cache", "thumbnails"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "exports"), exist_ok=True)

    def store_file(self, source_path: str, hall_id: str, original_name: Optional[str] = None) -> Dict[str, Any]:
        if original_name is None:
            original_name = os.path.basename(source_path)

        hall_path = os.path.join(self.base_path, hall_id)
        os.makedirs(hall_path, exist_ok=True)

        file_id = f"{int(datetime.now().timestamp())}_{hashlib.md5(original_name.encode()).hexdigest()[:8]}"
        dest_name = f"{file_id}_{original_name}"
        dest_path = os.path.join(hall_path, dest_name)

        shutil.copy2(source_path, dest_path)

        file_size = os.path.getsize(dest_path)
        file_hash = self._calculate_hash(dest_path)
        mime_type = self._get_mime_type(original_name)

        return {
            'id': file_id,
            'hall_id': hall_id,
            'file_path': dest_path,
            'file_name': original_name,
            'file_hash': file_hash,
            'file_size': file_size,
            'mime_type': mime_type
        }

    def get_file(self, file_path: str) -> Optional[bytes]:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
        return None

    def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def export_file(self, file_path: str, export_dir: str = "db/drawers/exports") -> Optional[str]:
        os.makedirs(export_dir, exist_ok=True)
        dest_path = os.path.join(export_dir, os.path.basename(file_path))
        shutil.copy2(file_path, dest_path)
        return dest_path

    def _calculate_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_mime_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.csv': 'text/csv'
        }
        return mime_types.get(ext, 'application/octet-stream')

    def list_files(self, hall_id: Optional[str] = None) -> list:
        if hall_id:
            path = os.path.join(self.base_path, hall_id)
        else:
            path = self.base_path

        if not os.path.exists(path):
            return []

        files = []
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                })
        return files
