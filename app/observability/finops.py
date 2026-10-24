import calendar
import hashlib
import json
import logging
import os
import threading
import time
from datetime import date, timedelta

import boto3
from botocore.exceptions import ClientError

from app.observability.metrics import (
    AWS_BILLING_DATA_ESTIMATED,
    AWS_BILLING_LAST_SUCCESSFUL_CHECK_TIMESTAMP,
    AWS_BILLING_LAST_CHANGE_DETECTED_TIMESTAMP,
    AWS_COST_BY_SERVICE_USD,
    AWS_COST_DAILY_USD,
    AWS_COST_DAILY_BY_DATE_USD,
    AWS_COST_GROSS_MTD_USD,
    AWS_COST_MONTHLY_FORECAST_USD,
    AWS_COST_MTD_USD,
    AWS_CREDITS_MTD_USD,
    AWS_CREDITS_REMAINING_USD,
    AWS_CREDITS_USED_CONFIRMED_USD,
    AWS_CREDITS_USED_ESTIMATED_USD,
    AWS_CREDITS_REMAINING_ESTIMATED_USD,
    AWS_FINOPS_LAST_REFRESH_TIMESTAMP,
)

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 3600
FINOPS_STATE_TABLE = os.getenv(
    "FINOPS_STATE_TABLE", "hybrid-ai-finops-state"
)


def _get_cost_data(client, start: date, end: date, **kwargs):
    return client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat(),
        },
        Metrics=["UnblendedCost"],
        **kwargs,
    )


def _update_billing_change_state(snapshot: dict) -> float:
    """Detect Billing changes while ignoring calendar-period transitions."""
    fingerprint = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    period_start = snapshot["period_start"]

    table = boto3.resource(
        "dynamodb", region_name="eu-west-3"
    ).Table(FINOPS_STATE_TABLE)

    now = int(time.time())
    key = {"StateID": "billing"}

    for _ in range(5):
        previous = table.get_item(
            Key=key,
            ConsistentRead=True,
        ).get("Item")

        if previous:
            old_fingerprint = previous.get("Fingerprint")
            old_period = previous.get("PeriodStart")
            last_change = int(previous.get("LastChange", 0))

            if old_fingerprint == fingerprint:
                return float(last_change)

            # A calendar-period transition is not a Billing update.
            new_last_change = (
                0 if old_period != period_start else now
            )

            condition = "Fingerprint = :old"
            values = {
                ":fingerprint": fingerprint,
                ":period": period_start,
                ":last_change": new_last_change,
                ":old": old_fingerprint,
            }
        else:
            new_last_change = 0
            condition = "attribute_not_exists(StateID)"
            values = {
                ":fingerprint": fingerprint,
                ":period": period_start,
                ":last_change": new_last_change,
            }

        try:
            table.update_item(
                Key=key,
                UpdateExpression=(
                    "SET Fingerprint = :fingerprint, "
                    "PeriodStart = :period, "
                    "LastChange = :last_change"
                ),
                ConditionExpression=condition,
                ExpressionAttributeValues=values,
            )
            return float(new_last_change)

        except ClientError as exc:
            if exc.response["Error"]["Code"] != (
                "ConditionalCheckFailedException"
            ):
                raise

    raise RuntimeError(
        "Concurrent Billing state updates exceeded retry limit"
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
    daily_costs_by_date = {}

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
        daily_costs_by_date[period["TimePeriod"]["Start"]] = daily_total

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

    credit_entries = credits_response.get("credits", [])

    credits_initial = sum(
        float(c.get("initialAmount", {}).get("currencyAmount", 0))
        for c in credit_entries
    )

    credits_estimated_remaining = sum(
        float(c.get("estimatedAmount", {}).get("currencyAmount", 0))
        for c in credit_entries
    )

    credits_used_confirmed = max(
        credits_initial - credits_remaining, 0.0
    )

    credits_used_estimated = max(
        credits_initial - credits_estimated_remaining, 0.0
    )

    AWS_CREDITS_USED_CONFIRMED_USD.set(credits_used_confirmed)
    AWS_CREDITS_USED_ESTIMATED_USD.set(credits_used_estimated)
    AWS_CREDITS_REMAINING_ESTIMATED_USD.set(
        credits_estimated_remaining
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
    # Rolling 30-day history, independent of monthly totals.
    history_start = today - timedelta(days=29)
    history_response = _get_cost_data(
        client,
        history_start,
        tomorrow,
        Granularity="DAILY",
        Filter={
            "Dimensions": {
                "Key": "RECORD_TYPE",
                "Values": ["Usage"],
            }
        },
    )

    history_by_date = {}
    for period in history_response.get("ResultsByTime", []):
        day = period["TimePeriod"]["Start"]
        amount = float(
            period.get("Total", {})
            .get("UnblendedCost", {})
            .get("Amount", 0.0)
        )
        history_by_date[day] = amount

    AWS_COST_DAILY_BY_DATE_USD.clear()
    for day, amount in history_by_date.items():
        AWS_COST_DAILY_BY_DATE_USD.labels(date=day).set(amount)

    # Track a fixed calendar period rather than a rolling 30-day window.
    # The dashboard's rolling 30-day chart remains unchanged.
    previous_month_end = today.replace(day=1)
    previous_month_start = (
        previous_month_end - timedelta(days=1)
    ).replace(day=1)

    billing_history = _get_cost_data(
        client,
        previous_month_start,
        tomorrow,
        Granularity="DAILY",
        Filter={
            "Dimensions": {
                "Key": "RECORD_TYPE",
                "Values": ["Usage"],
            }
        },
    )

    billing_snapshot = {
        "period_start": previous_month_start.isoformat(),
        "daily_costs": {
            period["TimePeriod"]["Start"]: round(
                float(
                    period.get("Total", {})
                    .get("UnblendedCost", {})
                    .get("Amount", 0.0)
                ),
                6,
            )
            for period in billing_history.get("ResultsByTime", [])
            if period["TimePeriod"]["Start"] < today.isoformat()
        },
        "credits_remaining": round(credits_remaining, 6),
        "credits_estimated_remaining": round(
            credits_estimated_remaining, 6
        ),
    }

    last_change = _update_billing_change_state(billing_snapshot)

    AWS_BILLING_LAST_CHANGE_DETECTED_TIMESTAMP.set(last_change)
    AWS_BILLING_LAST_SUCCESSFUL_CHECK_TIMESTAMP.set(time.time())

    AWS_BILLING_DATA_ESTIMATED.set(
        1 if any(
            period.get("Estimated", False)
            for period in history_response.get("ResultsByTime", [])
        ) else 0
    )

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
