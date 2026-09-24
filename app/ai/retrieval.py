from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.embeddings import generate_embedding


def semantic_search(query: str, limit: int = 3):
    query_embedding = generate_embedding(query)

    db = SessionLocal()
    try:
        distance = KnowledgeDocument.embedding.cosine_distance(query_embedding)

        results = (
            db.query(KnowledgeDocument, distance.label("distance"))
            .filter(KnowledgeDocument.embedding.isnot(None))
            .order_by(distance)
            .limit(limit)
            .all()
        )

        return [
            {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "source": document.source,
                "similarity": round(1 - float(distance_value), 4),
            }
            for document, distance_value in results
        ]
    finally:
        db.close()
