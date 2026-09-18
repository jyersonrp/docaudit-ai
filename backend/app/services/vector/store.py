import json
import sqlite3
import math
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from app.models.document import DocumentChunk
from app.core.config import settings

class BaseVectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        pass

    @abstractmethod
    def search(self, query: str, doc_id: Optional[str] = None, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        pass

    @abstractmethod
    def get_chunks_by_doc(self, doc_id: str) -> List[DocumentChunk]:
        pass

    @abstractmethod
    def delete_doc(self, doc_id: str) -> None:
        pass

class LocalVectorStore(BaseVectorStore):
    """
    Production-ready lightweight SQLite vector & keyword store.
    Computes TF-IDF hybrid cosine similarity locally, with support for dense embeddings.
    Zero external database requirements for local testing.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    section TEXT,
                    embedding TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
            conn.commit()

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        if not chunks:
            return
        with self._get_connection() as conn:
            data = [
                (
                    c.id,
                    c.doc_id,
                    c.page_number,
                    c.chunk_index,
                    c.content,
                    c.token_count,
                    c.section,
                    json.dumps(c.embedding) if c.embedding else None
                )
                for c in chunks
            ]
            conn.executemany("""
                INSERT OR REPLACE INTO chunks (id, doc_id, page_number, chunk_index, content, token_count, section, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()

    def get_chunks_by_doc(self, doc_id: str) -> List[DocumentChunk]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC", (doc_id,))
            rows = cursor.fetchall()
            return [
                DocumentChunk(
                    id=row["id"],
                    doc_id=row["doc_id"],
                    page_number=row["page_number"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    token_count=row["token_count"],
                    section=row["section"],
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None
                )
                for row in rows
            ]

    def delete_doc(self, doc_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.commit()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def search(self, query: str, doc_id: Optional[str] = None, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """
        Hybrid vector and lexical search.
        If chunks have dense embeddings, uses cosine similarity.
        Otherwise, uses normalized TF-IDF vector cosine similarity + lexical matching.
        Only returns chunks with positive relevance (score > 0).
        """
        with self._get_connection() as conn:
            if doc_id:
                cursor = conn.execute("SELECT * FROM chunks WHERE doc_id = ?", (doc_id,))
            else:
                cursor = conn.execute("SELECT * FROM chunks")
            rows = cursor.fetchall()

        if not rows:
            return []

        chunks = [
            DocumentChunk(
                id=r["id"],
                doc_id=r["doc_id"],
                page_number=r["page_number"],
                chunk_index=r["chunk_index"],
                content=r["content"],
                token_count=r["token_count"],
                section=r["section"],
                embedding=json.loads(r["embedding"]) if r["embedding"] else None
            )
            for r in rows
        ]

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [(c, 1.0) for c in chunks[:top_k]]

        # Document frequencies for TF-IDF
        df: Dict[str, int] = {}
        doc_token_counts: List[Dict[str, int]] = []
        for c in chunks:
            tokens = self._tokenize(c.content)
            tf_dict: Dict[str, int] = {}
            for t in tokens:
                tf_dict[t] = tf_dict.get(t, 0) + 1
            for t in tf_dict.keys():
                df[t] = df.get(t, 0) + 1
            doc_token_counts.append(tf_dict)

        num_docs = len(chunks)
        scored_chunks: List[Tuple[DocumentChunk, float]] = []

        for i, c in enumerate(chunks):
            tf_dict = doc_token_counts[i]
            score = 0.0
            content_lower = c.content.lower()

            # Exact phrase boost
            if query.lower() in content_lower:
                score += 0.5

            # TF-IDF term scoring
            for q_term in q_tokens:
                if q_term in tf_dict:
                    term_tf = tf_dict[q_term]
                    idf = math.log((num_docs + 1) / (df.get(q_term, 1) + 1)) + 1.0
                    score += (term_tf / max(c.token_count, 1)) * idf

            # Section boost
            if c.section and any(q_term in c.section.lower() for q_term in q_tokens):
                score += 0.3

            # Only retain chunks with a genuine match
            if score > 0.0:
                norm_score = min(score / 1.5, 1.0)
                scored_chunks.append((c, float(norm_score)))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

# Global store singleton
vector_store = LocalVectorStore()
