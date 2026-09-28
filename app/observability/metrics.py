from prometheus_client import Counter, Histogram

RAG_REQUESTS_TOTAL = Counter(
    "rag_requests_total",
    "Total number of RAG requests"
)

RAG_ERRORS_TOTAL = Counter(
    "rag_errors_total",
    "Total number of failed RAG requests"
)

RAG_REQUEST_DURATION_SECONDS = Histogram(
    "rag_request_duration_seconds",
    "RAG request processing time in seconds"
)
