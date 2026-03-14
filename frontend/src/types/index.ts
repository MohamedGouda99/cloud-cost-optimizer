export type CloudProvider = "aws" | "gcp";

export type RecommendationCategory =
  | "rightsizing"
  | "unused_resources"
  | "reserved_instances"
  | "storage_optimization"
  | "networking";

export type Priority = "high" | "medium" | "low";

export type RecommendationStatus = "pending" | "implemented" | "dismissed";

export interface ServiceCost {
  service_name: string;
  cost: number;
  percentage: number;
}

export interface DailyCost {
  date: string;
  cost: number;
}

export interface CostSummary {
  provider: CloudProvider;
  total_cost: number;
  period_start: string;
  period_end: string;
  top_services: ServiceCost[];
  daily_costs: DailyCost[];
}

export interface AIRecommendation {
  id: string;
  category: RecommendationCategory;
  title: string;
  description: string;
  estimated_monthly_savings: number;
  confidence: number;
  priority: Priority;
  cloud_provider: CloudProvider;
  affected_resources: string[];
  implementation_steps: string[];
  status: RecommendationStatus;
  created_at: string;
}

export interface CostAnomaly {
  id: string;
  date: string;
  service: string;
  expected_cost: number;
  actual_cost: number;
  deviation_percentage: number;
  explanation: string;
}

export interface OptimizationStats {
  total_potential_savings: number;
  implemented_savings: number;
  recommendations_count: number;
  anomalies_detected: number;
}

export interface SyncResponse {
  records_synced: number;
  providers: string[];
  message: string;
}

export interface GenerateResponse {
  recommendations_count: number;
  anomalies_count: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  demo_mode: boolean;
  providers: Record<string, boolean>;
}
