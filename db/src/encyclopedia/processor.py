import re
import os
import time
from typing import Dict, List, Optional, Any
from .readers import DocumentReader

CATEGORIES = {
    "计算机科学": ["计算机", "编程", "算法", "软件", "硬件", "代码", "编程语言"],
    "人工智能": ["人工智能", "机器学习", "深度学习", "神经网络", "AI", "自然语言处理"],
    "数学": ["数学", "代数", "几何", "微积分", "概率", "统计"],
    "物理": ["物理", "力学", "电磁学", "量子", "相对论"],
    "化学": ["化学", "分子", "原子", "反应", "有机", "无机"],
    "生物": ["生物", "细胞", "基因", "进化", "生态"],
    "医学": ["医学", "疾病", "治疗", "药物", "临床"],
    "经济学": ["经济", "市场", "金融", "投资", "贸易"],
    "管理学": ["管理", "组织", "战略", "领导", "决策"]
}

class EncyclopediaProcessor:
    def __init__(self, vector_store=None):
        self.reader = DocumentReader()
        self.vector_store = vector_store

    def process_document(self, file_path: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        content = self.reader.read_document(file_path)
        if content is None:
            return {'success': False, 'error': '无法读取文档'}

        filename = os.path.basename(file_path)
        extracted_metadata = self.extract_metadata(content, filename, metadata)

        if self.vector_store:
            doc_id = self.vector_store.add_document(
                content=content,
                metadata=extracted_metadata,
                collection_name="documents"
            )
            extracted_metadata['id'] = doc_id

        return {
            'success': True,
            'content': content,
            'metadata': extracted_metadata
        }

    def process_batch(self, file_paths: List[str], metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        results = []
        for file_path in file_paths:
            result = self.process_document(file_path, metadata)
            results.append(result)
        return results

    def extract_metadata(
        self,
        content: str,
        filename: str = "",
        extra_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        title = self._extract_title(content, filename)
        authors = self._extract_authors(content)
        date = self._extract_date(content)
        keywords = self._extract_keywords(content)
        abstract = self._extract_abstract(content)
        category = self._classify_document(content)

        metadata = {
            'title': title,
            'authors': authors,
            'date': date,
            'keywords': keywords,
            'abstract': abstract,
            'category': category,
            'kind': 'encyclopedia',
            'source': filename,
            'processed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        if extra_metadata:
            metadata.update(extra_metadata)

        return metadata

    def _extract_title(self, content: str, filename: str) -> str:
        lines = content.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 5 and len(line) < 200:
                return line
        return filename.replace('.md', '').replace('.txt', '')

    def _extract_authors(self, content: str) -> List[str]:
        author_patterns = [
            r'作者[：:]\s*([^\n]+)',
            r'Author[：:]\s*([^\n]+)',
            r'By\s+([^\n]+)',
        ]
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                authors_str = match.group(1)
                authors = [a.strip() for a in re.split(r'[,，;；]', authors_str)]
                return [a for a in authors if a]
        return ["Unknown"]

    def _extract_date(self, content: str) -> str:
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(202[0-9][-/]\d{1,2}[-/]\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return time.strftime('%Y-%m-%d')

    def _extract_keywords(self, content: str) -> List[str]:
        keyword_patterns = [
            r'关键词[：:]\s*([^\n]+)',
            r'Keywords?[：:]\s*([^\n]+)',
        ]
        for pattern in keyword_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                keywords_str = match.group(1)
                keywords = [k.strip() for k in re.split(r'[,，;；\s]', keywords_str)]
                return [k for k in keywords if k and len(k) > 1][:10]

        words = re.findall(r'[\u4e00-\u9fff]{2,}', content[:5000])
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]

    def _extract_abstract(self, content: str) -> str:
        abstract_patterns = [
            r'摘要[：:]\s*([^\n]+(?:\n[^\n]+)*)',
            r'Abstract[：:]\s*([^\n]+(?:\n[^\n]+)*)',
        ]
        for pattern in abstract_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).replace('\n', ' ')
                abstract = re.sub(r'\s+', ' ', abstract)
                return abstract[:200]
        return content[:200] + "..."

    def _classify_document(self, content: str) -> List[str]:
        scores = {}
        content_lower = content.lower()

        for category, keywords in CATEGORIES.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1
            if score > 0:
                scores[category] = score

        if not scores:
            return ["其他"]

        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [sorted_categories[0][0]] if sorted_categories else ["其他"]

    def store_to_db(self, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        if self.vector_store is None:
            return None

        doc_id = f"enc-{int(time.time())}-{hash(content) % 100000}"
        metadata['id'] = doc_id
        metadata['kind'] = 'encyclopedia'

        self.vector_store.add_document(
            content=content,
            metadata=metadata,
            doc_id=doc_id,
            collection_name="documents"
        )
        return doc_id
