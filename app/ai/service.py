import os

import boto3
import requests
from opentelemetry import trace

from app.ai.retrieval import semantic_search
from app.ai.structured_retrieval import get_relevant_structured_context
from app.ai.business_glossary import BUSINESS_GLOSSARY
from app.observability.metrics import (
    RAG_REQUESTS_TOTAL,
    RAG_ERRORS_TOTAL,
    RAG_REQUEST_DURATION_SECONDS,
)


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://host.docker.internal:11434/api/generate",
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

BEDROCK_REGION = os.getenv("BEDROCK_REGION", "eu-west-3")
BEDROCK_MODEL = os.getenv(
    "BEDROCK_MODEL",
    "eu.amazon.nova-micro-v1:0",
)

tracer = trace.get_tracer(__name__)


def generate_with_ollama(prompt: str) -> str:
    with tracer.start_as_current_span("llm.ollama.generate") as span:
        span.set_attribute("llm.provider", "ollama")
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

        return response.json()["response"].strip()


def generate_with_bedrock(prompt: str) -> str:
    with tracer.start_as_current_span("llm.bedrock.converse") as span:
        span.set_attribute("llm.provider", "bedrock")
        span.set_attribute("llm.model", BEDROCK_MODEL)

        client = boto3.client(
            "bedrock-runtime",
            region_name=BEDROCK_REGION,
        )

        response = client.converse(
            modelId=BEDROCK_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt,
                        }
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0,
            },
        )

        return response["output"]["message"]["content"][0]["text"].strip()


def generate_answer(prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return generate_with_ollama(prompt)

    if LLM_PROVIDER == "bedrock":
        return generate_with_bedrock(prompt)

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
        "Expected 'ollama' or 'bedrock'."
    )


def ask_rag(query: str, limit: int = 3) -> dict:
    RAG_REQUESTS_TOTAL.inc()

    try:
        with RAG_REQUEST_DURATION_SECONDS.time():
            documents = semantic_search(query, limit=limit)
            structured_context = get_relevant_structured_context(query)

            rag_context = "\n\n".join(
                f"[{doc['title']}]\n{doc['content']}"
                for doc in documents
            )

            if not rag_context:
                rag_context = "No relevant knowledge documents found."

            prompt = f"""You are a Supply Chain AI assistant.

Answer the user's question using only the supplied data.

You have two information sources:

1. STRUCTURED DATA
Live operational data retrieved from PostgreSQL.

2. KNOWLEDGE DOCUMENTS
Relevant unstructured documents retrieved with semantic search
from pgvector.

Rules:
- Use structured data for factual questions about suppliers,
  risk levels, blocked stock and purchase orders.
- Use knowledge documents when they contain relevant operational
  information.
- Combine both sources when useful.
- Do not invent facts, labels, interpretations, or qualifications
  that are not explicitly present in the supplied data.
- Preserve numerical values exactly as provided by structured data.
- When structured data contains a ranking, preserve its exact order.
- When the user asks for a ranking or list, return every item supplied
  for that ranking; do not omit, merge, or add items.
- Do not reinterpret business labels. For example, "high risk" means
  high risk and must not be transformed into "high value" or another label.
- Do not claim that one supplier represents a percentage of all delays
  unless that percentage is explicitly supplied in the structured data.
- If the supplied data does not contain the answer, say that you
  do not have enough information.
- Always answer entirely in the same language as the user's question.
- Never mix languages in section titles or in the answer.
- Present the answer in a clear, concise and visually structured format.
- Use short section headings and bullet points when several facts are available.
- For supplier performance or supplier analysis questions, organize the answer into four short sections.
- If the user's question is in French, use exactly these Markdown section headings:
  ### SYNTHÈSE
  ### INDICATEURS CLÉS
  ### ANALYSE
  ### RECOMMANDATION
- If the user's question is not in French, use equivalent headings in the user's language.
- SYNTHESIS / SYNTHÈSE must be one short paragraph with no bullets.
- KEY INDICATORS / INDICATEURS CLÉS must contain only quantitative KPIs or concise measurable facts actually present in the supplied context. Prefer 2 to 5 flat bullet points. Never invent a KPI. If no quantitative KPI is available, write one short sentence instead of creating qualitative bullet lists.
- ANALYSIS / ANALYSE must be one short paragraph with no bullets.
- RECOMMENDATION must be one short paragraph for a single recommendation, or one flat numbered list for several distinct actions.
- Never create nested lists or a bullet whose only purpose is to introduce more bullets.
- Do not repeat the same action or fact in multiple sections unless necessary for the conclusion.
- When the structured context contains an explicitly ranked list of suppliers (for example lines beginning with 1., 2., 3.), preserve that ranking supplier by supplier in the final answer.
- For a supplier prioritization question, INDICATEURS CLÉS must show the ranked suppliers individually, with the supplier name and the quantitative metrics supplied for that supplier.
- Never merge metrics from several ranked suppliers into one aggregate KPI line.
- Do not omit supplier names from a ranking requested by the user.
- Translate technical metric labels into the user's language, but preserve supplier names and numeric values exactly.
- For French ranking answers, format each ranked supplier as one compact numbered item using French labels such as : commandes en retard, taux de retard, retard moyen, stock bloqué.
- Under INDICATEURS CLÉS, use bullet points for the relevant available KPIs.
- Do not copy or repeat these instructions in the answer.
- Do not display a section when no relevant supplied information exists for it.
- Keep the response concise and suitable for an operational dashboard.
- When available in structured data, explicitly mention:
  total purchase orders,
  delayed purchase orders,
  delay rate,
  average delay days,
  and blocked stock EUR.
- Recommended actions must be practical supply-chain actions grounded in the supplied data.
- Prefer actions such as supplier review, root-cause analysis, delivery recovery plan,
  short-term supply securing, escalation, and weekly KPI follow-up when relevant.
- Do not invent missing operational facts.

BUSINESS GLOSSARY:
{BUSINESS_GLOSSARY}

STRUCTURED DATA:
{structured_context}

KNOWLEDGE DOCUMENTS:
{rag_context}

QUESTION:
{query}

ANSWER:
"""

            answer = generate_answer(prompt)

            data_sources = [
                {
                    "type": "postgresql",
                    "label": "Structured supplier data",
                }
            ]

            if documents:
                data_sources.append(
                    {
                        "type": "pgvector",
                        "label": "Semantic knowledge documents",
                    }
                )

            return {
                "answer": answer,
                "sources": [
                    {
                        "id": doc["id"],
                        "title": doc["title"],
                        "source": doc["source"],
                        "similarity": doc["similarity"],
                    }
                    for doc in documents
                ],
                "data_sources": data_sources,
            }

    except Exception:
        RAG_ERRORS_TOTAL.inc()
        raise
