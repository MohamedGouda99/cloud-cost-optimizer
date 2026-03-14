import { useCallback, useEffect, useState } from "react";
import type {
  AIRecommendation,
  CloudProvider,
  CostAnomaly,
  CostSummary,
  DailyCost,
  OptimizationStats,
} from "../types";
import * as api from "../lib/api";

interface UseCostDataReturn {
  awsSummary: CostSummary | null;
  gcpSummary: CostSummary | null;
  dailyCosts: DailyCost[];
  recommendations: AIRecommendation[];
  anomalies: CostAnomaly[];
  stats: OptimizationStats | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  syncCosts: () => Promise<string>;
  generateRecommendations: () => Promise<string>;
  updateRecommendation: (
    id: string,
    status: "implemented" | "dismissed",
  ) => Promise<void>;
}

export function useCostData(
  provider: CloudProvider | "all",
  period: number,
): UseCostDataReturn {
  const [awsSummary, setAwsSummary] = useState<CostSummary | null>(null);
  const [gcpSummary, setGcpSummary] = useState<CostSummary | null>(null);
  const [dailyCosts, setDailyCosts] = useState<DailyCost[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>(
    [],
  );
  const [anomalies, setAnomalies] = useState<CostAnomaly[]>([]);
  const [stats, setStats] = useState<OptimizationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [awsSum, gcpSum, recs, anoms, st] = await Promise.all([
        api.getCostSummary("aws", period),
        api.getCostSummary("gcp", period),
        api.getRecommendations(),
        api.getAnomalies(),
        api.getStats(),
      ]);

      setAwsSummary(awsSum);
      setGcpSummary(gcpSum);
      setRecommendations(recs);
      setAnomalies(anoms);
      setStats(st);

      // Merge daily costs from both summaries for the chart
      const awsDailyMap = new Map(
        awsSum.daily_costs.map((d) => [d.date, d.cost]),
      );
      const gcpDailyMap = new Map(
        gcpSum.daily_costs.map((d) => [d.date, d.cost]),
      );
      const allDates = new Set([
        ...awsDailyMap.keys(),
        ...gcpDailyMap.keys(),
      ]);
      const merged = Array.from(allDates)
        .sort()
        .map((date) => ({
          date,
          aws: awsDailyMap.get(date) ?? 0,
          gcp: gcpDailyMap.get(date) ?? 0,
          cost: (awsDailyMap.get(date) ?? 0) + (gcpDailyMap.get(date) ?? 0),
        }));
      setDailyCosts(merged as unknown as DailyCost[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const doSync = useCallback(async () => {
    const res = await api.syncCosts();
    await refresh();
    return res.message;
  }, [refresh]);

  const doGenerate = useCallback(async () => {
    const res = await api.generateRecommendations();
    await refresh();
    return res.message;
  }, [refresh]);

  const doUpdateRec = useCallback(
    async (id: string, status: "implemented" | "dismissed") => {
      await api.updateRecommendation(id, status);
      await refresh();
    },
    [refresh],
  );

  // Filter by provider if needed
  const filteredRecs =
    provider === "all"
      ? recommendations
      : recommendations.filter((r) => r.cloud_provider === provider);

  return {
    awsSummary,
    gcpSummary,
    dailyCosts,
    recommendations: filteredRecs,
    anomalies,
    stats,
    loading,
    error,
    refresh,
    syncCosts: doSync,
    generateRecommendations: doGenerate,
    updateRecommendation: doUpdateRec,
  };
}
