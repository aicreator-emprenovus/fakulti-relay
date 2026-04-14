import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, useTheme } from "@/App";
import { LayoutDashboard, Users, Gamepad2, Heart, Phone, Settings, LogOut, Menu, X, Sun, Moon, Zap, QrCode, UserCheck, Megaphone, ChevronLeft, ChevronRight, Code, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import NotificationBell from "@/components/NotificationBell";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

const allNavItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard", roles: ["admin", "advisor"] },
  { path: "/chat", icon: Phone, label: "WhatsApp Bot", roles: ["admin", "advisor"] },
  { path: "/leads", icon: Users, label: "Leads", roles: ["admin", "advisor"] },
  { path: "/advisors", icon: UserCheck, label: "Asesores", roles: ["admin"] },
  { path: "/campaigns", icon: Megaphone, label: "Campañas", roles: ["admin"] },
  { path: "/qr-campaigns", icon: QrCode, label: "QR y Canales", roles: ["admin"] },
  { path: "/games", icon: Gamepad2, label: "Juegos", roles: ["admin"] },
  { path: "/loyalty", icon: Heart, label: "Fidelización", roles: ["admin"] },
  { path: "/settings", icon: Settings, label: "Productos y Bots", roles: ["admin"] },
  { path: "/config", icon: Zap, label: "Configuración", roles: ["admin", "developer"] },
  // Centro de Entrenamiento removed - bot behavior managed from Reglas de Automatización
  { path: "/dev-alerts", icon: Bell, label: "Panel de Alertas", roles: ["developer"] },
];

export default function Sidebar({ currentPath }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("fk_sidebar") === "collapsed");
  const userRole = user?.role || "admin";

  const navItems = allNavItems.filter(item => item.roles.includes(userRole));

  const handleNav = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("fk_sidebar", next ? "collapsed" : "expanded");
  };

  const w = collapsed ? "w-16" : "w-52";

  const sidebarContent = (
    <div className="flex flex-col h-full bg-card border-r border-border">
      {/* Logo */}
      <div className={`p-3 flex items-center justify-center border-b border-border ${collapsed ? "px-2" : "px-4"}`}>
        <img src={LOGO_URL} alt="Fakulti" className={`${collapsed ? "h-7" : "h-9"} w-auto transition-all`} />
      </div>

      {/* Collapse toggle */}
      <button
        data-testid="sidebar-toggle"
        onClick={toggleCollapse}
        className="hidden md:flex items-center justify-center py-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors border-b border-border"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {navItems.map(item => {
          const isActive = currentPath === item.path;
          return (
            <button
              key={item.path}
              data-testid={`nav-${item.path.replace("/", "") || "dashboard"}`}
              onClick={() => handleNav(item.path)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center ${collapsed ? "justify-center px-2" : "gap-2.5 px-3"} py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              <item.icon size={18} className="flex-shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={`border-t border-border ${collapsed ? "p-2 space-y-2" : "p-3 space-y-2"}`}>
        {userRole !== "developer" && (
          <div className={`flex items-center ${collapsed ? "justify-center" : "gap-2.5 px-3"}`}>
            <NotificationBell />
            {!collapsed && <span className="text-sm text-muted-foreground">Notificaciones</span>}
          </div>
        )}
        <button
          data-testid="theme-toggle-btn"
          onClick={toggleTheme}
          title={collapsed ? (theme === "dark" ? "Modo Claro" : "Modo Oscuro") : undefined}
          className={`w-full flex items-center ${collapsed ? "justify-center px-2" : "gap-2.5 px-3"} py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all`}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          {!collapsed && <span>{theme === "dark" ? "Modo Claro" : "Modo Oscuro"}</span>}
        </button>

        {!collapsed && (
          <div className="flex items-center gap-2.5 px-1">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
              userRole === "advisor" ? "bg-amber-500/10 text-amber-500" : userRole === "developer" ? "bg-violet-500/10 text-violet-500" : "bg-primary/10 text-primary"
            }`}>
              {user?.name?.[0] || "A"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{user?.name || "Admin"}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {userRole === "advisor" ? "Asesor" : userRole === "developer" ? "Desarrollador" : "Administrador"} - {user?.email || ""}
              </p>
            </div>
          </div>
        )}

        {collapsed && (
          <div className="flex justify-center">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
              userRole === "advisor" ? "bg-amber-500/10 text-amber-500" : userRole === "developer" ? "bg-violet-500/10 text-violet-500" : "bg-primary/10 text-primary"
            }`} title={user?.name || "Admin"}>
              {user?.name?.[0] || "A"}
            </div>
          </div>
        )}

        <Button
          data-testid="logout-btn"
          variant="ghost"
          size="sm"
          title={collapsed ? "Cerrar Sesión" : undefined}
          className={`w-full text-muted-foreground hover:text-red-400 hover:bg-red-400/5 ${collapsed ? "justify-center px-2" : "justify-start gap-2"}`}
          onClick={logout}
        >
          <LogOut size={16} />
          {!collapsed && "Cerrar Sesión"}
        </Button>
      </div>
    </div>
  );

  return (
    <>
      <button
        data-testid="mobile-menu-btn"
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-card border border-border text-foreground"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {mobileOpen && (
        <div className="md:hidden fixed inset-0 bg-black/60 z-40" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={`fixed top-0 left-0 h-full ${w} z-40 transition-all duration-300 md:translate-x-0 ${mobileOpen ? "translate-x-0 w-52" : "-translate-x-full md:translate-x-0"}`}>
        {sidebarContent}
      </aside>
    </>
  );
}
