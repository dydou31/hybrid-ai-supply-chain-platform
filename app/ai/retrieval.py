from opentelemetry import trace
from time import perf_counter
from typing import Callable, Optional

from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.embeddings import generate_embedding

tracer = trace.get_tracer(__name__)


def semantic_search(
    query: str,
    limit: int = 3,
    min_similarity: float = 0.40,
    on_event: Optional[Callable[[str, dict], None]] = None,
):
    with tracer.start_as_current_span("rag.semantic_search") as span:
        span.set_attribute("rag.limit", limit)

        if on_event:
            on_event("embedding.started", {})

        embedding_start = perf_counter()

        try:
            with tracer.start_as_current_span("embedding.generate"):
                query_embedding = generate_embedding(query)
        except Exception as exc:
            if on_event:
                on_event("embedding.failed", {
                    "duration_ms": round((perf_counter() - embedding_start) * 1000, 2),
                    "error_type": type(exc).__name__,
                })
            raise

        if on_event:
            on_event("embedding.completed", {
                "duration_ms": round((perf_counter() - embedding_start) * 1000, 2),
                "dimensions": len(query_embedding),
            })

        db = SessionLocal()

        if on_event:
            on_event("pgvector.started", {
                "limit": limit,
                "min_similarity": min_similarity,
            })

        search_start = perf_counter()

        try:
            with tracer.start_as_current_span("pgvector.search") as search_span:
                distance = KnowledgeDocument.embedding.cosine_distance(
                    query_embedding
                )

                results = (
                    db.query(KnowledgeDocument, distance.label("distance"))
                    .filter(KnowledgeDocument.embedding.isnot(None))
                    .filter(distance <= (1 - min_similarity))
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

            if on_event:
                on_event("pgvector.completed", {
                    "duration_ms": round(
                        (perf_counter() - search_start) * 1000, 2
                    ),
                    "documents_count": len(documents),
                    "scores": [
                        {
                            "title": doc["title"],
                            "similarity": doc["similarity"],
                        }
                        for doc in documents
                    ],
                })

            return documents

        except Exception as exc:
            if on_event:
                on_event("pgvector.failed", {
                    "duration_ms": round(
                        (perf_counter() - search_start) * 1000, 2
                    ),
                    "error_type": type(exc).__name__,
                })
            raise

        finally:
            db.close()
