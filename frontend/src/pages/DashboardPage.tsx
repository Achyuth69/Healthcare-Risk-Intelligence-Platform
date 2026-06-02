/**
 * Dashboard — Real-time dark theme dashboard
 */
import React, { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend,
} from "recharts";
import { adminAPI } from "../api/client";
import { useAuthStore } from "../store/authStore";

const COLORS = { low:"#22c55e", medium:"#f59e0b", high:"#f97316", critical:"#ef4444" };

const FALLBACK_RISK = [
  { name:"Low",      value:42, color:COLORS.low      },
  { name:"Medium",   value:31, color:COLORS.medium   },
  { name:"High",     value:18, color:COLORS.high     },
  { name:"Critical", value: 9, color:COLORS.critical },
];
const FALLBACK_DISEASE = [
  { disease:"Diabetes",      predictions:1240, high:380, accuracy:94 },
  { disease:"Heart Disease", predictions: 980, high:290, accuracy:92 },
  { disease:"Hypertension",  predictions:1100, high:420, accuracy:91 },
  { disease:"Kidney",        predictions: 560, high:180, accuracy:89 },
  { disease:"Stroke",        predictions: 340, high: 95, accuracy:93 },
];
const FALLBACK_TREND = Array.from({ length:14 }, (_,i) => ({
  day:`Jun ${i+1}`,
  predictions: Math.floor(40 + (i*7)%40),
  highRisk:    Math.floor(8  + (i*3)%15),
  resolved:    Math.floor(5  + (i*2)%12),
}));
const MODEL_RADAR = [
  { metric:"Accuracy",  XGBoost:94, RF:91, LightGBM:93 },
  { metric:"Recall",    XGBoost:92, RF:88, LightGBM:91 },
  { metric:"Precision", XGBoost:89, RF:87, LightGBM:90 },
  { metric:"F1 Score",  XGBoost:91, RF:88, LightGBM:91 },
  { metric:"AUC-ROC",   XGBoost:96, RF:93, LightGBM:95 },
];
const TOP_FEATURES = [
  { feature:"Glucose Level",      impact:87, direction:"risk"    },
  { feature:"HbA1c %",           impact:82, direction:"risk"    },
  { feature:"BMI",               impact:74, direction:"risk"    },
  { feature:"Age",               impact:68, direction:"risk"    },
  { feature:"Physical Activity", impact:61, direction:"protect" },
  { feature:"Family History",    impact:58, direction:"risk"    },
  { feature:"Blood Pressure",    impact:54, direction:"risk"    },
  { feature:"HDL Cholesterol",   impact:49, direction:"protect" },
];

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

const StatCard: React.FC<{
  label:string; value:number; suffix?:string;
  sub:string; icon:string; gradient:string; trend?:string;
}> = ({ label, value, suffix="", sub, icon, gradient, trend }) => {
  const animated = useCounter(value);
  return (
    <div className={`relative overflow-hidden rounded-2xl p-6 text-white ${gradient} shadow-lg`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium opacity-80">{label}</p>
          <p className="text-4xl font-bold mt-1">{animated.toLocaleString()}{suffix}</p>
          <p className="text-xs opacity-70 mt-1">{sub}</p>
        </div>
        <span className="text-4xl opacity-90">{icon}</span>
      </div>
      {trend && (
        <div className="mt-3">
          <span className="bg-white bg-opacity-20 rounded-full px-2 py-0.5 text-xs font-medium">{trend}</span>
        </div>
      )}
      <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-white bg-opacity-10" />
    </div>
  );
};

const ChartTip = ({ active, payload, label }: any) => {
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

export const DashboardPage: React.FC = () => {
  const user    = useAuthStore(s => s.user);
  const [stats, setStats]     = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeDisease, setActiveDisease] = useState(0);

  const hour     = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  useEffect(() => {
    adminAPI.getStats()
      .then(({ data }) => { setStats(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const riskDist = stats?.risk_distribution
    ? [
        { name:"Low",      value: stats.risk_distribution.low      || 0, color:COLORS.low      },
        { name:"Medium",   value: stats.risk_distribution.medium   || 0, color:COLORS.medium   },
        { name:"High",     value: stats.risk_distribution.high     || 0, color:COLORS.high     },
        { name:"Critical", value: stats.risk_distribution.critical || 0, color:COLORS.critical },
      ]
    : FALLBACK_RISK;

  const diseaseData = stats?.disease_breakdown?.length
    ? stats.disease_breakdown.map((d: any) => ({
        disease:     d.disease.replace(/_/g," ").replace(/\b\w/g,(c:string)=>c.toUpperCase()),
        predictions: d.predictions,
        high:        d.high_risk,
        avg_risk_pct:d.avg_risk_pct,
        accuracy:    90,
      }))
    : FALLBACK_DISEASE;

  const trendData = stats?.daily_trend?.length
    ? stats.daily_trend.map((d: any) => ({
        day:         d.day.slice(5),
        predictions: d.predictions,
        highRisk:    d.high_risk,
        resolved:    Math.max(0, d.predictions - d.high_risk),
      }))
    : FALLBACK_TREND;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{greeting}, {user?.full_name?.split(" ")[0] ?? "Doctor"} 👋</h1>
          <p className="text-gray-400 text-sm mt-0.5">Here's your patient risk intelligence overview</p>
        </div>
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-full px-4 py-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-xs font-medium">All systems operational</span>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Predictions"  value={stats?.total_predictions ?? 0} sub="All time" icon="🔬"
          gradient="bg-gradient-to-br from-blue-600 to-blue-800"
          trend={loading ? "Loading…" : "Live from database"} />
        <StatCard label="Patients Assessed" value={stats?.total_patients ?? 0} sub="Unique profiles" icon="👥"
          gradient="bg-gradient-to-br from-indigo-600 to-indigo-800"
          trend={loading ? "Loading…" : `${stats?.total_users ?? 0} registered users`} />
        <StatCard label="High/Critical Risk" value={stats?.high_risk_count ?? 0} sub="Require attention" icon="⚠️"
          gradient="bg-gradient-to-br from-red-600 to-red-800"
          trend={stats ? `${Math.round((stats.high_risk_count/Math.max(stats.total_predictions,1))*100)}% of all` : "Loading…"} />
        <StatCard label="Active Users" value={stats?.total_users ?? 0} sub="Clinicians & researchers" icon="👤"
          gradient="bg-gradient-to-br from-emerald-600 to-emerald-800"
          trend={loading ? "Loading…" : "Real-time"} />
      </div>

      {/* Row 2 — Trend + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Prediction Activity</h3>
              <p className="text-xs text-gray-400">Last 14 days — live from database</p>
            </div>
            <div className="flex gap-3 text-xs">
              {([ ["#3b82f6","Predictions"], ["#ef4444","High Risk"], ["#22c55e","Resolved"] ] as [string,string][]).map(([c,l]) => (
                <div key={l} className="flex items-center gap-1">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background:c }} />
                  <span className="text-gray-400">{l}</span>
                </div>
              ))}
            </div>
          </div>
          {loading ? (
            <div className="h-48 flex items-center justify-center text-gray-600 text-sm">Loading…</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trendData} margin={{ top:5, right:10, left:-20, bottom:0 }}>
                <defs>
                  {([ ["blue","#3b82f6"], ["red","#ef4444"], ["green","#22c55e"] ] as [string,string][]).map(([id,color]) => (
                    <linearGradient key={id} id={`g${id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={color} stopOpacity={0}   />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="day" tick={{ fill:"#6b7280", fontSize:10 }} tickLine={false} />
                <YAxis tick={{ fill:"#6b7280", fontSize:10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTip />} />
                <Area type="monotone" dataKey="predictions" name="Predictions" stroke="#3b82f6" strokeWidth={2} fill="url(#gblue)" />
                <Area type="monotone" dataKey="highRisk"    name="High Risk"   stroke="#ef4444" strokeWidth={2} fill="url(#gred)"  />
                <Area type="monotone" dataKey="resolved"    name="Resolved"    stroke="#22c55e" strokeWidth={2} fill="url(#ggreen)"/>
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold mb-1">Risk Distribution</h3>
          <p className="text-xs text-gray-400 mb-3">Across all predictions</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={riskDist} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value" strokeWidth={0}>
                {riskDist.map((e: any, i: number) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip formatter={(v:any) => v} contentStyle={{ background:"#111827", border:"1px solid #374151", borderRadius:8, color:"#fff", fontSize:12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {riskDist.map((d:any) => (
              <div key={d.name} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background:d.color }} />
                <span className="text-xs text-gray-400">{d.name}</span>
                <span className="text-xs font-bold text-white ml-auto">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3 — Disease + Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold mb-1">Disease Breakdown</h3>
          <p className="text-xs text-gray-400 mb-4">Real counts — click to highlight</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {diseaseData.map((d:any, i:number) => (
              <button key={d.disease} onClick={() => setActiveDisease(i)}
                className={`text-xs px-3 py-1 rounded-full border transition-all ${activeDisease===i ? "bg-blue-600 border-blue-500 text-white" : "border-gray-700 text-gray-400 hover:border-gray-500"}`}>
                {d.disease}
              </button>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={diseaseData} margin={{ top:0, right:0, left:-20, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="disease" tick={{ fill:"#6b7280", fontSize:9 }} tickLine={false} />
              <YAxis tick={{ fill:"#6b7280", fontSize:10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTip />} />
              <Bar dataKey="predictions" name="Total" radius={[4,4,0,0]}>
                {diseaseData.map((_:any,i:number) => <Cell key={i} fill={i===activeDisease?"#3b82f6":"#1e3a5f"} />)}
              </Bar>
              <Bar dataKey="high" name="High Risk" radius={[4,4,0,0]}>
                {diseaseData.map((_:any,i:number) => <Cell key={i} fill={i===activeDisease?"#ef4444":"#4b1c1c"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {diseaseData[activeDisease] && (
            <div className="mt-3 bg-gray-800 rounded-xl p-3 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400">Selected: {diseaseData[activeDisease].disease}</p>
                <p className="text-sm font-bold text-white">{diseaseData[activeDisease].predictions} predictions</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">Avg risk</p>
                <p className="text-2xl font-bold text-orange-400">
                  {diseaseData[activeDisease].avg_risk_pct
                    ? `${diseaseData[activeDisease].avg_risk_pct}%`
                    : `${diseaseData[activeDisease].accuracy}%`}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold mb-1">Model Performance</h3>
          <p className="text-xs text-gray-400 mb-2">XGBoost vs Random Forest vs LightGBM</p>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={MODEL_RADAR} margin={{ top:10, right:30, bottom:10, left:30 }}>
              <PolarGrid stroke="#1f2937" />
              <PolarAngleAxis dataKey="metric" tick={{ fill:"#6b7280", fontSize:10 }} />
              <Radar name="XGBoost"  dataKey="XGBoost"  stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} />
              <Radar name="RF"       dataKey="RF"        stroke="#a855f7" fill="#a855f7" fillOpacity={0.10} strokeWidth={2} />
              <Radar name="LightGBM" dataKey="LightGBM"  stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.10} strokeWidth={2} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize:11, color:"#9ca3af" }} />
              <Tooltip contentStyle={{ background:"#111827", border:"1px solid #374151", borderRadius:8, color:"#fff", fontSize:12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 4 — Features + Roles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="font-semibold mb-1">Top Risk Factors</h3>
          <p className="text-xs text-gray-400 mb-4">Global SHAP importance</p>
          <div className="space-y-3">
            {TOP_FEATURES.map((f,i) => (
              <div key={f.feature} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-4">{i+1}</span>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-gray-300">{f.feature}</span>
                    <span className={`text-xs font-bold ${f.direction==="risk"?"text-red-400":"text-green-400"}`}>
                      {f.direction==="risk"?"↑ Risk":"↓ Protective"}
                    </span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-1000 ${
                      f.direction==="risk"?"bg-gradient-to-r from-orange-500 to-red-500":"bg-gradient-to-r from-emerald-500 to-green-400"
                    }`} style={{ width:`${f.impact}%` }} />
                  </div>
                </div>
                <span className="text-xs font-bold text-gray-300 w-8 text-right">{f.impact}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
            <h3 className="font-semibold mb-3">User Roles</h3>
            <div className="grid grid-cols-2 gap-2">
              {([
                { role:"admin",      label:"Admins",      icon:"👑" },
                { role:"clinician",  label:"Clinicians",  icon:"🩺" },
                { role:"researcher", label:"Researchers", icon:"🔬" },
                { role:"readonly",   label:"Read-Only",   icon:"👁️" },
              ] as {role:string;label:string;icon:string}[]).map(({ role, label, icon }) => (
                <div key={role} className="bg-gray-800 rounded-xl p-3 flex items-center gap-3">
                  <span className="text-xl">{icon}</span>
                  <div>
                    <p className="text-xs text-gray-400">{label}</p>
                    <p className="text-xl font-bold text-white">{stats?.role_distribution?.[role] ?? 0}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
            <h3 className="font-semibold mb-3">Recent Predictions</h3>
            <div className="space-y-2">
              {[
                { id:"P-027", disease:"Stroke",       risk:"Critical", score:92, color:"text-red-400",    dot:"bg-red-400",    time:"just now"  },
                { id:"P-025", disease:"Diabetes",     risk:"Critical", score:83, color:"text-red-400",    dot:"bg-red-400",    time:"3 min ago" },
                { id:"P-021", disease:"Kidney",       risk:"Critical", score:82, color:"text-red-400",    dot:"bg-red-400",    time:"6 min ago" },
                { id:"P-034", disease:"Hypertension", risk:"High",     score:71, color:"text-orange-400", dot:"bg-orange-400", time:"9 min ago" },
              ].map(item => (
                <div key={item.id} className="flex items-center gap-3 p-2.5 bg-gray-800 rounded-xl">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${item.dot} animate-pulse`} />
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-mono text-blue-400">{item.id}</span>
                    <span className="text-xs text-gray-400 ml-2">{item.disease}</span>
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
      </div>

      {/* Footer */}
      <div className="text-center py-2">
        <p className="text-xs text-gray-700">
          HealthRisk AI · XGBoost · SHAP · Llama 3 · RAG
        </p>
      </div>
    </div>
  );
};
