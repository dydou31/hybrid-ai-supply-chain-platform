from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.chunk_models import KnowledgeChunk
from app.ai.embeddings import generate_embedding


def semantic_search_chunks(
    query: str,
    limit: int = 3,
    min_similarity: float = 0.40,
):
    """Search relevant knowledge chunks using pgvector cosine distance."""

    query_embedding = generate_embedding(query)

    with SessionLocal() as db:
        distance = KnowledgeChunk.embedding.cosine_distance(
            query_embedding
        )

        results = (
            db.query(KnowledgeChunk, distance.label("distance"))
            .options(joinedload(KnowledgeChunk.document))
            .filter(distance <= (1 - min_similarity))
            .order_by(distance)
            .limit(limit)
            .all()
        )

        chunks = []

        for chunk, distance_value in results:
            similarity = 1 - float(distance_value)

            chunks.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "title": chunk.document.title,
                "content": chunk.content,
                "source": chunk.document.source,
                "similarity": round(similarity, 4),
            })

        return chunks
