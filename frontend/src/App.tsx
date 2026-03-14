import { useState } from "react";
import {
  DollarSign,
  RefreshCw,
  Sparkles,
  Loader2,
  AlertCircle,
  Cloud,
} from "lucide-react";
import { useCostData } from "./hooks/useCostData";
import StatsCards from "./components/StatsCards";
import CostChart from "./components/CostChart";
import ServiceBreakdown from "./components/ServiceBreakdown";
import RecommendationsList from "./components/RecommendationsList";
import AnomalyList from "./components/AnomalyList";
import type { CloudProvider } from "./types";

type ProviderFilter = "all" | CloudProvider;
type PeriodOption = 7 | 30 | 90;

const providerTabs: { value: ProviderFilter; label: string }[] = [
  { value: "all", label: "All Providers" },
  { value: "aws", label: "AWS" },
  { value: "gcp", label: "GCP" },
];

const periodOptions: { value: PeriodOption; label: string }[] = [
  { value: 7, label: "7d" },
  { value: 30, label: "30d" },
  { value: 90, label: "90d" },
];

export default function App() {
  const [provider, setProvider] = useState<ProviderFilter>("all");
  const [period, setPeriod] = useState<PeriodOption>(30);
  const [syncing, setSyncing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  const {
    awsSummary,
    gcpSummary,
    dailyCosts,
    recommendations,
    anomalies,
    stats,
    loading,
    error,
    syncCosts,
    generateRecommendations,
    updateRecommendation,
  } = useCostData(provider, period);

  function showToast(message: string, type: "success" | "error" = "success") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const msg = await syncCosts();
      showToast(msg);
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Sync failed",
        "error",
      );
    } finally {
      setSyncing(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      const msg = await generateRecommendations();
      showToast(msg);
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Generation failed",
        "error",
      );
    } finally {
      setGenerating(false);
    }
  }

  async function handleImplement(id: string) {
    try {
      await updateRecommendation(id, "implemented");
      showToast("Recommendation marked as implemented");
    } catch (err) {
      showToast("Failed to update recommendation", "error");
    }
  }

  async function handleDismiss(id: string) {
    try {
      await updateRecommendation(id, "dismissed");
      showToast("Recommendation dismissed");
    } catch (err) {
      showToast("Failed to update recommendation", "error");
    }
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Toast */}
      {toast && (
        <div className="fixed right-4 top-4 z-50 animate-pulse">
          <div
            className={`flex items-center gap-2 rounded-lg border px-4 py-3 shadow-xl ${
              toast.type === "success"
                ? "border-emerald-800 bg-emerald-950 text-emerald-300"
                : "border-red-800 bg-red-950 text-red-300"
            }`}
          >
            {toast.type === "error" && (
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
            )}
            <span className="text-sm">{toast.message}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-gray-800 bg-gray-950/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 p-2">
              <DollarSign className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">
                Cloud Cost Optimizer
              </h1>
              <p className="text-xs text-gray-500">
                AI-Powered Multi-Cloud Cost Management
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSync}
              disabled={syncing}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:border-gray-600 hover:text-white disabled:opacity-50"
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Sync Data
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {generating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate AI Recommendations
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          {/* Provider tabs */}
          <div className="inline-flex rounded-lg border border-gray-800 bg-gray-900 p-1">
            {providerTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setProvider(tab.value)}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  provider === tab.value
                    ? "bg-gray-700 text-white shadow"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {tab.value !== "all" && <Cloud className="h-3.5 w-3.5" />}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Period selector */}
          <div className="inline-flex rounded-lg border border-gray-800 bg-gray-900 p-1">
            {periodOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPeriod(opt.value)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  period === opt.value
                    ? "bg-gray-700 text-white shadow"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading / Error states */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-3 text-gray-400">Loading cost data...</span>
          </div>
        )}

        {error && !loading && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-800 bg-red-950/50 px-5 py-4 text-sm text-red-300">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <div>
              <p className="font-medium">Failed to load data</p>
              <p className="mt-0.5 text-red-400">{error}</p>
            </div>
          </div>
        )}

        {!loading && (
          <>
            {/* Stats Cards */}
            <StatsCards
              stats={stats}
              awsSummary={awsSummary}
              gcpSummary={gcpSummary}
            />

            {/* Charts row */}
            <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-5">
              <div className="lg:col-span-3">
                <CostChart data={dailyCosts as any} provider={provider} />
              </div>
              <div className="lg:col-span-2">
                <ServiceBreakdown
                  awsSummary={awsSummary}
                  gcpSummary={gcpSummary}
                  provider={provider}
                />
              </div>
            </div>

            {/* Recommendations */}
            <section className="mt-8">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-semibold text-white">
                  AI Recommendations
                </h2>
                <span className="text-xs text-gray-500">
                  {recommendations.length} recommendation
                  {recommendations.length !== 1 ? "s" : ""}
                </span>
              </div>
              <RecommendationsList
                recommendations={recommendations}
                onImplement={handleImplement}
                onDismiss={handleDismiss}
              />
            </section>

            {/* Anomalies */}
            <section className="mt-8 pb-12">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-semibold text-white">
                  Cost Anomalies
                </h2>
                <span className="text-xs text-gray-500">
                  {anomalies.length} anomal
                  {anomalies.length !== 1 ? "ies" : "y"}
                </span>
              </div>
              <AnomalyList anomalies={anomalies} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}
