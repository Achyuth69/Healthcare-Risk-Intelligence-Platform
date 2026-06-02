/**
 * Prediction Page — Main risk assessment form and results display
 */
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { predictionAPI } from "../api/client";
import { RiskGauge } from "../components/RiskGauge";
import { SHAPChart } from "../components/SHAPChart";

// ── Form Schema ───────────────────────────────────────────────
const predictionSchema = z.object({
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

type PredictionFormData = z.infer<typeof predictionSchema>;

interface PredictionResult {
  prediction_id: string;
  risk_score: number;
  risk_percentage: number;
  risk_category: "low" | "medium" | "high" | "critical";
  confidence: number;
  disease_type: string;
  model_type: string;
  model_version: string;
  shap_explanation?: {
    top_features: Array<{
      name: string;
      value: number;
      shap_value: number;
      direction: string;
    }>;
  };
  llm_narrative?: string;
  processing_time_ms: number;
}

export const PredictionPage: React.FC = () => {
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"shap" | "narrative">("shap");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PredictionFormData>({
    resolver: zodResolver(predictionSchema),
    defaultValues: {
      disease_type: "diabetes",
      model_type: "ensemble",
      has_diabetes: false,
      has_hypertension: false,
      has_heart_disease: false,
      has_kidney_disease: false,
      family_history_diabetes: false,
      family_history_heart_disease: false,
    },
  });

  const onSubmit = async (data: PredictionFormData) => {
    setIsLoading(true);
    try {
      const { disease_type, model_type, ...features } = data;
      const { data: response } = await predictionAPI.predict({
        features,
        disease_type,
        model_type,
        include_shap: true,
        include_lime: false,
        include_llm_narrative: true,
      });
      setResult(response);
      toast.success("Risk assessment complete");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Prediction failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Disease Risk Assessment</h1>
        <p className="text-gray-500 mt-1">
          Enter patient clinical data to generate an AI-powered risk prediction with explainability.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ── Input Form ─────────────────────────────────────── */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">Patient Data</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Disease & Model Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Disease Type
                </label>
                <select
                  {...register("disease_type")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="diabetes">Diabetes</option>
                  <option value="heart_disease">Heart Disease</option>
                  <option value="hypertension">Hypertension</option>
                  <option value="kidney_disease">Kidney Disease</option>
                  <option value="stroke">Stroke</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model
                </label>
                <select
                  {...register("model_type")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="ensemble">Ensemble (Recommended)</option>
                  <option value="xgboost">XGBoost</option>
                  <option value="random_forest">Random Forest</option>
                  <option value="lightgbm">LightGBM</option>
                </select>
              </div>
            </div>

            {/* Demographics */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age *</label>
                <input
                  type="number"
                  {...register("age", { valueAsNumber: true })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 52"
                />
                {errors.age && <p className="text-red-500 text-xs mt-1">{errors.age.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                <select
                  {...register("gender")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Vitals */}
            <div>
              <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Vitals & Lab Values
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { name: "bmi", label: "BMI", placeholder: "e.g. 28.5" },
                  { name: "glucose_level", label: "Glucose (mg/dL)", placeholder: "e.g. 105" },
                  { name: "hba1c", label: "HbA1c (%)", placeholder: "e.g. 5.8" },
                  { name: "blood_pressure_systolic", label: "BP Systolic", placeholder: "e.g. 130" },
                  { name: "blood_pressure_diastolic", label: "BP Diastolic", placeholder: "e.g. 85" },
                  { name: "cholesterol_total", label: "Total Cholesterol", placeholder: "e.g. 200" },
                  { name: "cholesterol_ldl", label: "LDL", placeholder: "e.g. 120" },
                  { name: "cholesterol_hdl", label: "HDL", placeholder: "e.g. 50" },
                ].map(({ name, label, placeholder }) => (
                  <div key={name}>
                    <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                    <input
                      type="number"
                      step="0.1"
                      {...register(name as any, { valueAsNumber: true })}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                      placeholder={placeholder}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Lifestyle */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Smoking</label>
                <select
                  {...register("smoking_status")}
                  className="w-full border border-gray-300 rounded-lg px-2 py-2 text-sm"
                >
                  <option value="never">Never</option>
                  <option value="former">Former</option>
                  <option value="current">Current</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Alcohol</label>
                <select
                  {...register("alcohol_use")}
                  className="w-full border border-gray-300 rounded-lg px-2 py-2 text-sm"
                >
                  <option value="none">None</option>
                  <option value="moderate">Moderate</option>
                  <option value="heavy">Heavy</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Activity</label>
                <select
                  {...register("physical_activity_level")}
                  className="w-full border border-gray-300 rounded-lg px-2 py-2 text-sm"
                >
                  <option value="sedentary">Sedentary</option>
                  <option value="light">Light</option>
                  <option value="moderate">Moderate</option>
                  <option value="active">Active</option>
                </select>
              </div>
            </div>

            {/* Medical History */}
            <div>
              <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Medical History
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { name: "has_diabetes", label: "Diabetes" },
                  { name: "has_hypertension", label: "Hypertension" },
                  { name: "has_heart_disease", label: "Heart Disease" },
                  { name: "has_kidney_disease", label: "Kidney Disease" },
                  { name: "family_history_diabetes", label: "Family: Diabetes" },
                  { name: "family_history_heart_disease", label: "Family: Heart Disease" },
                ].map(({ name, label }) => (
                  <label key={name} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      {...register(name as any)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                "Run Risk Assessment"
              )}
            </button>
          </form>
        </div>

        {/* ── Results Panel ───────────────────────────────────── */}
        <div className="space-y-6">
          {result ? (
            <>
              {/* Risk Score Card */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-800">Risk Assessment Result</h2>
                    <p className="text-sm text-gray-500">
                      {result.disease_type.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())} ·{" "}
                      {result.model_type} · v{result.model_version}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">{result.processing_time_ms.toFixed(0)}ms</span>
                </div>

                <div className="flex items-center justify-center py-4">
                  <RiskGauge
                    score={result.risk_score}
                    category={result.risk_category}
                    size={220}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Risk Score</p>
                    <p className="text-2xl font-bold text-gray-800">{result.risk_percentage}%</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Model Confidence</p>
                    <p className="text-2xl font-bold text-gray-800">
                      {(result.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Explanation Tabs */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="flex border-b border-gray-200">
                  <button
                    onClick={() => setActiveTab("shap")}
                    className={`flex-1 py-3 text-sm font-medium transition-colors ${
                      activeTab === "shap"
                        ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                        : "text-gray-600 hover:text-gray-800"
                    }`}
                  >
                    SHAP Explanation
                  </button>
                  <button
                    onClick={() => setActiveTab("narrative")}
                    className={`flex-1 py-3 text-sm font-medium transition-colors ${
                      activeTab === "narrative"
                        ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                        : "text-gray-600 hover:text-gray-800"
                    }`}
                  >
                    Clinical Narrative
                  </button>
                </div>

                <div className="p-6">
                  {activeTab === "shap" && result.shap_explanation ? (
                    <SHAPChart features={result.shap_explanation.top_features} />
                  ) : activeTab === "shap" ? (
                    <p className="text-gray-500 text-sm">No SHAP data available.</p>
                  ) : null}

                  {activeTab === "narrative" && result.llm_narrative ? (
                    <div className="prose prose-sm max-w-none">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-blue-600 text-lg">🤖</span>
                          <span className="text-sm font-semibold text-blue-800">
                            AI Clinical Narrative (Llama 3)
                          </span>
                        </div>
                        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
                          {result.llm_narrative}
                        </p>
                      </div>
                    </div>
                  ) : activeTab === "narrative" ? (
                    <p className="text-gray-500 text-sm">No narrative available.</p>
                  ) : null}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-700">Ready for Assessment</h3>
              <p className="text-gray-400 text-sm mt-1">
                Fill in the patient data and click "Run Risk Assessment" to see results with AI explanations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
