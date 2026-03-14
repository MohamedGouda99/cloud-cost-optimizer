import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface DailyCostMerged {
  date: string;
  aws: number;
  gcp: number;
  cost: number;
}

interface Props {
  data: DailyCostMerged[];
  provider: "all" | "aws" | "gcp";
}

function formatDate(d: string): string {
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatCurrency(v: number): string {
  return `$${v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 shadow-xl">
      <p className="mb-2 text-sm font-medium text-gray-300">
        {formatDate(label)}
      </p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-sm">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-gray-400">{entry.name}:</span>
          <span className="font-semibold text-white">
            {formatCurrency(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function CostChart({ data, provider }: Props) {
  const showAws = provider === "all" || provider === "aws";
  const showGcp = provider === "all" || provider === "gcp";

  return (
    <div className="card">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
        Daily Cost Trend
      </h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#4b5563"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v) => `$${v}`}
              stroke="#4b5563"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 13, paddingTop: 8 }}
              iconType="circle"
            />
            {showAws && (
              <Line
                type="monotone"
                dataKey="aws"
                name="AWS"
                stroke="#f97316"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            )}
            {showGcp && (
              <Line
                type="monotone"
                dataKey="gcp"
                name="GCP"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
