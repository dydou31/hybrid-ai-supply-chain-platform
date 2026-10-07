from prometheus_client import Counter, Histogram, Gauge

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


AWS_COST_MTD_USD = Gauge(
    "aws_cost_mtd_usd",
    "AWS month-to-date unblended cost in USD",
)

AWS_COST_DAILY_USD = Gauge(
    "aws_cost_daily_usd",
    "Latest available AWS daily unblended cost in USD",
)

AWS_COST_MONTHLY_FORECAST_USD = Gauge(
    "aws_cost_monthly_forecast_usd",
    "Projected AWS monthly cost in USD based on current daily burn rate",
)

AWS_COST_BY_SERVICE_USD = Gauge(
    "aws_cost_by_service_usd",
    "AWS month-to-date unblended cost in USD by service",
    ["service"],
)

AWS_FINOPS_LAST_REFRESH_TIMESTAMP = Gauge(
    "aws_finops_last_refresh_timestamp",
    "Unix timestamp of the latest successful AWS FinOps metrics refresh",
)

AWS_COST_GROSS_MTD_USD = Gauge(
    "aws_cost_gross_mtd_usd",
    "AWS month-to-date usage cost before credits in USD",
)

AWS_CREDITS_MTD_USD = Gauge(
    "aws_credits_mtd_usd",
    "AWS month-to-date credits applied in USD",
)

AWS_CREDITS_REMAINING_USD = Gauge(
    "aws_credits_remaining_usd",
    "AWS credits remaining balance in USD",
)
