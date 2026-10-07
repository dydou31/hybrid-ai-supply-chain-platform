import calendar
import logging
import os
import threading
import time
from datetime import date, timedelta

import boto3

from app.observability.metrics import (
    AWS_COST_BY_SERVICE_USD,
    AWS_COST_DAILY_USD,
    AWS_COST_GROSS_MTD_USD,
    AWS_COST_MONTHLY_FORECAST_USD,
    AWS_COST_MTD_USD,
    AWS_CREDITS_MTD_USD,
    AWS_CREDITS_REMAINING_USD,
    AWS_FINOPS_LAST_REFRESH_TIMESTAMP,
)

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 3600


def _get_cost_data(client, start: date, end: date, **kwargs):
    return client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat(),
        },
        Metrics=["UnblendedCost"],
        **kwargs,
    )


def _refresh_finops_metrics() -> None:
    client = boto3.client("ce", region_name="us-east-1")
    billing_client = boto3.client("billing", region_name="us-east-1")

    today = date.today()
    month_start = today.replace(day=1)
    tomorrow = today + timedelta(days=1)

    # Gross usage cost by service and by day.
    usage_response = _get_cost_data(
        client,
        month_start,
        tomorrow,
        Granularity="DAILY",
        Filter={
            "Dimensions": {
                "Key": "RECORD_TYPE",
                "Values": ["Usage"],
            }
        },
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            }
        ],
    )

    gross_total = 0.0
    service_costs = {}
    daily_totals = []

    for period in usage_response.get("ResultsByTime", []):
        daily_total = 0.0

        for group in period.get("Groups", []):
            amount = float(
                group["Metrics"]["UnblendedCost"]["Amount"]
            )

            service = group["Keys"][0]

            service_costs[service] = (
                service_costs.get(service, 0.0) + amount
            )

            daily_total += amount
            gross_total += amount

        daily_totals.append(daily_total)

    # Net cost and credits for the month.
    billing_response = _get_cost_data(
        client,
        month_start,
        tomorrow,
        Granularity="MONTHLY",
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "RECORD_TYPE",
            }
        ],
    )

    net_total = 0.0
    credits = 0.0

    for period in billing_response.get("ResultsByTime", []):
        for group in period.get("Groups", []):
            amount = float(
                group["Metrics"]["UnblendedCost"]["Amount"]
            )

            record_type = group["Keys"][0]
            net_total += amount

            if record_type == "Credit":
                credits += abs(amount)

    account_id = boto3.client("sts").get_caller_identity()["Account"]

    credits_response = billing_client.get_credits(
        accountId=account_id,
        startDate=int(
            time.mktime(
                today.replace(month=1, day=1).timetuple()
            )
        ),
    )

    credits_remaining = sum(
        float(
            credit.get("remainingAmount", {}).get(
                "currencyAmount",
                0.0,
            )
        )
        for credit in credits_response.get("credits", [])
    )

    AWS_COST_BY_SERVICE_USD.clear()

    for service, amount in service_costs.items():
        AWS_COST_BY_SERVICE_USD.labels(
            service=service
        ).set(amount)

    AWS_COST_GROSS_MTD_USD.set(gross_total)
    AWS_CREDITS_MTD_USD.set(credits)
    AWS_CREDITS_REMAINING_USD.set(credits_remaining)
    AWS_COST_MTD_USD.set(net_total)

    latest_daily = daily_totals[-1] if daily_totals else 0.0
    AWS_COST_DAILY_USD.set(latest_daily)

    elapsed_days = max(today.day, 1)
    days_in_month = calendar.monthrange(
        today.year,
        today.month,
    )[1]

    forecast = (
        gross_total / elapsed_days
    ) * days_in_month

    AWS_COST_MONTHLY_FORECAST_USD.set(forecast)
    AWS_FINOPS_LAST_REFRESH_TIMESTAMP.set(time.time())

    logger.info(
        (
            "FinOps metrics refreshed: "
            "gross=$%.4f credits=$%.4f "
            "net=$%.4f daily=$%.4f forecast=$%.4f"
        ),
        gross_total,
        credits,
        net_total,
        latest_daily,
        forecast,
    )


def _collector_loop() -> None:
    while True:
        try:
            _refresh_finops_metrics()
        except Exception:
            logger.exception(
                "Unable to refresh AWS FinOps metrics"
            )

        time.sleep(REFRESH_SECONDS)


def start_finops_collector() -> None:
    # Cloud deployment uses Bedrock; local development uses Ollama.
    if os.getenv(
        "LLM_PROVIDER",
        "ollama",
    ).lower() != "bedrock":
        logger.info(
            "FinOps collector disabled outside AWS deployment"
        )
        return

    thread = threading.Thread(
        target=_collector_loop,
        name="finops-collector",
        daemon=True,
    )
    thread.start()
