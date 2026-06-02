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
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl text-sm">
        <p className="font-semibold text-gray-200">{d.name}</p>
        <p className="text-gray-400">Feature value: <span className="font-medium text-white">{d.value?.toFixed(2)}</span></p>
        <p className={d.shap_value > 0 ? "text-red-400" : "text-green-400"}>
          SHAP impact: <span className="font-medium">{d.shap_value > 0 ? "+" : ""}{d.shap_value?.toFixed(4)}</span>
        </p>
      </div>
    );
  }
  return null;
};

export const SHAPChart: React.FC<SHAPChartProps> = ({ features, title = "Feature Impact on Risk (SHAP Values)" }) => {
  const sorted = [...features].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).slice(0, 12);
  const formatted = sorted.map(f => ({
    ...f,
    displayName: f.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()).slice(0, 25),
  }));

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-300 mb-1">{title}</h3>
      <p className="text-xs text-gray-500 mb-4">Red = increases risk · Green = decreases risk · Length = magnitude</p>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart data={formatted} layout="vertical" margin={{ top: 5, right: 30, left: 140, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1f2937" />
          <XAxis type="number" tickFormatter={v => v.toFixed(3)} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} />
          <YAxis type="category" dataKey="displayName" width={135} tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={0} stroke="#374151" strokeWidth={2} />
          <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
            {formatted.map((entry, index) => (
              <Cell key={index} fill={entry.shap_value > 0 ? "#ef4444" : "#22c55e"} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
