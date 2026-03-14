from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import structlog

from app.core.config import settings
from app.models.schemas import (
    AIRecommendation,
    CloudProvider,
    CostAnomaly,
    CostRecord,
    CostSummary,
    DailyCost,
    OptimizationStats,
    RecommendationStatus,
    ServiceCost,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# In-memory fallback store (used when Supabase is not configured)
# ---------------------------------------------------------------------------

class _InMemoryStore:
    def __init__(self) -> None:
        self.cost_records: list[CostRecord] = []
        self.recommendations: list[AIRecommendation] = []
        self.anomalies: list[CostAnomaly] = []

    def clear_costs(self) -> None:
        self.cost_records.clear()

    def clear_recommendations(self) -> None:
        self.recommendations.clear()

    def clear_anomalies(self) -> None:
        self.anomalies.clear()


_mem = _InMemoryStore()


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def _get_supabase():  # type: ignore[no-untyped-def]
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_key)


# ---------------------------------------------------------------------------
# Cost records
# ---------------------------------------------------------------------------

async def upsert_cost_records(records: list[CostRecord]) -> int:
    """Insert or update cost records.  Returns the number of rows written."""
    if not records:
        return 0

    if not settings.supabase_configured:
        _mem.cost_records.extend(records)
        logger.info("storage.in_memory.upsert_costs", count=len(records))
        return len(records)

    client = _get_supabase()
    rows = [r.model_dump(mode="json") for r in records]
    # Supabase upsert on (cloud_provider, service_name, usage_date)
    client.table("cost_records").upsert(rows, on_conflict="id").execute()
    logger.info("storage.supabase.upsert_costs", count=len(rows))
    return len(rows)


async def get_cost_records(
    provider: CloudProvider | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[CostRecord]:
    if not settings.supabase_configured:
        results = _mem.cost_records
        if provider:
            results = [r for r in results if r.cloud_provider == provider]
        if start:
            results = [r for r in results if r.usage_date >= start]
        if end:
            results = [r for r in results if r.usage_date <= end]
        return results

    client = _get_supabase()
    query = client.table("cost_records").select("*")
    if provider:
        query = query.eq("cloud_provider", provider.value)
    if start:
        query = query.gte("usage_date", start.isoformat())
    if end:
        query = query.lte("usage_date", end.isoformat())
    query = query.order("usage_date", desc=True)
    resp = query.execute()
    return [CostRecord(**row) for row in resp.data]


# ---------------------------------------------------------------------------
# Summaries (computed from stored records)
# ---------------------------------------------------------------------------

async def get_cost_summary(
    provider: CloudProvider,
    start: date,
    end: date,
) -> CostSummary:
    records = await get_cost_records(provider=provider, start=start, end=end)

    total = sum(r.cost_amount for r in records)

    # top services
    svc_totals: dict[str, float] = defaultdict(float)
    for r in records:
        svc_totals[r.service_name] += r.cost_amount
    sorted_svcs = sorted(svc_totals.items(), key=lambda x: x[1], reverse=True)
    top_services = [
        ServiceCost(
            service_name=name,
            cost=round(cost, 2),
            percentage=round(cost / total * 100, 1) if total else 0.0,
        )
        for name, cost in sorted_svcs[:10]
    ]

    # daily costs
    daily_totals: dict[date, float] = defaultdict(float)
    for r in records:
        daily_totals[r.usage_date] += r.cost_amount
    daily_costs = [
        DailyCost(date=d, cost=round(c, 2))
        for d, c in sorted(daily_totals.items())
    ]

    return CostSummary(
        provider=provider,
        total_cost=round(total, 2),
        period_start=start,
        period_end=end,
        top_services=top_services,
        daily_costs=daily_costs,
    )


async def get_daily_costs(
    provider: CloudProvider | None,
    days: int,
) -> list[DailyCost]:
    end = date.today()
    start = end - timedelta(days=days)
    records = await get_cost_records(provider=provider, start=start, end=end)

    daily: dict[date, float] = defaultdict(float)
    for r in records:
        daily[r.usage_date] += r.cost_amount
    return [DailyCost(date=d, cost=round(c, 2)) for d, c in sorted(daily.items())]


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

async def save_recommendations(recs: list[AIRecommendation]) -> int:
    if not recs:
        return 0

    if not settings.supabase_configured:
        _mem.recommendations.extend(recs)
        return len(recs)

    client = _get_supabase()
    rows = [r.model_dump(mode="json") for r in recs]
    client.table("recommendations").upsert(rows, on_conflict="id").execute()
    return len(rows)


async def get_recommendations() -> list[AIRecommendation]:
    if not settings.supabase_configured:
        return list(_mem.recommendations)

    client = _get_supabase()
    resp = (
        client.table("recommendations")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return [AIRecommendation(**row) for row in resp.data]


async def update_recommendation_status(
    rec_id: str,
    status: RecommendationStatus,
) -> AIRecommendation | None:
    if not settings.supabase_configured:
        for rec in _mem.recommendations:
            if rec.id == rec_id:
                rec.status = status
                return rec
        return None

    client = _get_supabase()
    resp = (
        client.table("recommendations")
        .update({"status": status.value})
        .eq("id", rec_id)
        .execute()
    )
    if resp.data:
        return AIRecommendation(**resp.data[0])
    return None


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

async def save_anomalies(anomalies: list[CostAnomaly]) -> int:
    if not anomalies:
        return 0

    if not settings.supabase_configured:
        _mem.anomalies.extend(anomalies)
        return len(anomalies)

    client = _get_supabase()
    rows = [a.model_dump(mode="json") for a in anomalies]
    client.table("anomalies").upsert(rows, on_conflict="id").execute()
    return len(rows)


async def get_anomalies() -> list[CostAnomaly]:
    if not settings.supabase_configured:
        return list(_mem.anomalies)

    client = _get_supabase()
    resp = (
        client.table("anomalies")
        .select("*")
        .order("date", desc=True)
        .execute()
    )
    return [CostAnomaly(**row) for row in resp.data]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

async def get_optimization_stats() -> OptimizationStats:
    recs = await get_recommendations()
    anomalies = await get_anomalies()

    total_potential = sum(r.estimated_monthly_savings for r in recs if r.status == RecommendationStatus.PENDING)
    implemented = sum(r.estimated_monthly_savings for r in recs if r.status == RecommendationStatus.IMPLEMENTED)

    return OptimizationStats(
        total_potential_savings=round(total_potential, 2),
        implemented_savings=round(implemented, 2),
        recommendations_count=len(recs),
        anomalies_detected=len(anomalies),
    )
