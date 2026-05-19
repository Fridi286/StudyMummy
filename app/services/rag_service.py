"""
RAG-Service: Retrieval-Augmented Generation (Übungsblatt 03, Option A).
Kapselt den Vector Store – leicht gegen andere Backends austauschbar.
"""
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class RAGService:
    """
    Einfacher RAG-Service.
    In-Memory-Implementierung für Entwicklung/Tests.
    Für Produktion: ChromaDB / pgvector einbauen (Dependencies in pyproject.toml).
    """

    def __init__(self):
        self._documents: list[dict] = []  # {id, text, metadata}

    def add_document(self, doc_id: str, text: str, metadata: dict = {}) -> None:
        self._documents.append({"id": doc_id, "text": text, "metadata": metadata})
        log.info(f"RAG: added document {doc_id!r}")

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Mock-Retrieval: gibt die k ähnlichsten Dokumente zurück.
        TODO: echtes Embedding-basiertes Retrieval via ChromaDB.
        """
        if not self._documents:
            return ""
        results = self._documents[:top_k]
        context = "\n\n---\n\n".join(
            f"[Dokument: {r['id']}]\n{r['text'][:800]}" for r in results
        )
        log.info(f"RAG: retrieved {len(results)} docs for query={query[:50]!r}")
        return context

    def clear(self, doc_id: str | None = None) -> None:
        if doc_id:
            self._documents = [d for d in self._documents if d["id"] != doc_id]
        else:
            self._documents.clear()


# Singleton – wird in Dependencies injiziert
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
