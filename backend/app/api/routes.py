from __future__ import annotations

from datetime import date, timedelta

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.agents.cost_analyzer import analyze_costs
from app.core.config import settings
from app.models.schemas import (
    AIRecommendation,
    CloudProvider,
    CostAnomaly,
    CostSummary,
    DailyCost,
    GenerateResponse,
    HealthResponse,
    OptimizationStats,
    RecommendationStatus,
    RecommendationUpdate,
    SyncResponse,
)
from app.services import aws_costs, gcp_costs, storage

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Cost endpoints
# ---------------------------------------------------------------------------

@router.get("/costs/summary", response_model=CostSummary)
async def cost_summary(
    provider: CloudProvider = Query(CloudProvider.AWS),
    period: int = Query(30, ge=1, le=365, description="Number of days"),
) -> CostSummary:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=period - 1)
    return await storage.get_cost_summary(provider, start, end)


@router.get("/costs/daily", response_model=list[DailyCost])
async def daily_costs(
    provider: CloudProvider | None = Query(None),
    days: int = Query(30, ge=1, le=365),
) -> list[DailyCost]:
    return await storage.get_daily_costs(provider, days)


@router.post("/costs/sync", response_model=SyncResponse)
async def sync_costs() -> SyncResponse:
    """Pull latest cost data from cloud providers and store it."""
    total = 0
    providers: list[str] = []

    # Fetch AWS
    try:
        aws_records = await aws_costs.fetch_aws_costs()
        count = await storage.upsert_cost_records(aws_records)
        total += count
        providers.append("aws")
        logger.info("sync.aws.complete", records=count)
    except Exception as exc:
        logger.error("sync.aws.failed", error=str(exc))

    # Fetch GCP
    try:
        gcp_records = await gcp_costs.fetch_gcp_costs()
        count = await storage.upsert_cost_records(gcp_records)
        total += count
        providers.append("gcp")
        logger.info("sync.gcp.complete", records=count)
    except Exception as exc:
        logger.error("sync.gcp.failed", error=str(exc))

    return SyncResponse(
        records_synced=total,
        providers=providers,
        message=f"Synced {total} cost records from {', '.join(providers) or 'no providers'}.",
    )


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@router.get("/recommendations", response_model=list[AIRecommendation])
async def list_recommendations() -> list[AIRecommendation]:
    return await storage.get_recommendations()


@router.post("/recommendations/generate", response_model=GenerateResponse)
async def generate_recommendations() -> GenerateResponse:
    """Run the AI cost analysis pipeline on stored data."""
    records = await storage.get_cost_records()
    if not records:
        raise HTTPException(
            status_code=400,
            detail="No cost data available. Run /costs/sync first.",
        )

    recommendations, anomalies = await analyze_costs(records)

    rec_count = await storage.save_recommendations(recommendations)
    anom_count = await storage.save_anomalies(anomalies)

    return GenerateResponse(
        recommendations_count=rec_count,
        anomalies_count=anom_count,
        message=f"Generated {rec_count} recommendations and detected {anom_count} anomalies.",
    )


@router.patch("/recommendations/{rec_id}", response_model=AIRecommendation)
async def update_recommendation(
    rec_id: str,
    body: RecommendationUpdate,
) -> AIRecommendation:
    updated = await storage.update_recommendation_status(rec_id, body.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return updated


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

@router.get("/anomalies", response_model=list[CostAnomaly])
async def list_anomalies() -> list[CostAnomaly]:
    return await storage.get_anomalies()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=OptimizationStats)
async def optimization_stats() -> OptimizationStats:
    return await storage.get_optimization_stats()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        demo_mode=settings.demo_mode,
        providers={
            "aws": settings.aws_configured,
            "gcp": settings.gcp_configured,
            "supabase": settings.supabase_configured,
            "openai": settings.openai_configured,
        },
    )
