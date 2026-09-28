from opentelemetry import trace

from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.embeddings import generate_embedding

tracer = trace.get_tracer(__name__)


def semantic_search(
    query: str,
    limit: int = 3,
    min_similarity: float = 0.30,
):
    with tracer.start_as_current_span("rag.semantic_search") as span:
        span.set_attribute("rag.limit", limit)

        with tracer.start_as_current_span("embedding.generate"):
            query_embedding = generate_embedding(query)

        db = SessionLocal()

        try:
            with tracer.start_as_current_span("pgvector.search") as search_span:
                distance = KnowledgeDocument.embedding.cosine_distance(
                    query_embedding
                )

                results = (
                    db.query(KnowledgeDocument, distance.label("distance"))
                    .filter(KnowledgeDocument.embedding.isnot(None))
                    .order_by(distance)
                    .limit(limit)
                    .all()
                )

                search_span.set_attribute(
                    "rag.documents_returned",
                    len(results),
                )

            documents = []

            for document, distance_value in results:
                similarity = 1 - float(distance_value)

                if similarity < min_similarity:
                    continue

                documents.append(
                    {
                        "id": document.id,
                        "title": document.title,
                        "content": document.content,
                        "source": document.source,
                        "similarity": round(similarity, 4),
                    }
                )

            search_span.set_attribute(
                "rag.documents_relevant",
                len(documents),
            )

            return documents

        finally:
            db.close()
