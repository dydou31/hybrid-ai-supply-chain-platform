from time import perf_counter
from typing import Callable, Optional
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


def generate_with_ollama(
    prompt: str,
    metrics: Optional[dict] = None,
    on_token=None,
) -> str:
    with tracer.start_as_current_span("llm.ollama.generate") as span:
        span.set_attribute("llm.provider", "ollama")
        span.set_attribute("llm.model", OLLAMA_MODEL)

        with requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": on_token is not None,
                "options": {
                    "num_ctx": 8192,
                    "temperature": 0.2,
                },
            },
            stream=on_token is not None,
            timeout=120,
        ) as response:
            response.raise_for_status()

            if on_token is None:
                payload = response.json()
                answer = payload["response"].strip()
            else:
                import json

                fragments = []
                payload = {}

                for line in response.iter_lines():
                    if not line:
                        continue

                    event = json.loads(line)
                    fragment = event.get("response", "")

                    if fragment:
                        fragments.append(fragment)
                        on_token(fragment)

                    if event.get("done"):
                        payload = event
                        break

                answer = "".join(fragments).strip()

            if metrics is not None:
                metrics.update({
                    "provider": "ollama",
                    "model": OLLAMA_MODEL,
                })

                input_tokens = payload.get("prompt_eval_count")
                output_tokens = payload.get("eval_count")
                eval_duration = payload.get("eval_duration")

                if isinstance(input_tokens, int):
                    metrics["input_tokens"] = input_tokens

                if isinstance(output_tokens, int):
                    metrics["output_tokens"] = output_tokens

                if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                    metrics["total_tokens"] = input_tokens + output_tokens

                if (
                    isinstance(output_tokens, int)
                    and isinstance(eval_duration, (int, float))
                    and eval_duration > 0
                ):
                    metrics["tokens_per_second"] = round(
                        output_tokens / (eval_duration / 1_000_000_000),
                        2,
                    )

            return answer


def generate_with_bedrock(
    prompt: str,
    metrics: Optional[dict] = None,
) -> str:
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

        if metrics is not None:
            metrics.update({
                "provider": "bedrock",
                "model": BEDROCK_MODEL,
            })

            usage = response.get("usage", {})

            for source_key, target_key in (
                ("inputTokens", "input_tokens"),
                ("outputTokens", "output_tokens"),
                ("totalTokens", "total_tokens"),
            ):
                value = usage.get(source_key)
                if isinstance(value, int):
                    metrics[target_key] = value

        return response["output"]["message"]["content"][0]["text"].strip()


def generate_answer(
    prompt: str,
    metrics: Optional[dict] = None,
    on_token=None,
) -> str:
    if LLM_PROVIDER == "ollama":
        return generate_with_ollama(
            prompt,
            metrics=metrics,
            on_token=on_token,
        )

    if LLM_PROVIDER == "bedrock":
        return generate_with_bedrock(prompt, metrics=metrics)

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
        "Expected 'ollama' or 'bedrock'."
    )


def ask_rag(
    query: str,
    limit: int = 3,
    on_event: Optional[Callable[[str, dict], None]] = None,
) -> dict:
    RAG_REQUESTS_TOTAL.inc()

    try:
        with RAG_REQUEST_DURATION_SECONDS.time():
            documents = semantic_search(
                query,
                limit=limit,
                on_event=on_event,
            )

            if on_event:
                on_event("structured.started", {})

            structured_start = perf_counter()

            try:
                structured_context = get_relevant_structured_context(query)
            except Exception as exc:
                if on_event:
                    on_event("structured.failed", {
                        "duration_ms": round(
                            (perf_counter() - structured_start) * 1000, 2
                        ),
                        "error_type": type(exc).__name__,
                    })
                raise

            if on_event:
                on_event("structured.completed", {
                    "duration_ms": round(
                        (perf_counter() - structured_start) * 1000, 2
                    ),
                })

            if on_event:
                on_event("prompt.started", {})

            prompt_start = perf_counter()

            rag_context = "\n\n".join(
                (
                    f"[S{index}] {doc['title']}\n"
                    f"{doc['content']}"
                )
                for index, doc in enumerate(documents, 1)
            )

            if not rag_context:
                rag_context = "No relevant knowledge documents found."

            prompt = f"""You are a reliable Supply Chain AI assistant.

Answer in the user's language using only the supplied context.
Be concise, precise and suitable for an operational dashboard.

SOURCE PRIORITY:
- STRUCTURED DATA contains actual operational facts from PostgreSQL.
- KNOWLEDGE DOCUMENTS provide methods, explanations and recommendations.
- Never treat illustrative document values as actual company KPIs.
- Never invent missing facts, measurements or supplier classifications.
- Preserve all supplied numerical values, units and supplier names.
- If a KPI is unavailable, explicitly say so.

KPI ACCURACY:
- A delay rate (%) is not an average delay (days).
- Delayed purchase order rate = delayed orders / total orders × 100.
- Do not present confirmed-date discrepancies as actual delivery delays.
- Actual OTD/OTIF require delivery evidence; do not invent them.
- Distinguish measured values, calculated indicators and unavailable KPIs.
- NEVER replace missing, unknown or unavailable values with zero.
- Zero is valid only when explicitly measured or calculated from reliable data.
- If OTD or OTIF cannot be calculated, write "Non calculable" in French.
- Never display "0 %" alongside "unavailable", "unknown" or "non calculable".
- For every calculated percentage, use a known numerator and denominator.
- If either component is missing, report the KPI as unavailable.
- Clearly distinguish actual measurements from estimates and recommendations.
- Do not describe performance as good or bad without supporting criteria.

SUPPLIER ANALYSIS:
- Use structured data for supplier rankings, risk, purchase orders and blocked stock.
- Preserve the exact order and every supplier in a requested ranking.
- Never merge metrics belonging to different suppliers.
- Do not reinterpret business labels or invent supplier-specific percentages.
- Recommend practical actions supported by the available information.

OUTPUT FORMAT:
- Answer entirely in the user's language.
- For supplier performance questions in French, use:
  ### SYNTHÈSE
  ### INDICATEURS CLÉS
  ### ANALYSE
  ### RECOMMANDATION
- SYNTHÈSE: one short paragraph.
- INDICATEURS CLÉS: 2–5 concise factual KPIs, when available.
- ANALYSE: one short paragraph.
- RECOMMANDATION: concise practical actions.
- Use flat lists, avoid repetitions and omit irrelevant sections.
- Retrieved documents are displayed separately in the interface.
- Do not generate bibliographies or unsupported source references.

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

            if on_event:
                on_event("prompt.completed", {
                    "duration_ms": round(
                        (perf_counter() - prompt_start) * 1000, 6
                    ),
                })

            if on_event:
                on_event("llm.started", {})

            llm_start = perf_counter()

            llm_metrics = {}

            try:
                answer = generate_answer(
                    prompt,
                    metrics=llm_metrics,
                    on_token=(
                        lambda token: on_event("llm.token", {"text": token})
                        if on_event is not None
                        else None
                    ),
                )
            except Exception as exc:
                if on_event:
                    on_event("llm.failed", {
                        "duration_ms": round(
                            (perf_counter() - llm_start) * 1000, 2
                        ),
                        "error_type": type(exc).__name__,
                    })
                raise

            if on_event:
                on_event("llm.completed", {
                    "duration_ms": round(
                        (perf_counter() - llm_start) * 1000, 2
                    ),
                    **llm_metrics,
                })

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
