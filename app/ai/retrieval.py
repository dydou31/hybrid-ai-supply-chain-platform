import os

from opentelemetry import trace
from time import perf_counter
from typing import Callable, Optional

from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.chunk_models import KnowledgeChunk
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
            embedding_payload = {
                "duration_ms": round((perf_counter() - embedding_start) * 1000, 2),
                "dimensions": len(query_embedding),
                "model": "all-MiniLM-L6-v2",
            }

            if (os.getenv("RAG_VECTOR_DEBUG", "false").lower() == "true" and os.getenv("APP_ENV", "").lower() == "local"):
                embedding_payload["vector"] = query_embedding

            on_event("embedding.completed", embedding_payload)

        db = SessionLocal()

        if on_event:
            on_event("pgvector.started", {
                "limit": limit,
                "min_similarity": min_similarity,
            })

        search_start = perf_counter()

        try:
            with tracer.start_as_current_span("pgvector.search") as search_span:
                distance = KnowledgeChunk.embedding.cosine_distance(
                    query_embedding
                )

                results = (
                    db.query(KnowledgeChunk, distance.label("distance"))
                    .filter(KnowledgeChunk.embedding.isnot(None))
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
                        "document_id": document.document_id,
                        "chunk_index": document.chunk_index,
                        "title": document.document.title,
                        "content": document.content,
                        "source": document.document.source,
                        "similarity": round(similarity, 4),
                    }
                )

            search_span.set_attribute(
                "rag.documents_relevant",
                len(documents),
            )

            if on_event and (os.getenv("RAG_VECTOR_DEBUG", "false").lower() == "true" and os.getenv("APP_ENV", "").lower() == "local"):
                import math

                diagnostic_results = (
                    db.query(KnowledgeChunk, distance.label("distance"))
                    .filter(KnowledgeChunk.embedding.isnot(None))
                    .order_by(distance)
                    .limit(20)
                    .all()
                )

                vector_diagnostics = []

                for rank, (document, pg_distance) in enumerate(
                    diagnostic_results, start=1
                ):
                    document_vector = list(document.embedding)

                    products = [
                        float(a) * float(b)
                        for a, b in zip(query_embedding, document_vector)
                    ]

                    dot_product = sum(products)

                    query_norm = math.sqrt(
                        sum(float(x) ** 2 for x in query_embedding)
                    )

                    document_norm = math.sqrt(
                        sum(float(x) ** 2 for x in document_vector)
                    )

                    similarity = (
                        dot_product / (query_norm * document_norm)
                        if query_norm and document_norm
                        else 0.0
                    )

                    pgvector_similarity = 1 - float(pg_distance)

                    vector_diagnostics.append({
                        "id": document.id,
                        "document_id": document.document_id,
                        "chunk_index": document.chunk_index,
                        "title": document.document.title,
                        "rank": rank,
                        "selected": (
                            pgvector_similarity >= min_similarity
                            and rank <= limit
                        ),
                        "query_vector": query_embedding,
                        "document_vector": document_vector,
                        "products": products,
                        "dot_product": dot_product,
                        "query_norm": query_norm,
                        "document_norm": document_norm,
                        "similarity": similarity,
                        "pgvector_similarity": pgvector_similarity,
                        "distance": float(pg_distance),
                    })

                on_event("pgvector.diagnostics", {
                    "min_similarity": min_similarity,
                    "limit": limit,
                    "documents": vector_diagnostics,
                })

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
