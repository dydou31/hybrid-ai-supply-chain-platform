import asyncio
import json
import queue
import threading
from time import perf_counter_ns

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from opentelemetry import context as otel_context, trace
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.service import ask_rag
from app.ai.models import KnowledgeDocument
from app.database import get_db

router = APIRouter(prefix="/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(request: AskRequest):
    return ask_rag(request.question)



@router.post("/ask/stream")
def ask_stream(request: AskRequest, http_request: Request):
    start_ns = http_request.scope.get("ai_request_start_ns")
    request_processing_ms = (
        (perf_counter_ns() - start_ns) / 1_000_000
        if start_ns is not None
        else None
    )

    """Stream actual RAG execution events over SSE."""

    events = queue.Queue()
    parent_context = otel_context.get_current()

    def emit(name: str, payload: dict):
        events.put({
            "event": name,
            "data": payload,
        })

    def worker():
        token = otel_context.attach(parent_context)

        try:
            span = trace.get_current_span()
            span_context = span.get_span_context()

            trace_id = (
                format(span_context.trace_id, "032x")
                if span_context.is_valid
                else None
            )

            request_start_ns = perf_counter_ns()

            emit("request.started", {"trace_id": trace_id})

            # Measured from ASGI entry to FastAPI endpoint entry.
            question = request.question

            emit("request.prepared", {
                "duration_ms": (
                    round(request_processing_ms, 6)
                    if request_processing_ms is not None
                    else None
                ),
            })

            result = ask_rag(
                question,
                on_event=emit,
            )

            duration_ms = (perf_counter_ns() - request_start_ns) / 1_000_000

            emit("request.completed", {
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 4),
                "result": result,
            })

        except Exception as exc:
            emit("request.failed", {
                "error_type": type(exc).__name__,
                "message": "RAG execution failed.",
            })

        finally:
            otel_context.detach(token)
            events.put(None)

    async def event_stream():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        loop = asyncio.get_running_loop()
        next_heartbeat = loop.time() + 1.0

        while True:
            try:
                item = events.get_nowait()
            except queue.Empty:
                now = loop.time()

                if now >= next_heartbeat:
                    yield ": heartbeat\n\n"
                    next_heartbeat = now + 1.0

                await asyncio.sleep(0.1)
                continue

            if item is None:
                break

            yield (
                f"event: {item['event']}\n"
                f"data: {json.dumps(item['data'], ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/knowledge/count")
def knowledge_count(db: Session = Depends(get_db)):
    count = db.query(KnowledgeDocument).count()
    return {"count": count}
