import os
import re
from typing import Optional

class DocumentReader:
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.md', '.txt']

    @staticmethod
    def read_document(file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return DocumentReader._read_pdf(file_path)
        elif ext == '.docx':
            return DocumentReader._read_docx(file_path)
        elif ext == '.md':
            return DocumentReader._read_markdown(file_path)
        elif ext == '.txt':
            return DocumentReader._read_text(file_path)
        else:
            return None

    @staticmethod
    def _read_pdf(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            text = content.decode('latin-1', errors='ignore')
            text = re.sub(r'[^\x20-\x7E\n\r]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception:
            return None

    @staticmethod
    def _read_docx(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            text = content.decode('utf-8', errors='ignore')
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception:
            return None

    @staticmethod
    def _read_markdown(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception:
                return None

    @staticmethod
    def _read_text(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception:
                return None

    @staticmethod
    def is_supported(file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in DocumentReader.SUPPORTED_FORMATS
