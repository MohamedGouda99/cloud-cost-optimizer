from __future__ import annotations

import json
import statistics
import uuid
from collections import defaultdict
from datetime import date, datetime
from typing import Any, TypedDict

import structlog

from app.core.config import settings
from app.models.schemas import (
    AIRecommendation,
    CloudProvider,
    CostAnomaly,
    CostRecord,
    Priority,
    RecommendationCategory,
    RecommendationStatus,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# LangGraph state schema
# ---------------------------------------------------------------------------

class AnalyzerState(TypedDict, total=False):
    cost_records: list[dict[str, Any]]
    provider_totals: dict[str, float]
    service_totals: dict[str, float]
    daily_totals: dict[str, float]
    anomalies: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    error: str | None


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def collect_data(state: AnalyzerState) -> AnalyzerState:
    """Aggregate raw cost records into provider/service/daily totals."""
    records = state["cost_records"]

    provider_totals: dict[str, float] = defaultdict(float)
    service_totals: dict[str, float] = defaultdict(float)
    daily_totals: dict[str, float] = defaultdict(float)

    for r in records:
        provider_totals[r["cloud_provider"]] += r["cost_amount"]
        key = f"{r['cloud_provider']}:{r['service_name']}"
        service_totals[key] += r["cost_amount"]
        daily_totals[r["usage_date"]] += r["cost_amount"]

    state["provider_totals"] = dict(provider_totals)
    state["service_totals"] = dict(service_totals)
    state["daily_totals"] = dict(daily_totals)
    return state


def detect_anomalies(state: AnalyzerState) -> AnalyzerState:
    """Flag days where spend deviates >2 std-devs from a 7-day moving average."""
    records = state["cost_records"]

    # group costs by (service, date)
    svc_daily: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in records:
        svc_daily[r["service_name"]][r["usage_date"]] += r["cost_amount"]

    anomalies: list[dict[str, Any]] = []

    for service, date_costs in svc_daily.items():
        sorted_dates = sorted(date_costs.keys())
        if len(sorted_dates) < 8:
            continue
        costs_list = [date_costs[d] for d in sorted_dates]

        for i in range(7, len(costs_list)):
            window = costs_list[i - 7 : i]
            mean = statistics.mean(window)
            stdev = statistics.stdev(window) if len(window) > 1 else 0
            actual = costs_list[i]
            threshold = mean + 2 * stdev if stdev > 0 else mean * 1.5

            if actual > threshold and actual > mean * 1.3:
                deviation = ((actual - mean) / mean * 100) if mean > 0 else 0
                anomalies.append(
                    {
                        "id": str(uuid.uuid4()),
                        "date": sorted_dates[i],
                        "service": service,
                        "expected_cost": round(mean, 2),
                        "actual_cost": round(actual, 2),
                        "deviation_percentage": round(deviation, 1),
                        "explanation": (
                            f"{service} cost was ${actual:.2f} on {sorted_dates[i]}, "
                            f"which is {deviation:.0f}% above the 7-day average of ${mean:.2f}."
                        ),
                    }
                )

    state["anomalies"] = anomalies
    return state


def _build_analysis_prompt(state: AnalyzerState) -> str:
    """Build a prompt that feeds spending data to the LLM."""
    # top 15 services by cost
    sorted_svcs = sorted(state["service_totals"].items(), key=lambda x: x[1], reverse=True)[:15]
    svc_lines = "\n".join(f"  - {name}: ${cost:,.2f}" for name, cost in sorted_svcs)

    anomaly_lines = ""
    if state["anomalies"]:
        top_anomalies = sorted(state["anomalies"], key=lambda a: a["deviation_percentage"], reverse=True)[:10]
        anomaly_lines = "\n".join(
            f"  - {a['service']} on {a['date']}: ${a['actual_cost']:.2f} vs expected ${a['expected_cost']:.2f} "
            f"(+{a['deviation_percentage']:.0f}%)"
            for a in top_anomalies
        )

    total_spend = sum(state["service_totals"].values())

    return f"""You are a cloud cost optimization expert. Analyze this cloud spending data and provide actionable recommendations.

TOTAL SPEND (period): ${total_spend:,.2f}

TOP SERVICES BY COST:
{svc_lines}

DETECTED ANOMALIES:
{anomaly_lines if anomaly_lines else "  None detected."}

Provide 5-8 specific optimization recommendations as a JSON array. Each item MUST have these exact fields:
- "category": one of "rightsizing", "unused_resources", "reserved_instances", "storage_optimization", "networking"
- "title": short title (max 80 chars)
- "description": 2-3 sentence explanation
- "estimated_monthly_savings": numeric dollar amount
- "confidence": float 0.0-1.0
- "priority": "high", "medium", or "low"
- "cloud_provider": "aws" or "gcp"
- "affected_resources": list of resource/service names
- "implementation_steps": list of 2-4 concrete action steps

Focus on the highest-cost services. Be specific with savings estimates (use realistic percentages of actual spend).
Return ONLY the JSON array, no other text."""


async def generate_recommendations_llm(state: AnalyzerState) -> AnalyzerState:
    """Use OpenAI via LangChain to generate optimization recommendations."""
    if not settings.openai_configured:
        return _generate_recommendations_heuristic(state)

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=4000,
        )

        prompt = _build_analysis_prompt(state)
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        recs_raw = json.loads(content)
        state["recommendations"] = recs_raw
        return state
    except Exception as exc:
        logger.error("llm.generation_failed", error=str(exc))
        return _generate_recommendations_heuristic(state)


def _generate_recommendations_heuristic(state: AnalyzerState) -> AnalyzerState:
    """Deterministic fallback when OpenAI is unavailable."""
    sorted_svcs = sorted(state["service_totals"].items(), key=lambda x: x[1], reverse=True)

    recs: list[dict[str, Any]] = []

    # Map service patterns to recommendation templates
    templates: list[dict[str, Any]] = [
        {
            "keywords": ["ec2", "compute engine"],
            "category": "rightsizing",
            "title": "Rightsize underutilized compute instances",
            "description": (
                "Analysis shows significant compute spending that likely includes oversized instances. "
                "Downsizing instances with consistently low CPU/memory utilization (<30%) can yield "
                "substantial savings without impacting performance."
            ),
            "savings_pct": 0.25,
            "confidence": 0.85,
            "priority": "high",
            "steps": [
                "Review CPU and memory utilization metrics for all instances over the past 14 days",
                "Identify instances with average utilization below 30%",
                "Schedule downsizing during next maintenance window",
                "Monitor performance metrics post-change for 48 hours",
            ],
        },
        {
            "keywords": ["ec2", "compute engine", "ecs", "gke"],
            "category": "reserved_instances",
            "title": "Purchase reserved instances for stable workloads",
            "description": (
                "Steady baseline compute usage indicates workloads suitable for 1-year reserved instances "
                "or committed use discounts, offering 30-40% savings over on-demand pricing."
            ),
            "savings_pct": 0.35,
            "confidence": 0.80,
            "priority": "high",
            "steps": [
                "Identify instances running consistently for 30+ days",
                "Calculate break-even point for 1-year vs 3-year reservations",
                "Purchase reserved capacity for baseline workload",
                "Set up monitoring for reservation utilization",
            ],
        },
        {
            "keywords": ["s3", "cloud storage", "storage"],
            "category": "storage_optimization",
            "title": "Implement storage lifecycle policies",
            "description": (
                "Storage costs can be reduced by moving infrequently accessed data to cheaper tiers "
                "(S3 Infrequent Access / Nearline) and setting expiration policies for temporary objects."
            ),
            "savings_pct": 0.30,
            "confidence": 0.78,
            "priority": "medium",
            "steps": [
                "Audit object access patterns using storage analytics",
                "Configure lifecycle rules to transition objects >90 days to cold storage",
                "Set expiration policies for log and temp buckets",
                "Enable intelligent tiering where available",
            ],
        },
        {
            "keywords": ["rds", "cloud sql", "elasticache", "memorystore", "dynamodb"],
            "category": "rightsizing",
            "title": "Optimize database instance sizing",
            "description": (
                "Database services represent a large portion of spend. Review instance sizes against "
                "actual query load and connection counts to identify over-provisioned databases."
            ),
            "savings_pct": 0.20,
            "confidence": 0.75,
            "priority": "high",
            "steps": [
                "Collect CPU, memory, and connection metrics for all database instances",
                "Identify databases with <40% average resource utilization",
                "Plan downsize migrations during low-traffic windows",
                "Consider Aurora Serverless or Cloud SQL autoscaling for variable workloads",
            ],
        },
        {
            "keywords": ["data transfer", "cloudfront", "networking"],
            "category": "networking",
            "title": "Reduce data transfer costs with CDN and VPC optimization",
            "description": (
                "Data transfer charges can be minimized by caching static content at the edge, "
                "using VPC endpoints for AWS service traffic, and consolidating cross-region transfers."
            ),
            "savings_pct": 0.20,
            "confidence": 0.70,
            "priority": "medium",
            "steps": [
                "Audit cross-region and internet egress data transfer patterns",
                "Implement VPC endpoints for S3 and DynamoDB access",
                "Optimize CDN cache hit ratios by reviewing cache policies",
                "Consolidate multi-region architectures where possible",
            ],
        },
        {
            "keywords": ["lambda", "cloud functions", "cloud run"],
            "category": "rightsizing",
            "title": "Optimize serverless function memory and concurrency",
            "description": (
                "Serverless functions are often over-provisioned with memory. Right-sizing memory "
                "allocations and setting appropriate concurrency limits reduces per-invocation cost."
            ),
            "savings_pct": 0.22,
            "confidence": 0.72,
            "priority": "medium",
            "steps": [
                "Profile function memory usage with AWS Lambda Power Tuning or equivalent",
                "Reduce memory allocation to match actual peak usage + 20% buffer",
                "Set reserved concurrency to prevent runaway scaling",
                "Review and optimize function timeout settings",
            ],
        },
        {
            "keywords": [],
            "category": "unused_resources",
            "title": "Identify and remove unused resources",
            "description": (
                "Unattached EBS volumes, idle load balancers, unused elastic IPs, and orphaned "
                "snapshots accumulate costs silently. Regular cleanup yields easy savings."
            ),
            "savings_pct": 0.10,
            "confidence": 0.90,
            "priority": "high",
            "steps": [
                "Scan for unattached EBS volumes and unused Elastic IPs",
                "Review load balancers with zero registered targets",
                "Delete snapshots older than retention policy",
                "Tag all resources and flag untagged ones for review",
            ],
        },
    ]

    used_titles: set[str] = set()
    for svc_key, svc_cost in sorted_svcs[:8]:
        provider_str, svc_name = (svc_key.split(":", 1) + ["unknown"])[:2]
        svc_lower = svc_name.lower()

        for tmpl in templates:
            if tmpl["title"] in used_titles:
                continue
            # match if keywords list is empty (catch-all) or any keyword matches
            if tmpl["keywords"] and not any(kw in svc_lower for kw in tmpl["keywords"]):
                continue

            savings = round(svc_cost * tmpl["savings_pct"] / max(1, len(sorted_svcs) // 3), 2)
            savings = max(savings, 15.0)

            recs.append(
                {
                    "category": tmpl["category"],
                    "title": tmpl["title"],
                    "description": tmpl["description"],
                    "estimated_monthly_savings": savings,
                    "confidence": tmpl["confidence"],
                    "priority": tmpl["priority"],
                    "cloud_provider": provider_str,
                    "affected_resources": [svc_name],
                    "implementation_steps": tmpl["steps"],
                }
            )
            used_titles.add(tmpl["title"])
            break

    state["recommendations"] = recs
    return state


def prioritize(state: AnalyzerState) -> AnalyzerState:
    """Sort recommendations by savings * confidence (ROI proxy) and cap at 8."""
    recs = state.get("recommendations", [])
    recs.sort(
        key=lambda r: r.get("estimated_monthly_savings", 0) * r.get("confidence", 0),
        reverse=True,
    )
    state["recommendations"] = recs[:8]
    return state


# ---------------------------------------------------------------------------
# Build the LangGraph workflow
# ---------------------------------------------------------------------------

def _build_graph():  # type: ignore[no-untyped-def]
    from langgraph.graph import END, StateGraph

    graph = StateGraph(AnalyzerState)
    graph.add_node("collect_data", collect_data)
    graph.add_node("detect_anomalies", detect_anomalies)
    graph.add_node("generate_recommendations", generate_recommendations_llm)
    graph.add_node("prioritize", prioritize)

    graph.set_entry_point("collect_data")
    graph.add_edge("collect_data", "detect_anomalies")
    graph.add_edge("detect_anomalies", "generate_recommendations")
    graph.add_edge("generate_recommendations", "prioritize")
    graph.add_edge("prioritize", END)

    return graph.compile()


# Lazy-initialized compiled graph
_compiled_graph = None


def _get_graph():  # type: ignore[no-untyped-def]
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_costs(
    records: list[CostRecord],
) -> tuple[list[AIRecommendation], list[CostAnomaly]]:
    """Run the full cost analysis pipeline and return recommendations + anomalies."""
    if not records:
        return [], []

    raw_records = [r.model_dump(mode="json") for r in records]
    # Ensure date fields are strings for JSON-safe processing
    for r in raw_records:
        if isinstance(r.get("usage_date"), date):
            r["usage_date"] = r["usage_date"].isoformat()

    initial_state: AnalyzerState = {
        "cost_records": raw_records,
        "provider_totals": {},
        "service_totals": {},
        "daily_totals": {},
        "anomalies": [],
        "recommendations": [],
        "error": None,
    }

    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)

    # Convert raw dicts to typed models
    recommendations: list[AIRecommendation] = []
    for r in final_state.get("recommendations", []):
        try:
            recommendations.append(
                AIRecommendation(
                    id=r.get("id", str(uuid.uuid4())),
                    category=RecommendationCategory(r["category"]),
                    title=r["title"],
                    description=r["description"],
                    estimated_monthly_savings=float(r["estimated_monthly_savings"]),
                    confidence=min(1.0, max(0.0, float(r.get("confidence", 0.7)))),
                    priority=Priority(r.get("priority", "medium")),
                    cloud_provider=CloudProvider(r.get("cloud_provider", "aws")),
                    affected_resources=r.get("affected_resources", []),
                    implementation_steps=r.get("implementation_steps", []),
                    status=RecommendationStatus.PENDING,
                    created_at=datetime.utcnow(),
                )
            )
        except Exception as exc:
            logger.warning("recommendation.parse_failed", error=str(exc), raw=r)

    anomalies: list[CostAnomaly] = []
    for a in final_state.get("anomalies", []):
        try:
            anomalies.append(CostAnomaly(**a))
        except Exception as exc:
            logger.warning("anomaly.parse_failed", error=str(exc), raw=a)

    logger.info(
        "analysis.complete",
        recommendations=len(recommendations),
        anomalies=len(anomalies),
    )
    return recommendations, anomalies
