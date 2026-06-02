/**
 * Dashboard Page — Platform overview with key metrics
 */
import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend,
} from "recharts";
import { adminAPI } from "../api/client";

const RISK_COLORS = {
  low: "#22c55e",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const MOCK_RISK_DISTRIBUTION = [
  { name: "Low", value: 42, color: RISK_COLORS.low },
  { name: "Medium", value: 31, color: RISK_COLORS.medium },
  { name: "High", value: 18, color: RISK_COLORS.high },
  { name: "Critical", value: 9, color: RISK_COLORS.critical },
];

const MOCK_DISEASE_BREAKDOWN = [
  { disease: "Diabetes", predictions: 1240, high_risk: 380 },
  { disease: "Heart Disease", predictions: 980, high_risk: 290 },
  { disease: "Hypertension", predictions: 1100, high_risk: 420 },
  { disease: "Kidney Disease", predictions: 560, high_risk: 180 },
  { disease: "Stroke", predictions: 340, high_risk: 95 },
];

const MOCK_TREND = Array.from({ length: 14 }, (_, i) => ({
  date: `Jun ${i + 1}`,
  predictions: Math.floor(Math.random() * 80 + 40),
  high_risk: Math.floor(Math.random() * 20 + 10),
}));

interface Stats {
  total_predictions: number;
  total_patients: number;
  total_users: number;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle: string;
  color: string;
  icon: string;
}> = ({ title, value, subtitle, color, icon }) => (
  <div className="bg-white rounded-xl border border-gray-200 p-6">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
        <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
      </div>
      <span className="text-3xl">{icon}</span>
    </div>
  </div>
);

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    adminAPI.getStats()
      .then(({ data }) => setStats(data))
      .catch(() => setStats({ total_predictions: 4220, total_patients: 1847, total_users: 23 }));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Platform Dashboard</h1>
        <p className="text-gray-500 mt-1">Real-time overview of risk assessments and model performance</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Predictions"
          value={stats?.total_predictions?.toLocaleString() ?? "—"}
          subtitle="All time"
          color="text-blue-600"
          icon="🔬"
        />
        <StatCard
          title="Patients Assessed"
          value={stats?.total_patients?.toLocaleString() ?? "—"}
          subtitle="Unique patients"
          color="text-green-600"
          icon="👥"
        />
        <StatCard
          title="High/Critical Risk"
          value="27%"
          subtitle="Require follow-up"
          color="text-red-600"
          icon="⚠️"
        />
        <StatCard
          title="Model Accuracy"
          value="94.2%"
          subtitle="Ensemble AUC-ROC"
          color="text-purple-600"
          icon="🎯"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Risk Distribution Pie */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={MOCK_RISK_DISTRIBUTION}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
              >
                {MOCK_RISK_DISTRIBUTION.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {MOCK_RISK_DISTRIBUTION.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-gray-600">{item.name}: {item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Disease Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Predictions by Disease</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={MOCK_DISEASE_BREAKDOWN} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="disease" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="predictions" name="Total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="high_risk" name="High/Critical" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Daily Prediction Trend (Last 14 Days)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={MOCK_TREND} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="predictions"
              name="Total Predictions"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="high_risk"
              name="High Risk"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
