/**
 * RiskGauge — Animated semicircular gauge for risk score visualization
 */
import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import clsx from "clsx";

interface RiskGaugeProps {
  score: number; // 0-1
  category: "low" | "medium" | "high" | "critical";
  size?: number;
}

const CATEGORY_CONFIG = {
  low: { color: "#22c55e", label: "Low Risk", bg: "bg-green-50", text: "text-green-700" },
  medium: { color: "#f59e0b", label: "Moderate Risk", bg: "bg-yellow-50", text: "text-yellow-700" },
  high: { color: "#f97316", label: "High Risk", bg: "bg-orange-50", text: "text-orange-700" },
  critical: { color: "#ef4444", label: "Critical Risk", bg: "bg-red-50", text: "text-red-700" },
};

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  category,
  size = 200,
}) => {
  const config = CATEGORY_CONFIG[category];
  const percentage = Math.round(score * 100);

  // Gauge data: filled portion + empty portion
  const data = [
    { value: percentage, color: config.color },
    { value: 100 - percentage, color: "#e5e7eb" },
  ];

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size / 2 + 20 }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.35}
              outerRadius={size * 0.48}
              paddingAngle={0}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center text */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-2"
          style={{ bottom: 0 }}
        >
          <span
            className="text-3xl font-bold"
            style={{ color: config.color }}
          >
            {percentage}%
          </span>
        </div>
      </div>

      {/* Category badge */}
      <div
        className={clsx(
          "mt-2 px-4 py-1 rounded-full text-sm font-semibold",
          config.bg,
          config.text
        )}
      >
        {config.label}
      </div>
    </div>
  );
};
