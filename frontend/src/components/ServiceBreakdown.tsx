import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import type { ServiceCost, CostSummary } from "../types";

interface Props {
  awsSummary: CostSummary | null;
  gcpSummary: CostSummary | null;
  provider: "all" | "aws" | "gcp";
}

const COLORS = [
  "#3b82f6",
  "#f97316",
  "#10b981",
  "#a855f7",
  "#f43f5e",
  "#06b6d4",
  "#eab308",
  "#ec4899",
  "#6366f1",
  "#14b8a6",
];

function formatCurrency(v: number): string {
  return `$${v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 shadow-xl">
      <p className="text-sm font-medium text-white">{d.name}</p>
      <p className="text-sm text-gray-400">
        {formatCurrency(d.value)} ({d.payload.percentage.toFixed(1)}%)
      </p>
    </div>
  );
};

const RADIAN = Math.PI / 180;
const renderLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percentage,
  name,
}: any) => {
  if (percentage < 5) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 1.3;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x}
      y={y}
      fill="#9ca3af"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize={11}
    >
      {name} ({percentage.toFixed(0)}%)
    </text>
  );
};

export default function ServiceBreakdown({
  awsSummary,
  gcpSummary,
  provider,
}: Props) {
  // Merge services from both providers
  const serviceMap = new Map<string, number>();

  const addServices = (services: ServiceCost[], prefix: string) => {
    for (const s of services) {
      const key = `${prefix}${s.service_name}`;
      serviceMap.set(key, (serviceMap.get(key) ?? 0) + s.cost);
    }
  };

  if ((provider === "all" || provider === "aws") && awsSummary) {
    addServices(awsSummary.top_services, provider === "all" ? "AWS: " : "");
  }
  if ((provider === "all" || provider === "gcp") && gcpSummary) {
    addServices(gcpSummary.top_services, provider === "all" ? "GCP: " : "");
  }

  const totalCost = Array.from(serviceMap.values()).reduce(
    (a, b) => a + b,
    0,
  );

  const chartData = Array.from(serviceMap.entries())
    .map(([name, cost]) => ({
      name,
      cost,
      percentage: totalCost > 0 ? (cost / totalCost) * 100 : 0,
    }))
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 10);

  return (
    <div className="card">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
        Cost by Service
      </h3>
      {chartData.length === 0 ? (
        <div className="flex h-72 items-center justify-center text-sm text-gray-500">
          No service data available
        </div>
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="cost"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={2}
                label={renderLabel}
              >
                {chartData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={COLORS[i % COLORS.length]}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
      {/* Breakdown list */}
      <div className="mt-3 space-y-2">
        {chartData.map((s, i) => (
          <div key={s.name} className="flex items-center gap-3 text-sm">
            <span
              className="inline-block h-3 w-3 flex-shrink-0 rounded-sm"
              style={{ backgroundColor: COLORS[i % COLORS.length] }}
            />
            <span className="flex-1 truncate text-gray-300">{s.name}</span>
            <span className="font-medium text-white">
              {formatCurrency(s.cost)}
            </span>
            <span className="w-12 text-right text-xs text-gray-500">
              {s.percentage.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
