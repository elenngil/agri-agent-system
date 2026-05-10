"""
Retriever sobre ChromaDB. Usado por ExplanationAgent y CriticAgent.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR  = Path(__file__).parent.parent / "chroma_db"
COLLECTION  = "agri_knowledge"
MODEL_NAME  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class Chunk:
    chunk_id: str
    content:  str
    metadata: dict
    score:    float


class AgriRetriever:

    _encoder_instance = None

    def __init__(self):
        if AgriRetriever._encoder_instance is None:
            AgriRetriever._encoder_instance = SentenceTransformer(MODEL_NAME)
        self._encoder = AgriRetriever._encoder_instance
        
        client           = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self._collection = client.get_collection(COLLECTION)

    def retrieve(self, query: str, top_k: int = 3, filters: dict | None = None) -> list[Chunk]:
        if not query.strip():
            return []

        embedding = self._encoder.encode([query])[0].tolist()
        where     = self._build_where(filters)

        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        return [
            Chunk(chunk_id=cid, content=doc, metadata=meta, score=round(dist, 4))
            for cid, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def format_context(self, chunks: list[Chunk], max_chars: int = 2500) -> str:
        parts, total = [], 0
        for c in chunks:
            source = c.metadata.get("filename", "—")
            block  = f"[{source}]\n{c.content}"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "\n\n---\n\n".join(parts)

    def _build_where(self, filters: dict | None) -> dict | None:
        if not filters:
            return None
        conditions = [{k: {"$eq": str(v)}} for k, v in filters.items() if v]
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    @property
    def count(self) -> int:
        return self._collection.count()


@lru_cache(maxsize=1)
def get_chroma_retriever() -> AgriRetriever:
    """Singleton: el modelo y ChromaDB se cargan una sola vez."""
    return AgriRetriever()
