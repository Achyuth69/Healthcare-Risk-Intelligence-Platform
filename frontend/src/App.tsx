import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import clsx from "clsx";
import { useAuthStore } from "./store/authStore";
import { DashboardPage } from "./pages/DashboardPage";
import { PredictionPage } from "./pages/PredictionPage";
import { ChatPage } from "./pages/ChatPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

// ── Auth Guard ────────────────────────────────────────────────
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// ── Sidebar ───────────────────────────────────────────────────
const NAV_ITEMS = [
  { path: "/dashboard", label: "Dashboard",       icon: "📊" },
  { path: "/predict",   label: "Risk Assessment",  icon: "🔬" },
  { path: "/chat",      label: "Clinical AI",      icon: "💬" },
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen fixed left-0 top-0 z-10">
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">H</div>
          <div>
            <p className="font-bold text-sm leading-tight">HealthRisk AI</p>
            <p className="text-xs text-gray-400">Risk Intelligence Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map(({ path, label, icon }) => (
          <Link
            key={path}
            to={path}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              location.pathname === path
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <span>{icon}</span>{label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-xs font-bold">
            {user?.full_name?.[0] ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name ?? "User"}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.role ?? "readonly"}</p>
          </div>
        </div>
        <button onClick={logout} className="w-full text-xs text-gray-400 hover:text-white py-1 transition-colors text-left">
          Sign out
        </button>
      </div>
    </aside>
  );
};

// ── App Layout ────────────────────────────────────────────────
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex bg-gray-950 min-h-screen">
    <Sidebar />
    <main className="ml-64 flex-1 bg-gray-950">{children}</main>
  </div>
);

// ── Root App ──────────────────────────────────────────────────
const App: React.FC = () => {
  const { isAuthenticated, fetchMe } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) fetchMe();
  }, []);

  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Routes>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/predict"   element={<PredictionPage />} />
                  <Route path="/chat"      element={<ChatPage />} />
                  <Route path="/"          element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
