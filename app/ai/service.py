import requests

from app.ai.retrieval import semantic_search

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"


def ask_rag(query: str, limit: int = 3) -> dict:
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
