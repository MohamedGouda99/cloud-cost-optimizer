import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Zap,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Server,
  HardDrive,
  Network,
  Archive,
  ShoppingCart,
} from "lucide-react";
import type { AIRecommendation, RecommendationCategory, Priority } from "../types";

interface Props {
  recommendations: AIRecommendation[];
  onImplement: (id: string) => void;
  onDismiss: (id: string) => void;
}

const categoryConfig: Record<
  RecommendationCategory,
  { label: string; color: string; bg: string; icon: typeof Server }
> = {
  rightsizing: {
    label: "Rightsizing",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/30",
    icon: Server,
  },
  unused_resources: {
    label: "Unused Resources",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/30",
    icon: Trash2,
  },
  reserved_instances: {
    label: "Reserved Instances",
    color: "text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/30",
    icon: ShoppingCart,
  },
  storage_optimization: {
    label: "Storage",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/30",
    icon: HardDrive,
  },
  networking: {
    label: "Networking",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/30",
    icon: Network,
  },
};

const priorityConfig: Record<Priority, { label: string; color: string }> = {
  high: { label: "High", color: "text-red-400 bg-red-500/10 border-red-500/30" },
  medium: { label: "Medium", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30" },
  low: { label: "Low", color: "text-gray-400 bg-gray-500/10 border-gray-500/30" },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "Pending", color: "text-yellow-400 bg-yellow-500/10" },
  implemented: { label: "Implemented", color: "text-emerald-400 bg-emerald-500/10" },
  dismissed: { label: "Dismissed", color: "text-gray-400 bg-gray-500/10" },
};

function RecCard({
  rec,
  onImplement,
  onDismiss,
}: {
  rec: AIRecommendation;
  onImplement: () => void;
  onDismiss: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const cat = categoryConfig[rec.category];
  const pri = priorityConfig[rec.priority];
  const st = statusConfig[rec.status];
  const CatIcon = cat.icon;

  return (
    <div className="card group transition-colors hover:border-gray-700">
      {/* Header row */}
      <div className="flex flex-wrap items-start gap-3">
        {/* Category icon */}
        <div className={`rounded-lg border p-2 ${cat.bg}`}>
          <CatIcon className={`h-4 w-4 ${cat.color}`} />
        </div>

        <div className="min-w-0 flex-1">
          {/* Badges */}
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${cat.bg} ${cat.color}`}
            >
              {cat.label}
            </span>
            <span
              className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${pri.color}`}
            >
              {pri.label}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${st.color}`}
            >
              {st.label}
            </span>
            <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs font-medium uppercase text-gray-400">
              {rec.cloud_provider}
            </span>
          </div>

          {/* Title */}
          <h4 className="text-sm font-semibold text-white">{rec.title}</h4>
          <p className="mt-1 text-sm leading-relaxed text-gray-400">
            {rec.description}
          </p>
        </div>

        {/* Savings */}
        <div className="text-right">
          <p className="text-lg font-bold text-emerald-400">
            ${rec.estimated_monthly_savings.toLocaleString()}/mo
          </p>
          <p className="text-xs text-gray-500">
            {(rec.confidence * 100).toFixed(0)}% confidence
          </p>
        </div>
      </div>

      {/* Affected resources */}
      {rec.affected_resources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {rec.affected_resources.map((r) => (
            <span
              key={r}
              className="rounded bg-gray-800 px-2 py-0.5 font-mono text-xs text-gray-400"
            >
              {r}
            </span>
          ))}
        </div>
      )}

      {/* Expandable implementation steps */}
      {rec.implementation_steps.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs font-medium text-gray-400 transition-colors hover:text-gray-200"
          >
            {expanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
            Implementation Steps ({rec.implementation_steps.length})
          </button>
          {expanded && (
            <ol className="mt-2 space-y-1.5 border-l-2 border-gray-800 pl-4">
              {rec.implementation_steps.map((step, i) => (
                <li
                  key={i}
                  className="text-sm leading-relaxed text-gray-400"
                >
                  <span className="mr-2 font-semibold text-gray-500">
                    {i + 1}.
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {/* Action buttons */}
      {rec.status === "pending" && (
        <div className="mt-4 flex gap-2">
          <button
            onClick={onImplement}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-500"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Implement
          </button>
          <button
            onClick={onDismiss}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-1.5 text-xs font-medium text-gray-400 transition-colors hover:border-gray-600 hover:text-gray-200"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

export default function RecommendationsList({
  recommendations,
  onImplement,
  onDismiss,
}: Props) {
  if (recommendations.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center py-12 text-center">
        <Zap className="mb-3 h-10 w-10 text-gray-700" />
        <p className="text-sm text-gray-500">
          No recommendations yet. Click "Generate AI Recommendations" to
          analyze your cost data.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {recommendations.map((rec) => (
        <RecCard
          key={rec.id}
          rec={rec}
          onImplement={() => onImplement(rec.id)}
          onDismiss={() => onDismiss(rec.id)}
        />
      ))}
    </div>
  );
}
