from __future__ import annotations

import hashlib
import math
import random
from datetime import date, timedelta
from typing import Any

import structlog

from app.core.config import settings
from app.models.schemas import CloudProvider, CostRecord

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Realistic demo data
# ---------------------------------------------------------------------------

_AWS_SERVICES: list[dict[str, Any]] = [
    {"name": "Amazon EC2", "base": 1800, "variance": 0.20},
    {"name": "Amazon RDS", "base": 920, "variance": 0.12},
    {"name": "Amazon S3", "base": 340, "variance": 0.15},
    {"name": "AWS Lambda", "base": 210, "variance": 0.30},
    {"name": "Amazon CloudFront", "base": 180, "variance": 0.18},
    {"name": "Amazon DynamoDB", "base": 150, "variance": 0.22},
    {"name": "Amazon ECS", "base": 420, "variance": 0.14},
    {"name": "Amazon ElastiCache", "base": 280, "variance": 0.10},
    {"name": "AWS Data Transfer", "base": 130, "variance": 0.25},
    {"name": "Amazon SQS", "base": 45, "variance": 0.35},
    {"name": "Amazon SNS", "base": 25, "variance": 0.20},
    {"name": "AWS CloudWatch", "base": 90, "variance": 0.15},
]


def _seed_for_date(d: date) -> int:
    """Deterministic seed so the same date always produces the same data."""
    h = hashlib.md5(f"aws-{d.isoformat()}".encode()).hexdigest()
    return int(h[:8], 16)


def _generate_demo_records(start: date, end: date) -> list[CostRecord]:
    records: list[CostRecord] = []
    current = start
    while current <= end:
        rng = random.Random(_seed_for_date(current))
        day_of_week = current.weekday()
        # weekends have ~30% less traffic
        weekend_factor = 0.70 if day_of_week >= 5 else 1.0
        # slight monthly growth trend
        days_offset = (current - date(2024, 1, 1)).days
        growth_factor = 1.0 + 0.002 * max(days_offset, 0)
        # occasional spike (roughly 1 in 20 days)
        spike = 1.6 if rng.random() < 0.05 else 1.0

        for svc in _AWS_SERVICES:
            daily_base = svc["base"] / 30.0
            noise = rng.gauss(0, svc["variance"] * daily_base)
            cost = max(0.01, daily_base * weekend_factor * growth_factor * spike + noise)
            cost = round(cost, 2)

            records.append(
                CostRecord(
                    cloud_provider=CloudProvider.AWS,
                    service_name=svc["name"],
                    cost_amount=cost,
                    currency="USD",
                    usage_date=current,
                    account_id="123456789012",
                    tags={"environment": "production", "team": "platform"},
                )
            )
        current += timedelta(days=1)
    return records


# ---------------------------------------------------------------------------
# Real AWS Cost Explorer client
# ---------------------------------------------------------------------------

def _fetch_real_aws_costs(start: date, end: date) -> list[CostRecord]:
    import boto3  # deferred import so demo mode works without boto3 configured

    client = boto3.client(
        "ce",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )

    records: list[CostRecord] = []
    next_token: str | None = None

    while True:
        kwargs: dict[str, Any] = {
            "TimePeriod": {
                "Start": start.isoformat(),
                "End": end.isoformat(),
            },
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if next_token:
            kwargs["NextPageToken"] = next_token

        response = client.get_cost_and_usage(**kwargs)

        for result_by_time in response.get("ResultsByTime", []):
            usage_date = date.fromisoformat(result_by_time["TimePeriod"]["Start"])
            for group in result_by_time.get("Groups", []):
                service_name = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount <= 0:
                    continue
                records.append(
                    CostRecord(
                        cloud_provider=CloudProvider.AWS,
                        service_name=service_name,
                        cost_amount=round(amount, 2),
                        currency="USD",
                        usage_date=usage_date,
                        account_id=settings.aws_access_key_id[:12],
                    )
                )

        next_token = response.get("NextPageToken")
        if not next_token:
            break

    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_aws_costs(
    start: date | None = None,
    end: date | None = None,
) -> list[CostRecord]:
    """Fetch AWS cost records.  Falls back to demo data when creds are absent."""
    if end is None:
        end = date.today() - timedelta(days=1)
    if start is None:
        start = end - timedelta(days=29)

    if not settings.aws_configured:
        logger.info("aws.demo_mode", start=str(start), end=str(end))
        return _generate_demo_records(start, end)

    try:
        logger.info("aws.fetching", start=str(start), end=str(end))
        return _fetch_real_aws_costs(start, end)
    except Exception as exc:
        logger.error("aws.fetch_failed", error=str(exc))
        logger.info("aws.falling_back_to_demo")
        return _generate_demo_records(start, end)
