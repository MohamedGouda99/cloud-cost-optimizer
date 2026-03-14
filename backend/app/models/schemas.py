from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CloudProvider(str, Enum):
    AWS = "aws"
    GCP = "gcp"


class RecommendationCategory(str, Enum):
    RIGHTSIZING = "rightsizing"
    UNUSED_RESOURCES = "unused_resources"
    RESERVED_INSTANCES = "reserved_instances"
    STORAGE_OPTIMIZATION = "storage_optimization"
    NETWORKING = "networking"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class CostRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cloud_provider: CloudProvider
    service_name: str
    cost_amount: float
    currency: str = "USD"
    usage_date: date
    account_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceCost(BaseModel):
    service_name: str
    cost: float
    percentage: float


class DailyCost(BaseModel):
    date: date
    cost: float


class CostSummary(BaseModel):
    provider: CloudProvider
    total_cost: float
    period_start: date
    period_end: date
    top_services: list[ServiceCost]
    daily_costs: list[DailyCost]


class AIRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: RecommendationCategory
    title: str
    description: str
    estimated_monthly_savings: float
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Priority
    cloud_provider: CloudProvider
    affected_resources: list[str] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostAnomaly(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    service: str
    expected_cost: float
    actual_cost: float
    deviation_percentage: float
    explanation: str


class OptimizationStats(BaseModel):
    total_potential_savings: float
    implemented_savings: float
    recommendations_count: int
    anomalies_detected: int


# ---------------------------------------------------------------------------
# Request / response helpers
# ---------------------------------------------------------------------------

class RecommendationUpdate(BaseModel):
    status: RecommendationStatus


class SyncResponse(BaseModel):
    records_synced: int
    providers: list[str]
    message: str


class GenerateResponse(BaseModel):
    recommendations_count: int
    anomalies_count: int
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool
    providers: dict[str, bool]
