"""
RAG-Service: Retrieval-Augmented Generation using pgvector.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import DocumentChunk, Document

log = get_logger(__name__)
settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

class RAGService:
    """
    RAG-Service using pgvector for similarity search.
    """
    
    async def retrieve(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        tags: list[str] | None = None,
        document_id: str | None = None,
        top_k: int = 3,
    ) -> str:
        """
        Embeds the query and retrieves the k most similar document chunks.
        Strictly filters by user_id for security.
        """
        if not settings.rag_embeddings_enabled:
            log.info("RAG: embeddings disabled; skipping retrieval.")
            return ""

        log.info(f"RAG: embedding query for user {user_id}")
        try:
            # 1. Embed the query
            response = await client.embeddings.create(
                input=query,
                model=settings.embedding_model
            )
            query_embedding = response.data[0].embedding
            
            # 2. Perform similarity search using pgvector
            stmt = select(DocumentChunk).where(
                DocumentChunk.user_id == user_id
            )

            if document_id:
                stmt = stmt.where(DocumentChunk.document_id == document_id)
            
            if tags:
                # Filter to chunks that belong to documents with all specified tags
                stmt = stmt.join(Document).where(Document.tags.contains(tags))
                
            # Use Cosine distance for similarity
            stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_embedding)).limit(top_k)
            
            result = await db.execute(stmt)
            chunks = result.scalars().all()
            
            if not chunks:
                return ""
                
            context = "\n\n---\n\n".join(
                f"[Dokument Chunk: {c.document_id} / {c.chunk_index}]\n{c.text}" for c in chunks
            )
            log.info(f"RAG: retrieved {len(chunks)} chunks for query={query[:50]!r}")
            return context
            
        except Exception as e:
            log.error(f"RAG retrieval failed: {e}")
            return ""

# Singleton
_rag_service: RAGService | None = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
