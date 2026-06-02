/**
 * Prediction Page — Dark theme, consistent with dashboard
 */
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { predictionAPI } from "../api/client";
import { RiskGauge } from "../components/RiskGauge";
import { SHAPChart } from "../components/SHAPChart";

const schema = z.object({
  age: z.number().min(0).max(120),
  gender: z.enum(["male", "female", "other"]),
  bmi: z.number().min(10).max(80).optional(),
  blood_pressure_systolic: z.number().min(60).max(300).optional(),
  blood_pressure_diastolic: z.number().min(40).max(200).optional(),
  glucose_level: z.number().min(20).max(600).optional(),
  hba1c: z.number().min(3).max(20).optional(),
  cholesterol_total: z.number().min(50).max(600).optional(),
  cholesterol_ldl: z.number().min(10).max(400).optional(),
  cholesterol_hdl: z.number().min(10).max(150).optional(),
  smoking_status: z.enum(["never", "former", "current"]).optional(),
  alcohol_use: z.enum(["none", "moderate", "heavy"]).optional(),
  physical_activity_level: z.enum(["sedentary", "light", "moderate", "active"]).optional(),
  has_diabetes: z.boolean().default(false),
  has_hypertension: z.boolean().default(false),
  has_heart_disease: z.boolean().default(false),
  has_kidney_disease: z.boolean().default(false),
  family_history_diabetes: z.boolean().default(false),
  family_history_heart_disease: z.boolean().default(false),
  disease_type: z.enum(["diabetes", "heart_disease", "hypertension", "kidney_disease", "stroke"]),
  model_type: z.enum(["xgboost", "random_forest", "lightgbm", "ensemble"]).default("ensemble"),
});

type FormData = z.infer<typeof schema>;

const inputCls = "w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none placeholder-gray-600";
const selectCls = `${inputCls} cursor-pointer`;
const labelCls = "block text-xs font-medium text-gray-400 mb-1";

const RISK_COLORS: Record<string, string> = {
  low: "text-green-400", medium: "text-yellow-400", high: "text-orange-400", critical: "text-red-400"
};
const RISK_BG: Record<string, string> = {
  low: "bg-green-500/10 border-green-500/30", medium: "bg-yellow-500/10 border-yellow-500/30",
  high: "bg-orange-500/10 border-orange-500/30", critical: "bg-red-500/10 border-red-500/30"
};

export const PredictionPage: React.FC = () => {
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"shap" | "narrative">("shap");

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      disease_type: "diabetes", model_type: "ensemble",
      has_diabetes: false, has_hypertension: false, has_heart_disease: false,
      has_kidney_disease: false, family_history_diabetes: false, family_history_heart_disease: false,
    },
  });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      const { disease_type, model_type, ...features } = data;
      const { data: res } = await predictionAPI.predict({
        features, disease_type, model_type,
        include_shap: true, include_lime: false, include_llm_narrative: true,
      });
      setResult(res);
      toast.success("Risk assessment complete");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Prediction failed");
    } finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Risk Assessment</h1>
        <p className="text-gray-400 text-sm mt-1">Enter patient data to generate AI-powered risk prediction with explanations</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Form ───────────────────────────────────────────── */}
        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-5">Patient Data</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

            {/* Disease & Model */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelCls}>Disease Type</label>
                <select {...register("disease_type")} className={selectCls}>
                  <option value="diabetes">Diabetes</option>
                  <option value="heart_disease">Heart Disease</option>
                  <option value="hypertension">Hypertension</option>
                  <option value="kidney_disease">Kidney Disease</option>
                  <option value="stroke">Stroke</option>
                </select>
              </div>
              <div>
                <label className={labelCls}>Model</label>
                <select {...register("model_type")} className={selectCls}>
                  <option value="ensemble">Ensemble ⭐</option>
                  <option value="xgboost">XGBoost</option>
                  <option value="random_forest">Random Forest</option>
                  <option value="lightgbm">LightGBM</option>
                </select>
              </div>
            </div>

            {/* Demographics */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelCls}>Age *</label>
                <input type="number" {...register("age", { valueAsNumber: true })}
                  className={inputCls} placeholder="e.g. 52" />
              </div>
              <div>
                <label className={labelCls}>Gender *</label>
                <select {...register("gender")} className={selectCls}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Vitals */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Vitals & Lab Values</p>
              <div className="grid grid-cols-2 gap-2.5">
                {[
                  { name: "bmi",                    label: "BMI",            ph: "28.5" },
                  { name: "glucose_level",           label: "Glucose mg/dL",  ph: "105"  },
                  { name: "hba1c",                   label: "HbA1c %",        ph: "5.8"  },
                  { name: "blood_pressure_systolic", label: "BP Systolic",    ph: "130"  },
                  { name: "blood_pressure_diastolic",label: "BP Diastolic",   ph: "85"   },
                  { name: "cholesterol_total",       label: "Cholesterol",    ph: "200"  },
                  { name: "cholesterol_ldl",         label: "LDL",            ph: "120"  },
                  { name: "cholesterol_hdl",         label: "HDL",            ph: "50"   },
                ].map(({ name, label, ph }) => (
                  <div key={name}>
                    <label className={labelCls}>{label}</label>
                    <input type="number" step="0.1"
                      {...register(name as any, { valueAsNumber: true })}
                      className={inputCls} placeholder={ph} />
                  </div>
                ))}
              </div>
            </div>

            {/* Lifestyle */}
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { name: "smoking_status",          label: "Smoking",   opts: [["never","Never"],["former","Former"],["current","Current"]] },
                { name: "alcohol_use",             label: "Alcohol",   opts: [["none","None"],["moderate","Moderate"],["heavy","Heavy"]] },
                { name: "physical_activity_level", label: "Activity",  opts: [["sedentary","Sedentary"],["light","Light"],["moderate","Moderate"],["active","Active"]] },
              ].map(({ name, label, opts }) => (
                <div key={name}>
                  <label className={labelCls}>{label}</label>
                  <select {...register(name as any)} className={selectCls}>
                    {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
              ))}
            </div>

            {/* Medical History */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Medical History</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { name: "has_diabetes",               label: "Diabetes" },
                  { name: "has_hypertension",           label: "Hypertension" },
                  { name: "has_heart_disease",          label: "Heart Disease" },
                  { name: "has_kidney_disease",         label: "Kidney Disease" },
                  { name: "family_history_diabetes",    label: "Family: Diabetes" },
                  { name: "family_history_heart_disease",label: "Family: Heart" },
                ].map(({ name, label }) => (
                  <label key={name} className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:text-gray-300">
                    <input type="checkbox" {...register(name as any)}
                      className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-500" />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <button type="submit" disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:text-blue-400 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2">
              {isLoading ? (
                <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>Analysing...</>
              ) : "Run Risk Assessment"}
            </button>
          </form>
        </div>

        {/* ── Results ─────────────────────────────────────────── */}
        <div className="space-y-4">
          {result ? (
            <>
              {/* Risk Card */}
              <div className={`bg-gray-900 rounded-2xl border p-6 ${RISK_BG[result.risk_category] || "border-gray-800"}`}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-semibold text-white">Assessment Result</h2>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {result.disease_type.replace("_"," ").replace(/\b\w/g,(c:string)=>c.toUpperCase())} ·{" "}
                      {result.model_type} · v{result.model_version}
                    </p>
                  </div>
                  <span className="text-xs text-gray-600">{result.processing_time_ms.toFixed(0)}ms</span>
                </div>
                <div className="flex items-center justify-center py-2">
                  <RiskGauge score={result.risk_score} category={result.risk_category} size={200} />
                </div>
                <div className="grid grid-cols-3 gap-3 mt-4">
                  <div className="bg-gray-800 rounded-xl p-3 text-center">
                    <p className="text-xs text-gray-500">Risk Score</p>
                    <p className={`text-2xl font-bold ${RISK_COLORS[result.risk_category]}`}>{result.risk_percentage}%</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-3 text-center">
                    <p className="text-xs text-gray-500">Confidence</p>
                    <p className="text-2xl font-bold text-white">{(result.confidence * 100).toFixed(0)}%</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-3 text-center">
                    <p className="text-xs text-gray-500">Category</p>
                    <p className={`text-sm font-bold capitalize mt-1 ${RISK_COLORS[result.risk_category]}`}>{result.risk_category}</p>
                  </div>
                </div>
              </div>

              {/* Explanation tabs */}
              <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
                <div className="flex border-b border-gray-800">
                  {(["shap","narrative"] as const).map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)}
                      className={`flex-1 py-3 text-sm font-medium transition-colors ${
                        activeTab === tab
                          ? "bg-blue-600/20 text-blue-400 border-b-2 border-blue-500"
                          : "text-gray-500 hover:text-gray-300"
                      }`}>
                      {tab === "shap" ? "SHAP Explanation" : "Clinical Narrative"}
                    </button>
                  ))}
                </div>
                <div className="p-5">
                  {activeTab === "shap" && result.shap_explanation && (
                    <SHAPChart features={result.shap_explanation.top_features} />
                  )}
                  {activeTab === "narrative" && (
                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-blue-400">🤖</span>
                        <span className="text-sm font-semibold text-blue-400">Llama 3 Clinical Narrative</span>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                        {result.llm_narrative || "No narrative available."}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-gray-900 rounded-2xl border border-gray-800 p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-400">Ready for Assessment</h3>
              <p className="text-gray-600 text-sm mt-1 max-w-xs">Fill in patient data and click "Run Risk Assessment" to see AI-powered results with SHAP explanations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
