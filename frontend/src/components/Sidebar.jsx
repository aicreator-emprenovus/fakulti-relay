import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { LayoutDashboard, Users, Gamepad2, Heart, MessageSquare, FileText, Upload, Settings, LogOut, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

const navItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/leads", icon: Users, label: "Leads" },
  { path: "/games", icon: Gamepad2, label: "Juegos" },
  { path: "/loyalty", icon: Heart, label: "Fidelizacion" },
  { path: "/chat", icon: MessageSquare, label: "Chat IA" },
  { path: "/quotations", icon: FileText, label: "Cotizaciones" },
  { path: "/bulk", icon: Upload, label: "Carga / Descarga" },
  { path: "/settings", icon: Settings, label: "Productos" },
];

export default function Sidebar({ currentPath }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#080808] border-r border-white/5">
      <div className="p-4 flex items-center gap-3 border-b border-white/5">
        <img src={LOGO_URL} alt="Faculty" className="h-10 w-auto" />
        <div className="hidden md:block">
          <p className="text-xs text-zinc-500 tracking-wider uppercase">CRM Panel</p>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map(item => {
          const isActive = currentPath === item.path;
          return (
            <button
              key={item.path}
              data-testid={`nav-${item.path.replace("/", "") || "dashboard"}`}
              onClick={() => handleNav(item.path)}
              className={`sidebar-item w-full flex items-center gap-3 text-sm font-medium transition-all ${
                isActive
                  ? "active text-lime-400"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-lime-400/10 flex items-center justify-center text-lime-400 text-sm font-bold">
            {user?.name?.[0] || "A"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name || "Admin"}</p>
            <p className="text-xs text-zinc-500 truncate">{user?.email || ""}</p>
          </div>
        </div>
        <Button
          data-testid="logout-btn"
          variant="ghost"
          size="sm"
          className="w-full text-zinc-400 hover:text-red-400 hover:bg-red-400/5 justify-start gap-2"
          onClick={logout}
        >
          <LogOut size={16} />
          Cerrar Sesion
        </Button>
      </div>
    </div>
  );

  return (
    <>
      <button
        data-testid="mobile-menu-btn"
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-white"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {mobileOpen && (
        <div className="md:hidden fixed inset-0 bg-black/60 z-40" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={`fixed top-0 left-0 h-full w-64 z-40 transition-transform duration-300 md:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {sidebarContent}
      </aside>
    </>
  );
}
