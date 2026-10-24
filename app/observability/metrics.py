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

AWS_COST_DAILY_BY_DATE_USD = Gauge(
    "aws_cost_daily_by_date_usd",
    "AWS daily gross usage cost before credits in USD",
    ["date"],
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

AWS_CREDITS_USED_CONFIRMED_USD = Gauge(
    "aws_credits_used_confirmed_usd",
    "AWS credits actually consumed based on confirmed balances in USD",
)

AWS_CREDITS_USED_ESTIMATED_USD = Gauge(
    "aws_credits_used_estimated_usd",
    "AWS estimated credits consumed in USD",
)

AWS_CREDITS_REMAINING_ESTIMATED_USD = Gauge(
    "aws_credits_remaining_estimated_usd",
    "AWS estimated remaining credits in USD",
)

AWS_CREDITS_REMAINING_USD = Gauge(
    "aws_credits_remaining_usd",
    "AWS credits remaining balance in USD",
)


# AWS Billing — persistent data freshness monitoring

AWS_BILLING_LAST_CHANGE_DETECTED_TIMESTAMP = Gauge(
    "aws_billing_last_change_detected_timestamp_seconds",
    "Timestamp when a change in AWS Billing data was last detected",
)

AWS_BILLING_LAST_SUCCESSFUL_CHECK_TIMESTAMP = Gauge(
    "aws_billing_last_successful_check_timestamp_seconds",
    "Timestamp of the last successful AWS Billing collection",
)

AWS_BILLING_DATA_ESTIMATED = Gauge(
    "aws_billing_data_estimated",
    "Whether AWS Billing data is estimated: 1=yes, 0=no",
)
