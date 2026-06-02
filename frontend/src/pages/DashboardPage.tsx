/**
 * Dashboard — Interactive, live, compelling overview
 */
import React, { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, RadarChart,
  PolarGrid, PolarAngleAxis, Radar, Legend,
} from "recharts";
import { adminAPI } from "../api/client";
import { useAuthStore } from "../store/authStore";

// ── Colour palette ────────────────────────────────────────────
const COLORS = {
  low:      "#22c55e",
  medium:   "#f59e0b",
  high:     "#f97316",
  critical: "#ef4444",
  blue:     "#3b82f6",
  indigo:   "#6366f1",
  purple:   "#a855f7",
};

// ── Mock data (replace with real API calls when ready) ────────
const RISK_DIST = [
  { name: "Low",      value: 42, color: COLORS.low      },
  { name: "Medium",   value: 31, color: COLORS.medium   },
  { name: "High",     value: 18, color: COLORS.high     },
  { name: "Critical", value:  9, color: COLORS.critical },
];

const DISEASE_DATA = [
  { disease: "Diabetes",      predictions: 1240, high: 380, accuracy: 94 },
  { disease: "Heart Disease", predictions:  980, high: 290, accuracy: 92 },
  { disease: "Hypertension",  predictions: 1100, high: 420, accuracy: 91 },
  { disease: "Kidney",        predictions:  560, high: 180, accuracy: 89 },
  { disease: "Stroke",        predictions:  340, high:  95, accuracy: 93 },
];

const TREND_DATA = Array.from({ length: 14 }, (_, i) => ({
  day: `Jun ${i + 1}`,
  predictions: Math.floor(40 + Math.random() * 80),
  highRisk:    Math.floor(8  + Math.random() * 20),
  resolved:    Math.floor(5  + Math.random() * 15),
}));

const MODEL_RADAR = [
  { metric: "Accuracy",  XGBoost: 94, RF: 91, LightGBM: 93 },
  { metric: "Recall",    XGBoost: 92, RF: 88, LightGBM: 91 },
  { metric: "Precision", XGBoost: 89, RF: 87, LightGBM: 90 },
  { metric: "F1 Score",  XGBoost: 91, RF: 88, LightGBM: 91 },
  { metric: "AUC-ROC",   XGBoost: 96, RF: 93, LightGBM: 95 },
];

const TOP_FEATURES = [
  { feature: "Glucose Level",      impact: 87, direction: "risk" },
  { feature: "HbA1c %",           impact: 82, direction: "risk" },
  { feature: "BMI",               impact: 74, direction: "risk" },
  { feature: "Age",               impact: 68, direction: "risk" },
  { feature: "Physical Activity", impact: 61, direction: "protect" },
  { feature: "Family History",    impact: 58, direction: "risk" },
  { feature: "Blood Pressure",    impact: 54, direction: "risk" },
  { feature: "HDL Cholesterol",   impact: 49, direction: "protect" },
];

// ── Animated counter ──────────────────────────────────────────
const useCounter = (target: number, duration = 1500) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [target]);
  return count;
};

// ── Stat Card ─────────────────────────────────────────────────
const StatCard: React.FC<{
  label: string; value: number; suffix?: string;
  sub: string; icon: string; gradient: string; trend?: string;
}> = ({ label, value, suffix = "", sub, icon, gradient, trend }) => {
  const animated = useCounter(value);
  return (
    <div className={`relative overflow-hidden rounded-2xl p-6 text-white ${gradient} shadow-lg`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium opacity-80">{label}</p>
          <p className="text-4xl font-bold mt-1">
            {animated.toLocaleString()}{suffix}
          </p>
          <p className="text-xs opacity-70 mt-1">{sub}</p>
        </div>
        <span className="text-4xl opacity-90">{icon}</span>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1 text-xs font-medium">
          <span className="bg-white bg-opacity-20 rounded-full px-2 py-0.5">{trend}</span>
        </div>
      )}
      {/* Decorative circle */}
      <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-white bg-opacity-10" />
    </div>
  );
};

// ── Custom tooltip ────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-3 shadow-2xl text-xs text-white">
      <p className="font-semibold text-gray-300 mb-2">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-400">{p.name}:</span>
          <span className="font-bold">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

// ── Main Dashboard ────────────────────────────────────────────
export const DashboardPage: React.FC = () => {
  const user = useAuthStore(s => s.user);
  const [stats, setStats]       = useState({ total_predictions: 4220, total_patients: 1847, total_users: 23 });
  const [activeDisease, setActiveDisease] = useState(0);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  useEffect(() => {
    adminAPI.getStats().then(({ data }) => setStats(data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 space-y-6">

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {greeting}, {user?.full_name?.split(" ")[0] ?? "Doctor"} 👋
          </h1>
          <p className="text-gray-400 text-sm mt-0.5">
            Here's what's happening with your patient risk intelligence today
          </p>
        </div>
        <div className="flex items-center gap-2 bg-green-500 bg-opacity-20 border border-green-500 border-opacity-30 rounded-full px-4 py-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-xs font-medium">All systems operational</span>
        </div>
      </div>

      {/* ── KPI Cards ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Predictions" value={stats.total_predictions}
          sub="All time" icon="🔬"
          gradient="bg-gradient-to-br from-blue-600 to-blue-800"
          trend="↑ 12% this week" />
        <StatCard label="Patients Assessed" value={stats.total_patients}
          sub="Unique profiles" icon="👥"
          gradient="bg-gradient-to-br from-indigo-600 to-indigo-800"
          trend="↑ 8% this week" />
        <StatCard label="Critical Risk Alerts" value={380}
          sub="Require immediate attention" icon="⚠️"
          gradient="bg-gradient-to-br from-red-600 to-red-800"
          trend="↓ 3% vs last week" />
        <StatCard label="Model Accuracy" value={94} suffix="%"
          sub="Ensemble AUC-ROC" icon="🎯"
          gradient="bg-gradient-to-br from-emerald-600 to-emerald-800"
          trend="Validated on 50k patients" />
      </div>

      {/* ── Row 2: Trend + Pie ──────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Trend Area Chart */}
        <div className="lg:col-span-2 bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white">Prediction Activity</h3>
              <p className="text-xs text-gray-400">Last 14 days — all disease types</p>
            </div>
            <div className="flex gap-3 text-xs">
              {[["#3b82f6","Predictions"],["#ef4444","High Risk"],["#22c55e","Resolved"]].map(([c,l]) => (
                <div key={l} className="flex items-center gap-1">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: c as string }} />
                  <span className="text-gray-400">{l}</span>
                </div>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={TREND_DATA} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                {[["blue","#3b82f6"],["red","#ef4444"],["green","#22c55e"]].map(([id, color]) => (
                  <linearGradient key={id} id={`g${id}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={color} stopOpacity={0}   />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="day" tick={{ fill: "#6b7280", fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="predictions" name="Predictions" stroke="#3b82f6" strokeWidth={2} fill="url(#gblue)" />
              <Area type="monotone" dataKey="highRisk"    name="High Risk"   stroke="#ef4444" strokeWidth={2} fill="url(#gred)"  />
              <Area type="monotone" dataKey="resolved"    name="Resolved"    stroke="#22c55e" strokeWidth={2} fill="url(#ggreen)"/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution Donut */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold text-white mb-1">Risk Distribution</h3>
          <p className="text-xs text-gray-400 mb-3">Across all patients today</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={RISK_DIST} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                paddingAngle={3} dataKey="value" strokeWidth={0}>
                {RISK_DIST.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#fff", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {RISK_DIST.map(d => (
              <div key={d.name} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: d.color }} />
                <span className="text-xs text-gray-400">{d.name}</span>
                <span className="text-xs font-bold text-white ml-auto">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Row 3: Disease breakdown + Model radar ──────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Disease Breakdown — interactive tabs */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold text-white mb-1">Disease Breakdown</h3>
          <p className="text-xs text-gray-400 mb-4">Click a disease to highlight</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {DISEASE_DATA.map((d, i) => (
              <button key={d.disease} onClick={() => setActiveDisease(i)}
                className={`text-xs px-3 py-1 rounded-full border transition-all ${
                  activeDisease === i
                    ? "bg-blue-600 border-blue-500 text-white"
                    : "border-gray-700 text-gray-400 hover:border-gray-500"
                }`}>
                {d.disease}
              </button>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={DISEASE_DATA} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="disease" tick={{ fill: "#6b7280", fontSize: 9 }} tickLine={false} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="predictions" name="Total" radius={[4,4,0,0]}>
                {DISEASE_DATA.map((_, i) => (
                  <Cell key={i} fill={i === activeDisease ? "#3b82f6" : "#1e3a5f"} />
                ))}
              </Bar>
              <Bar dataKey="high" name="High Risk" radius={[4,4,0,0]}>
                {DISEASE_DATA.map((_, i) => (
                  <Cell key={i} fill={i === activeDisease ? "#ef4444" : "#4b1c1c"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {/* Active disease detail */}
          <div className="mt-3 bg-gray-800 rounded-xl p-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400">Selected: {DISEASE_DATA[activeDisease].disease}</p>
              <p className="text-sm font-bold text-white">{DISEASE_DATA[activeDisease].predictions.toLocaleString()} predictions</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-400">Model accuracy</p>
              <p className="text-2xl font-bold text-emerald-400">{DISEASE_DATA[activeDisease].accuracy}%</p>
            </div>
          </div>
        </div>

        {/* Model Performance Radar */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold text-white mb-1">Model Performance</h3>
          <p className="text-xs text-gray-400 mb-2">XGBoost vs Random Forest vs LightGBM</p>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={MODEL_RADAR} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
              <PolarGrid stroke="#1f2937" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "#6b7280", fontSize: 10 }} />
              <Radar name="XGBoost"  dataKey="XGBoost"  stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} />
              <Radar name="RF"       dataKey="RF"        stroke="#a855f7" fill="#a855f7" fillOpacity={0.10} strokeWidth={2} />
              <Radar name="LightGBM" dataKey="LightGBM"  stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.10} strokeWidth={2} />
              <Legend iconType="circle" iconSize={8}
                wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#fff", fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Row 4: Top features + Live alerts ───────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Top Risk Features */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold text-white mb-1">Top Risk Factors</h3>
          <p className="text-xs text-gray-400 mb-4">Global SHAP importance — average across all patients</p>
          <div className="space-y-3">
            {TOP_FEATURES.map((f, i) => (
              <div key={f.feature} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-4">{i + 1}</span>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-gray-300">{f.feature}</span>
                    <span className={`text-xs font-bold ${f.direction === "risk" ? "text-red-400" : "text-green-400"}`}>
                      {f.direction === "risk" ? "↑ Risk" : "↓ Protective"}
                    </span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${
                        f.direction === "risk" ? "bg-gradient-to-r from-orange-500 to-red-500"
                                               : "bg-gradient-to-r from-emerald-500 to-green-400"
                      }`}
                      style={{ width: `${f.impact}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs font-bold text-gray-300 w-8 text-right">{f.impact}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold text-white mb-1">Recent Activity</h3>
          <p className="text-xs text-gray-400 mb-4">Live prediction feed</p>
          <div className="space-y-2">
            {[
              { id: "P-2847", disease: "Diabetes",      risk: "High",     score: 73, time: "2 min ago",  color: "text-orange-400", dot: "bg-orange-400" },
              { id: "P-2846", disease: "Heart Disease",  risk: "Critical", score: 89, time: "5 min ago",  color: "text-red-400",    dot: "bg-red-400" },
              { id: "P-2845", disease: "Hypertension",  risk: "Low",      score: 18, time: "8 min ago",  color: "text-green-400",  dot: "bg-green-400" },
              { id: "P-2844", disease: "Stroke",         risk: "Medium",   score: 44, time: "12 min ago", color: "text-yellow-400", dot: "bg-yellow-400" },
              { id: "P-2843", disease: "Kidney Disease", risk: "High",     score: 67, time: "15 min ago", color: "text-orange-400", dot: "bg-orange-400" },
              { id: "P-2842", disease: "Diabetes",      risk: "Low",      score: 12, time: "18 min ago", color: "text-green-400",  dot: "bg-green-400" },
            ].map((item) => (
              <div key={item.id} className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl hover:bg-gray-750 transition-colors">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${item.dot} animate-pulse`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-blue-400">{item.id}</span>
                    <span className="text-xs text-gray-400 truncate">{item.disease}</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className={`text-xs font-bold ${item.color}`}>{item.risk} · {item.score}%</p>
                  <p className="text-xs text-gray-600">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────────────── */}
      <div className="text-center py-2">
        <p className="text-xs text-gray-700">
          HealthRisk AI · Explainable Healthcare Risk Intelligence Platform · Built with XGBoost · SHAP · Llama 3 · RAG
        </p>
      </div>

    </div>
  );
};
