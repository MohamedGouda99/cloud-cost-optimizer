from __future__ import annotations

import hashlib
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

_GCP_SERVICES: list[dict[str, Any]] = [
    {"name": "Compute Engine", "base": 1450, "variance": 0.18},
    {"name": "Cloud SQL", "base": 680, "variance": 0.10},
    {"name": "Cloud Storage", "base": 260, "variance": 0.14},
    {"name": "BigQuery", "base": 390, "variance": 0.28},
    {"name": "Cloud Run", "base": 175, "variance": 0.32},
    {"name": "Cloud Functions", "base": 95, "variance": 0.30},
    {"name": "Cloud Pub/Sub", "base": 55, "variance": 0.20},
    {"name": "Cloud Logging", "base": 110, "variance": 0.15},
    {"name": "Networking", "base": 200, "variance": 0.22},
    {"name": "GKE / Kubernetes Engine", "base": 520, "variance": 0.16},
    {"name": "Cloud Memorystore", "base": 180, "variance": 0.12},
    {"name": "Artifact Registry", "base": 35, "variance": 0.18},
]


def _seed_for_date(d: date) -> int:
    h = hashlib.md5(f"gcp-{d.isoformat()}".encode()).hexdigest()
    return int(h[:8], 16)


def _generate_demo_records(start: date, end: date) -> list[CostRecord]:
    records: list[CostRecord] = []
    current = start
    while current <= end:
        rng = random.Random(_seed_for_date(current))
        day_of_week = current.weekday()
        weekend_factor = 0.72 if day_of_week >= 5 else 1.0
        days_offset = (current - date(2024, 1, 1)).days
        growth_factor = 1.0 + 0.0018 * max(days_offset, 0)
        spike = 1.55 if rng.random() < 0.04 else 1.0

        for svc in _GCP_SERVICES:
            daily_base = svc["base"] / 30.0
            noise = rng.gauss(0, svc["variance"] * daily_base)
            cost = max(0.01, daily_base * weekend_factor * growth_factor * spike + noise)
            cost = round(cost, 2)

            records.append(
                CostRecord(
                    cloud_provider=CloudProvider.GCP,
                    service_name=svc["name"],
                    cost_amount=cost,
                    currency="USD",
                    usage_date=current,
                    project_id="demo-project-123",
                    tags={"environment": "production", "team": "data"},
                )
            )
        current += timedelta(days=1)
    return records


# ---------------------------------------------------------------------------
# Real GCP BigQuery billing client
# ---------------------------------------------------------------------------

def _fetch_real_gcp_costs(start: date, end: date) -> list[CostRecord]:
    from google.cloud import bigquery

    client = bigquery.Client(project=settings.gcp_project_id)

    query = f"""
        SELECT
            service.description AS service_name,
            DATE(usage_start_time) AS usage_date,
            project.id AS project_id,
            SUM(cost) AS total_cost,
            currency
        FROM `{settings.gcp_project_id}.{settings.gcp_billing_dataset}.gcp_billing_export_v1_*`
        WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
            AND cost > 0
        GROUP BY service_name, usage_date, project_id, currency
        ORDER BY usage_date, total_cost DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start.isoformat()),
            bigquery.ScalarQueryParameter("end_date", "DATE", end.isoformat()),
        ]
    )

    results = client.query(query, job_config=job_config).result()

    records: list[CostRecord] = []
    for row in results:
        records.append(
            CostRecord(
                cloud_provider=CloudProvider.GCP,
                service_name=row.service_name,
                cost_amount=round(float(row.total_cost), 2),
                currency=row.currency or "USD",
                usage_date=row.usage_date,
                project_id=row.project_id,
            )
        )
    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_gcp_costs(
    start: date | None = None,
    end: date | None = None,
) -> list[CostRecord]:
    """Fetch GCP cost records.  Falls back to demo data when creds are absent."""
    if end is None:
        end = date.today() - timedelta(days=1)
    if start is None:
        start = end - timedelta(days=29)

    if not settings.gcp_configured:
        logger.info("gcp.demo_mode", start=str(start), end=str(end))
        return _generate_demo_records(start, end)

    try:
        logger.info("gcp.fetching", start=str(start), end=str(end))
        return _fetch_real_gcp_costs(start, end)
    except Exception as exc:
        logger.error("gcp.fetch_failed", error=str(exc))
        logger.info("gcp.falling_back_to_demo")
        return _generate_demo_records(start, end)
