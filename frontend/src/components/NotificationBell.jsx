import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API, useAuth } from "@/App";
import { Bell, X, AlertTriangle, UserCheck, MessageCircle, CheckCircle, Volume2, VolumeX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";

const REASON_LABELS = {
  solicitud_usuario: "Solicitud del cliente",
  timeout_bot: "Timeout del bot",
  bot_transfer: "Bot transfirió a asesor",
  regla_operativa: "Regla operativa",
  new_message: "Nuevo mensaje",
};

export default function NotificationBell() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem("fk_sound") !== "off");
  const prevCountRef = useRef(0);
  const audioRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [alertRes, notifRes] = await Promise.all([
        axios.get(`${API}/chat/alerts`),
        axios.get(`${API}/advisors/notifications`),
      ]);
      setAlerts(alertRes.data.filter(a => a.status === "pending"));
      setNotifications(notifRes.data.filter(n => !n.read));
    } catch (err) { /* fetch error ignored */ }
  }, []);

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 6000);
    return () => clearInterval(iv);
  }, [fetchData]);

  const totalCount = alerts.length + notifications.length;

  useEffect(() => {
    if (totalCount > prevCountRef.current && soundEnabled && prevCountRef.current >= 0) {
      try {
        if (!audioRef.current) {
          audioRef.current = new Audio("data:audio/wav;base64,UklGRlgEAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YTQEAAB/e3p4d3V0c3Fwbm1raWhmZGJgXlxaWFZUUlBOTEpIRkRCQD49Ozo5ODc2NTQ0MzMyMjExMTExMTExMjIyMzM0NTU2Nzg5Ojs8PT4/QEJDREZIS0xOUFJUVlhcXmBiZGhpbG5wcnR1eHp7fn+BgoSGh4mLjI6PkJKTlJWWl5iYmZqam5ybm5ubm5qamZmYl5aVlJOSkI+OjIuJh4aEgoF/fXt5d3V0cnBubGppZ2VjYWBdW1pYV1VUUlFPTkxLSkhHRkVEQ0JBQD8/Pj49PDs7Ozo6OTk5OTk5OTk5Ojo6Ozs8PD0+Pj9AQUJDREZHR0lKTE1PUFJTVVdYWlxeYGFjZWdpa2xucHFzdXd4ent9f4CChIWHiImLjI2Oj5CRkpOTlJSVlZWVlZWUlJOTkpGQj46NjIuKiIeGhIKBf359e3l4dnRzcXBubGtpZ2ZkY2FgXl1bWllXVlVUU1JRUE9OTUxMS0pKSUlISEdHRkZGRkZGRkZGRkdHR0hISUlKS0tMTU5OT1BRVFJTVFVWV1lbXF5gYWNlZ2lrbW9xc3V3eXt9f4GDhYeJi42Oj5GSlJWXmJmam5ydn56fn5+fnp6dnJuamJeVlJKQjo2LiYeEgoB+fHp4dnRycG5samlnZWNhX15cWlhXVVRSUU9OTUxLSkpJSEhHR0dHR0dHR0dIiElKS0xNTk9QUVJTVFVWV1lbXF5gYmRmaGpsbm9xc3V3eXt9f4CCg4WHiYqMjY+QkpOUlZaXmJiZmZqampqampqZmZiXlpWUkpGPjo2LiYiGhIKAf317enl3dXRycXBubWxqaWhnZmVjYmFgX15dXFtbWlpZWVhYWFhYWFhYWFlZWVpaW1tcXF1eX2BhYmNkZmdoaWpsbW5vcXJzdXZ4eXt8fn+BgoSGh4mKjI2Oj5GSlJWWl5iZmpucnZ2enp+fn5+fn56enZybmpmYlpWUkpGPjoyLiYeGhIKAf316eHd1c3JwbmxraWdmZGJhX15cW1lYV1ZVVFNSUVBQTk5NTU1MTExMTExMTExMTE1NTU5OT1BQUVJTVFVWVlhZWltcXl9hYmRlZ2hqa2xucHFzdHZ4eXt9foCAgoOFh4iKi4yOj5CRkpOUlZaWl5iYmJmZmZmZmZiYmJeWlZSTkpGQj46Mi4mHhoSDgX9+fHt5eHZ1c3JxcG5tbGtqaGdmZWRjYmFgX19eXl1dXFxcXFxcXFxcXF1dXV5eX19gYWFiY2RlZmZnaGlqa2xtbm9wcXJzdHV2d3h5ent8fX5/gIGCg4SFhoeIiYqLjI2Oj4+QkZGSkpOTk5OTk5OTkpKRkZCQj46NjYyLiomIh4aFhIOCgYB/fn18e3p5eHd2dnV0dHNzc3JycnJycnJyc3Nzc3R0dXV2d3d4eXl6e3x8fX5/f4CBgoODhIWGh4eIiYqLi4yNjY6Pj5CQkZGRkpKSkpKSkpKSkZGRkJCPj4+OjY2MjIuLioqJiYiIh4eGhoWFhYSEhISDg4ODg4ODg4ODg4ODhISEhIWFhYaGh4eIiIiJiYqKi4uMjI2NjY6Ojo+Pj5CQkJCRkZGRkZGRkZCQkJCPj4+OjoyA");
        }
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(() => {});
      } catch (err) { console.error("Audio play error:", err); }
    }
    prevCountRef.current = totalCount;
  }, [totalCount, soundEnabled]);

  const toggleSound = () => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    localStorage.setItem("fk_sound", next ? "on" : "off");
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.put(`${API}/chat/alerts/${alertId}/resolve`);
      fetchData();
      toast.success("Alerta resuelta");
    } catch (err) { toast.error("Error al resolver alerta"); }
  };

  const markRead = async (notifId) => {
    try {
      await axios.put(`${API}/advisors/notifications/${notifId}/read`);
      fetchData();
    } catch (err) { console.error("Mark read error:", err); }
  };

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/advisors/notifications/read-all`);
      fetchData();
      toast.success("Notificaciones leídas");
    } catch (err) { console.error("Mark all read error:", err); }
  };

  const timeAgo = (ts) => {
    if (!ts) return "";
    const d = (Date.now() - new Date(ts).getTime()) / 60000;
    if (d < 1) return "ahora";
    if (d < 60) return `${Math.floor(d)}m`;
    if (d < 1440) return `${Math.floor(d / 60)}h`;
    return `${Math.floor(d / 1440)}d`;
  };

  return (
    <div className="relative">
      <button
        data-testid="notification-bell"
        onClick={() => setOpen(!open)}
        className={`relative p-2 rounded-lg transition-all ${totalCount > 0 ? "text-red-500 bg-red-500/10 hover:bg-red-500/20 animate-pulse" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}
      >
        <Bell size={20} />
        {totalCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {totalCount > 9 ? "9+" : totalCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div data-testid="notification-panel" className="fixed left-14 md:left-56 bottom-16 w-80 max-h-[70vh] bg-popover border border-border rounded-xl shadow-2xl z-50 overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b border-border">
              <h3 className="text-sm font-semibold text-foreground">Notificaciones</h3>
              <div className="flex items-center gap-1">
                <button onClick={toggleSound} className="p-1 rounded hover:bg-muted text-muted-foreground" title={soundEnabled ? "Silenciar" : "Activar sonido"}>
                  {soundEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
                </button>
                {notifications.length > 0 && (
                  <button onClick={markAllRead} className="text-[10px] text-primary hover:underline px-1">Leer todo</button>
                )}
                <button onClick={() => setOpen(false)} className="p-1 rounded hover:bg-muted text-muted-foreground"><X size={14} /></button>
              </div>
            </div>
            <ScrollArea className="max-h-[calc(70vh-50px)]">
              <div className="p-2 space-y-1.5">
                {/* Handover Alerts */}
                {alerts.map(a => (
                  <div key={a.id} className="p-2.5 rounded-lg bg-red-500/5 border border-red-500/20 cursor-pointer hover:bg-red-500/10 transition-colors" onClick={() => { setOpen(false); navigate(`/chat?lead_id=${a.lead_id}`); }}>
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground">{a.lead_name || a.lead_phone}</p>
                        <p className="text-[10px] text-red-400">{REASON_LABELS[a.reason] || a.reason}</p>
                        <p className="text-[10px] text-muted-foreground truncate mt-0.5">"{a.message}"</p>
                        <span className="text-[10px] text-muted-foreground">{timeAgo(a.created_at)}</span>
                      </div>
                      <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-green-500 hover:bg-green-500/10" onClick={(e) => { e.stopPropagation(); resolveAlert(a.id); }} data-testid={`resolve-notif-${a.id}`}>
                        <CheckCircle size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
                {/* Advisor Notifications */}
                {notifications.map(n => {
                  const isUrgent = n.type === "advisor_request" || n.type === "hot_lead";
                  const Icon = isUrgent ? AlertTriangle : MessageCircle;
                  const colorClass = isUrgent ? "text-orange-500" : "text-blue-500";
                  const bgClass = isUrgent ? "bg-orange-500/5 border-orange-500/20 hover:bg-orange-500/10" : "bg-blue-500/5 border border-blue-500/10 hover:bg-blue-500/10";
                  return (
                    <div key={n.id} className={`p-2.5 rounded-lg border ${bgClass} transition-colors cursor-pointer`} onClick={() => { markRead(n.id); setOpen(false); if (n.lead_id) navigate(`/chat?lead_id=${n.lead_id}`); }}>
                      <div className="flex items-start gap-2">
                        <Icon size={14} className={`${colorClass} mt-0.5 flex-shrink-0`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-foreground">{n.title || n.lead_name || "Lead"}</p>
                          <p className="text-[10px] text-muted-foreground truncate">{n.message || "Nuevo mensaje"}</p>
                          <span className="text-[10px] text-muted-foreground">{timeAgo(n.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {totalCount === 0 && (
                  <div className="text-center py-6 text-muted-foreground">
                    <Bell size={24} className="mx-auto mb-2 opacity-30" />
                    <p className="text-xs">Sin notificaciones</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </>
      )}
    </div>
  );
}
