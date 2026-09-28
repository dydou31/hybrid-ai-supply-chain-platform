import requests
from opentelemetry import trace

from app.ai.retrieval import semantic_search
from app.observability.metrics import (
    RAG_REQUESTS_TOTAL,
    RAG_ERRORS_TOTAL,
    RAG_REQUEST_DURATION_SECONDS,
)

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

tracer = trace.get_tracer(__name__)


def ask_rag(query: str, limit: int = 3) -> dict:
    RAG_REQUESTS_TOTAL.inc()

    try:
        with RAG_REQUEST_DURATION_SECONDS.time():
            documents = semantic_search(query, limit=limit)

            context = "\n\n".join(
                f"[{doc['title']}]\n{doc['content']}"
                for doc in documents
            )

            prompt = f"""You are a Supply Chain AI assistant.

Answer the question using only the context below.
If the answer is not in the context, say that you do not have enough information.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

            with tracer.start_as_current_span("llm.ollama.generate") as span:
                span.set_attribute("llm.model", OLLAMA_MODEL)

                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=120,
                )

                response.raise_for_status()

            return {
                "answer": response.json()["response"].strip(),
                "sources": [
                    {
                        "id": doc["id"],
                        "title": doc["title"],
                        "source": doc["source"],
                        "similarity": doc["similarity"],
                    }
                    for doc in documents
                ],
            }

    except Exception:
        RAG_ERRORS_TOTAL.inc()
        raise
