/**
 * Axios API Client — Centralized HTTP client with JWT interceptors
 */
import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_URL || "http://localhost:8000/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor: Attach JWT ──────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor: Handle 401 / Token Refresh ─────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// ── API Methods ───────────────────────────────────────────────

export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post("/auth/login", { email, password }),
  register: (data: RegisterPayload) =>
    apiClient.post("/auth/register", data),
  me: () => apiClient.get("/auth/me"),
  refresh: (refreshToken: string) =>
    apiClient.post("/auth/refresh", { refresh_token: refreshToken }),
};

export const predictionAPI = {
  predict: (payload: PredictionPayload) =>
    apiClient.post("/predictions/predict", payload),
  getHistory: (patientId: string, limit = 20) =>
    apiClient.get(`/predictions/history/${patientId}?limit=${limit}`),
};

export const explanationAPI = {
  getSHAP: (predictionId: string) =>
    apiClient.get(`/explanations/shap/${predictionId}`),
  getLIME: (predictionId: string) =>
    apiClient.get(`/explanations/lime/${predictionId}`),
  getGlobalImportance: (diseaseType: string, modelType = "ensemble") =>
    apiClient.get(
      `/explanations/global-importance/${diseaseType}?model_type=${modelType}`
    ),
};

export const ragAPI = {
  query: (payload: RAGQueryPayload) =>
    apiClient.post("/rag/query", payload),
  ingestDocument: (formData: FormData) =>
    apiClient.post("/rag/ingest", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

export const adminAPI = {
  getStats: () => apiClient.get("/admin/stats"),
  getModelStatus: () => apiClient.get("/admin/models/status"),
  listUsers: () => apiClient.get("/admin/users"),
};

// ── Types ─────────────────────────────────────────────────────

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role?: string;
}

export interface PredictionPayload {
  patient_id?: string;
  features: PatientFeatures;
  disease_type: string;
  model_type: string;
  include_shap: boolean;
  include_lime: boolean;
  include_llm_narrative: boolean;
}

export interface PatientFeatures {
  age: number;
  gender: string;
  bmi?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  heart_rate?: number;
  glucose_level?: number;
  hba1c?: number;
  cholesterol_total?: number;
  cholesterol_ldl?: number;
  cholesterol_hdl?: number;
  triglycerides?: number;
  smoking_status?: string;
  alcohol_use?: string;
  physical_activity_level?: string;
  has_diabetes: boolean;
  has_hypertension: boolean;
  has_heart_disease: boolean;
  has_kidney_disease: boolean;
  family_history_diabetes: boolean;
  family_history_heart_disease: boolean;
}

export interface RAGQueryPayload {
  query: string;
  patient_context?: Record<string, unknown>;
  top_k?: number;
  include_sources?: boolean;
}
