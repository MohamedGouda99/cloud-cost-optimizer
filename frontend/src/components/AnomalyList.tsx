import { AlertTriangle } from "lucide-react";
import type { CostAnomaly } from "../types";

interface Props {
  anomalies: CostAnomaly[];
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function fmt(n: number): string {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function AnomalyList({ anomalies }: Props) {
  if (anomalies.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center py-12 text-center">
        <AlertTriangle className="mb-3 h-10 w-10 text-gray-700" />
        <p className="text-sm text-gray-500">No anomalies detected.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/50 text-left">
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Date
              </th>
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Service
              </th>
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Expected
              </th>
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Actual
              </th>
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Deviation
              </th>
              <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Explanation
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/50">
            {anomalies.map((a) => {
              const isOver = a.deviation_percentage > 0;
              return (
                <tr
                  key={a.id}
                  className="transition-colors hover:bg-gray-800/30"
                >
                  <td className="whitespace-nowrap px-5 py-3.5 text-gray-300">
                    {formatDate(a.date)}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3.5">
                    <span className="rounded bg-gray-800 px-2 py-0.5 font-mono text-xs text-gray-300">
                      {a.service}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-5 py-3.5 text-gray-400">
                    {fmt(a.expected_cost)}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3.5 font-medium text-white">
                    {fmt(a.actual_cost)}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3.5">
                    <span
                      className={`inline-flex items-center gap-1 font-semibold ${
                        isOver ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {isOver ? "+" : ""}
                      {a.deviation_percentage.toFixed(1)}%
                      {isOver && (
                        <AlertTriangle className="h-3.5 w-3.5" />
                      )}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-5 py-3.5 text-gray-400">
                    {a.explanation}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
