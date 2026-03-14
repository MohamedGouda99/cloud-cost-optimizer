import type {
  AIRecommendation,
  CloudProvider,
  CostAnomaly,
  CostSummary,
  DailyCost,
  GenerateResponse,
  HealthResponse,
  OptimizationStats,
  RecommendationStatus,
  SyncResponse,
} from "../types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

// ----- Costs -----

export function getCostSummary(
  provider: CloudProvider,
  period: number = 30,
): Promise<CostSummary> {
  return request(`/costs/summary?provider=${provider}&period=${period}`);
}

export function getDailyCosts(
  provider?: CloudProvider | null,
  days: number = 30,
): Promise<DailyCost[]> {
  const params = new URLSearchParams({ days: String(days) });
  if (provider) params.set("provider", provider);
  return request(`/costs/daily?${params}`);
}

export function syncCosts(): Promise<SyncResponse> {
  return request("/costs/sync", { method: "POST" });
}

// ----- Recommendations -----

export function getRecommendations(): Promise<AIRecommendation[]> {
  return request("/recommendations");
}

export function generateRecommendations(): Promise<GenerateResponse> {
  return request("/recommendations/generate", { method: "POST" });
}

export function updateRecommendation(
  id: string,
  status: RecommendationStatus,
): Promise<AIRecommendation> {
  return request(`/recommendations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ----- Anomalies -----

export function getAnomalies(): Promise<CostAnomaly[]> {
  return request("/anomalies");
}

// ----- Stats -----

export function getStats(): Promise<OptimizationStats> {
  return request("/stats");
}

// ----- Health -----

export function getHealth(): Promise<HealthResponse> {
  return request("/health");
}
