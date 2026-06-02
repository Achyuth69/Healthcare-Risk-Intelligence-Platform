/**
 * SHAPChart — Horizontal bar chart for SHAP feature importance
 * Shows which features push risk up (red) or down (green)
 */
import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface SHAPFeature {
  name: string;
  value: number;
  shap_value: number;
  direction: string;
}

interface SHAPChartProps {
  features: SHAPFeature[];
  title?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg text-sm">
        <p className="font-semibold text-gray-800">{d.name}</p>
        <p className="text-gray-600">Feature value: <span className="font-medium">{d.value?.toFixed(2)}</span></p>
        <p className={d.shap_value > 0 ? "text-red-600" : "text-green-600"}>
          SHAP impact: <span className="font-medium">{d.shap_value > 0 ? "+" : ""}{d.shap_value.toFixed(4)}</span>
        </p>
        <p className="text-gray-500 text-xs mt-1">
          {d.direction === "increases_risk" ? "↑ Increases risk" : "↓ Decreases risk"}
        </p>
      </div>
    );
  }
  return null;
};

export const SHAPChart: React.FC<SHAPChartProps> = ({
  features,
  title = "Feature Impact on Risk (SHAP Values)",
}) => {
  // Sort by absolute SHAP value
  const sorted = [...features]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 12);

  // Format feature names for display
  const formatted = sorted.map((f) => ({
    ...f,
    displayName: f.name
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
      .slice(0, 25),
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">
        Red bars increase risk · Green bars decrease risk · Length = magnitude of impact
      </p>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={formatted}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v) => v.toFixed(3)}
            label={{ value: "SHAP Value", position: "insideBottom", offset: -5 }}
          />
          <YAxis
            type="category"
            dataKey="displayName"
            width={135}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={0} stroke="#6b7280" strokeWidth={2} />
          <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
            {formatted.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.shap_value > 0 ? "#ef4444" : "#22c55e"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
