import {
  DollarSign,
  TrendingDown,
  CheckCircle,
  Lightbulb,
} from "lucide-react";
import type { OptimizationStats, CostSummary } from "../types";

interface Props {
  stats: OptimizationStats | null;
  awsSummary: CostSummary | null;
  gcpSummary: CostSummary | null;
}

function fmt(n: number): string {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

const cards = [
  {
    key: "spend" as const,
    label: "Total Monthly Spend",
    icon: DollarSign,
    color: "border-blue-500",
    iconColor: "text-blue-400 bg-blue-500/10",
  },
  {
    key: "potential" as const,
    label: "Potential Savings",
    icon: TrendingDown,
    color: "border-amber-500",
    iconColor: "text-amber-400 bg-amber-500/10",
  },
  {
    key: "implemented" as const,
    label: "Implemented Savings",
    icon: CheckCircle,
    color: "border-emerald-500",
    iconColor: "text-emerald-400 bg-emerald-500/10",
  },
  {
    key: "recs" as const,
    label: "Active Recommendations",
    icon: Lightbulb,
    color: "border-purple-500",
    iconColor: "text-purple-400 bg-purple-500/10",
  },
];

export default function StatsCards({ stats, awsSummary, gcpSummary }: Props) {
  const totalSpend =
    (awsSummary?.total_cost ?? 0) + (gcpSummary?.total_cost ?? 0);

  function getValue(key: string): string {
    if (!stats) return "--";
    switch (key) {
      case "spend":
        return fmt(totalSpend);
      case "potential":
        return fmt(stats.total_potential_savings);
      case "implemented":
        return fmt(stats.implemented_savings);
      case "recs":
        return String(stats.recommendations_count);
      default:
        return "--";
    }
  }

  function getSubtext(key: string): string {
    if (!stats) return "";
    switch (key) {
      case "spend":
        return `AWS ${fmt(awsSummary?.total_cost ?? 0)} + GCP ${fmt(gcpSummary?.total_cost ?? 0)}`;
      case "potential":
        return totalSpend > 0
          ? `${((stats.total_potential_savings / totalSpend) * 100).toFixed(1)}% of total spend`
          : "";
      case "implemented":
        return stats.total_potential_savings > 0
          ? `${((stats.implemented_savings / stats.total_potential_savings) * 100).toFixed(0)}% of potential captured`
          : "";
      case "recs":
        return `${stats.anomalies_detected} anomalies detected`;
      default:
        return "";
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.key}
            className={`card border-l-4 ${c.color} flex items-start gap-4`}
          >
            <div className={`rounded-lg p-2.5 ${c.iconColor}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                {c.label}
              </p>
              <p className="mt-1 text-2xl font-bold text-white">
                {getValue(c.key)}
              </p>
              <p className="mt-0.5 truncate text-xs text-gray-500">
                {getSubtext(c.key)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
