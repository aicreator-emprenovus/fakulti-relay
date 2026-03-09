import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import LeadsPage from "@/pages/LeadsPage";
import GamesConfigPage from "@/pages/GamesConfigPage";
import GamePublicPage from "@/pages/GamePublicPage";
import LoyaltyPage from "@/pages/LoyaltyPage";
import ChatPage from "@/pages/ChatPage";
import SettingsPage from "@/pages/SettingsPage";
import QuotationsPage from "@/pages/QuotationsPage";
import BulkPage from "@/pages/BulkPage";
import Sidebar from "@/components/Sidebar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);
const ThemeContext = createContext(null);

export const useAuth = () => useContext(AuthContext);
export const useTheme = () => useContext(ThemeContext);
export { API, BACKEND_URL, Footer };

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem("faculty_theme") || "light");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("faculty_theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("faculty_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      axios.get(`${API}/auth/me`).then(res => {
        setUser(res.data);
        setLoading(false);
      }).catch(() => {
        localStorage.removeItem("faculty_token");
        setToken(null);
        setUser(null);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    const { token: t, user: u } = res.data;
    localStorage.setItem("faculty_token", t);
    axios.defaults.headers.common["Authorization"] = `Bearer ${t}`;
    setToken(t);
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("faculty_token");
    delete axios.defaults.headers.common["Authorization"];
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

const EMPRENOVUS_LOGO = "https://customer-assets.emergentagent.com/job_maestro-ventas/artifacts/seoa983y_isotipo.png";

function Footer() {
  return (
    <footer className="w-full py-4 px-6 border-t border-border text-center text-xs text-muted-foreground flex items-center justify-center gap-1.5 flex-wrap" data-testid="app-footer">
      <span>&copy; 2026 Fakulti. Todos los derechos reservados</span>
      <span className="hidden sm:inline">|</span>
      <a href="https://www.emprenovus.com" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 hover:text-foreground transition-colors">
        <img src={EMPRENOVUS_LOGO} alt="Emprenovus" className="h-4 w-4 inline-block" />
        <span>AI powered by <span className="font-semibold">Emprenovus</span></span>
      </a>
    </footer>
  );
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-background flex items-center justify-center"><div className="text-primary text-lg">Cargando...</div></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AdminLayout({ children }) {
  const location = useLocation();
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar currentPath={location.pathname} />
      <main className="flex-1 ml-0 md:ml-64 min-h-screen flex flex-col">
        <div className="p-4 md:p-8 flex-1">
          {children}
        </div>
        <Footer />
      </main>
    </div>
  );
}

function AppContent() {
  const { theme } = useTheme();
  return (
    <>
      <Toaster position="top-right" richColors theme={theme} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/game/:gameType" element={<GamePublicPage />} />
        <Route path="/" element={<ProtectedRoute><AdminLayout><DashboardPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/leads" element={<ProtectedRoute><AdminLayout><LeadsPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/games" element={<ProtectedRoute><AdminLayout><GamesConfigPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/loyalty" element={<ProtectedRoute><AdminLayout><LoyaltyPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><AdminLayout><ChatPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/quotations" element={<ProtectedRoute><AdminLayout><QuotationsPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/bulk" element={<ProtectedRoute><AdminLayout><BulkPage /></AdminLayout></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><AdminLayout><SettingsPage /></AdminLayout></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
