import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import {
  Send, Trash2, X, Phone, Clock, AlertTriangle, Activity,
  Shield, MessageCircle, CheckCircle, Users,
  Pause, Play, UserCheck, Bot, Brain, Loader2, Bell, RotateCcw, Paperclip
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const STAGE_CONFIG = {
  nuevo: { label: "Contacto inicial", color: "#3B82F6" },
  interesado: { label: "Chat", color: "#8B5CF6" },
  en_negociacion: { label: "En Negociación", color: "#F59E0B" },
  cliente_nuevo: { label: "Leads ganados", color: "#10B981" },
  cliente_activo: { label: "Cartera activa", color: "#A3E635" },
  perdido: { label: "Perdido", color: "#64748B" },
};

const REASON_LABELS = {
  solicitud_usuario: { label: "Solicitud del cliente", color: "bg-amber-500/20 text-amber-400" },
  timeout_bot: { label: "Timeout del bot", color: "bg-red-500/20 text-red-400" },
  bot_transfer: { label: "Bot transfirió a asesor", color: "bg-orange-500/20 text-orange-400" },
  regla_operativa: { label: "Regla operativa", color: "bg-blue-500/20 text-blue-400" },
};

function SessionItem({ s, isActive, onClick }) {
  const timeAgo = s.timestamp ? (() => { const d = (Date.now() - new Date(s.timestamp).getTime()) / 60000; return d < 1 ? "ahora" : d < 60 ? `${Math.floor(d)}m` : d < 1440 ? `${Math.floor(d / 60)}h` : `${Math.floor(d / 1440)}d`; })() : "";
  const hasUnread = !isActive && (s.unread_count || 0) > 0;
  return (
    <button
      data-testid={`session-${s.session_id}`}
      onClick={onClick}
      className={`w-full text-left p-2.5 rounded-lg text-xs transition-all relative ${
        isActive ? "bg-green-500/10 text-green-700 border border-green-500/20" : hasUnread ? "bg-blue-500/5 hover:bg-blue-500/10" : "text-muted-foreground hover:bg-muted"
      }`}
    >
      <div className="flex items-center gap-2">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${s.bot_paused ? "bg-amber-500/10" : "bg-green-500/10"}`}>
          {s.bot_paused ? <UserCheck size={12} className="text-amber-500" /> : <Phone size={12} className="text-green-500" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className={`truncate ${hasUnread ? "font-semibold text-blue-600" : "font-medium text-foreground"}`}>{s.lead_name || "Sin nombre"}</span>
            {s.needs_advisor && (
              <span data-testid={`hot-bell-${s.session_id}`} className="flex-shrink-0 hot-lead-bell" title="Lead caliente - requiere asesor">
                <Bell size={12} className="text-amber-500" />
              </span>
            )}
            {s.has_alert && <AlertTriangle size={11} className="text-red-500 flex-shrink-0" />}
            {s.bot_paused && <span className="text-[9px] px-1 py-0 rounded bg-amber-500/20 text-amber-500 flex-shrink-0">HUMANO</span>}
            {hasUnread && (
              <span data-testid={`unread-badge-${s.session_id}`} className="ml-auto flex-shrink-0 min-w-[18px] h-[18px] px-1.5 rounded-full bg-blue-500 text-white text-[10px] font-bold flex items-center justify-center" title={`${s.unread_count} mensaje(s) sin leer`}>
                {s.unread_count > 9 ? "9+" : s.unread_count}
              </span>
            )}
          </div>
          <p className="truncate text-muted-foreground mt-0.5">{s.lead_phone || s.session_id.replace("wa_", "")}</p>
          {s.lead_channel && <span className="text-[10px] px-1.5 py-0 rounded bg-emerald-500/20 text-emerald-400 inline-block mt-0.5">{s.lead_channel}</span>}
        </div>
      </div>
      <div className="flex items-center justify-between mt-1 pl-9">
        <span className="text-muted-foreground">{timeAgo}</span>
      </div>
      {s.has_alert && (
        <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
      )}
    </button>
  );
}

function AlertPanel({ alerts, onResolve, onTakeOver }) {
  const pending = alerts.filter(a => a.status === "pending");
  if (pending.length === 0) return null;
  return (
    <div data-testid="alert-panel" className="mb-4 bg-red-500/5 border border-red-500/20 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle size={14} className="text-red-500" />
        <p className="text-xs font-semibold text-red-500 uppercase tracking-wider">Solicitudes de Atención Humana ({pending.length})</p>
      </div>
      <div className="space-y-2">
        {pending.map(a => {
          const reason = REASON_LABELS[a.reason] || { label: a.reason || "Desconocido", color: "bg-muted text-muted-foreground" };
          return (
            <div key={a.id} className="bg-card rounded-lg p-3 border border-border">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-xs font-medium text-foreground">{a.lead_name || a.lead_phone}</p>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${reason.color}`}>{reason.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground truncate mb-1">"{a.message}"</p>
                  <div className="flex flex-wrap gap-1.5">
                    {a.product && <span className="text-[10px] px-1.5 py-0 rounded bg-blue-500/15 text-blue-400">{a.product}</span>}
                    {a.channel && <span className="text-[10px] px-1.5 py-0 rounded bg-emerald-500/15 text-emerald-400">{a.channel}</span>}
                    {a.lead_city && <span className="text-[10px] px-1.5 py-0 rounded bg-violet-500/15 text-violet-400">{a.lead_city}</span>}
                    {a.created_at && <span className="text-[10px] text-muted-foreground">{new Date(a.created_at).toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" })}</span>}
                  </div>
                </div>
                <div className="flex gap-1 flex-shrink-0">
                  {!a.bot_paused && (
                    <Button
                      data-testid={`takeover-${a.id}`}
                      size="sm" variant="outline"
                      className="text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 h-7 px-2 text-[10px]"
                      onClick={() => onTakeOver(a.lead_id, a.id)}
                    >
                      <UserCheck size={12} className="mr-1" /> Tomar control
                    </Button>
                  )}
                  <Button
                    data-testid={`resolve-alert-${a.id}`}
                    size="sm" variant="ghost"
                    className="text-green-500 hover:text-green-600 hover:bg-green-500/10 h-7 px-2"
                    onClick={() => onResolve(a.id)}
                  >
                    <CheckCircle size={14} />
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [activeLeadId, setActiveLeadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [leadInfo, setLeadInfo] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [botPaused, setBotPaused] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [advisors, setAdvisors] = useState([]);
  const [showAssignAdvisor, setShowAssignAdvisor] = useState(false);
  const messagesEndRef = useRef(null);
  const pollRef = useRef(null);
  const sseRef = useRef(null);

  const fetchSessions = useCallback(() => {
    axios.get(`${API}/chat/sessions`).then(res => {
      setSessions(res.data.filter(s => s.source === "whatsapp"));
    }).catch(() => {});
  }, []);

  const fetchAlerts = useCallback(() => {
    axios.get(`${API}/chat/alerts`).then(res => setAlerts(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    fetchSessions();
    fetchAlerts();
    axios.get(`${API}/advisors`).then(res => setAdvisors(res.data)).catch(() => {});
  }, [fetchSessions, fetchAlerts]);

  // Server-Sent Events: instant push of new messages for active session
  useEffect(() => {
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    if (!activeSession) return;
    const token = localStorage.getItem("faculty_token");
    if (!token) return;
    const url = `${API}/chat/stream/${activeSession}?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    sseRef.current = es;
    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.type === "message" && payload.message) {
          setMessages(prev => {
            if (prev.some(m => m.id === payload.message.id)) return prev;
            return [...prev, payload.message];
          });
          // Also refresh sidebar so last-message + timestamp updates
          fetchSessions();
        }
      } catch { /* ignore malformed events */ }
    };
    es.onerror = () => {
      // EventSource auto-reconnects; no action needed. Polling below is fallback.
    };
    return () => {
      es.close();
      if (sseRef.current === es) sseRef.current = null;
    };
  }, [activeSession, fetchSessions]);

  useEffect(() => {
    pollRef.current = setInterval(() => {
      fetchSessions();
      fetchAlerts();
      if (activeSession) {
        // Fallback polling in case SSE is unavailable behind strict proxies.
        axios.get(`${API}/chat/history/${activeSession}?_t=${Date.now()}`).then(res => {
          setMessages(res.data);
        }).catch(() => {});
      }
    }, 8000);
    return () => clearInterval(pollRef.current);
  }, [activeSession, fetchSessions, fetchAlerts]);

  useEffect(() => {
    const leadId = searchParams.get("lead_id");
    if (!leadId) {
      if (!initialized) setInitialized(true);
      return;
    }
    // Navigate to lead conversation (works on initial load and subsequent navigations)
    axios.get(`${API}/chat/lead-session/${leadId}`).then(res => {
      setActiveSession(res.data.session_id);
      setActiveLeadId(leadId);
      setMessages(res.data.messages || []);
      if (res.data.lead) {
        const l = res.data.lead;
        setLeadInfo({
          id: l.id, name: l.name, funnel_stage: l.funnel_stage,
          whatsapp: l.whatsapp, city: l.city, email: l.email,
          product_interest: l.product_interest, source: l.source,
          channel: l.channel,
          assigned_advisor_name: l._advisor_name || ""
        });
        setBotPaused(l.bot_paused || false);
      }
      setInitialized(true);
      setSearchParams({}, { replace: true });
    }).catch(() => {
      toast.error("Lead no encontrado");
      setInitialized(true);
    });
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSession = (session) => {
    setActiveSession(session.session_id);
    setActiveLeadId(session.lead_id || null);
    setBotPaused(session.bot_paused || false);
    axios.get(`${API}/chat/history/${session.session_id}`).then(res => setMessages(res.data)).catch(() => {});
    // Mark session as read so unread indicator clears
    axios.post(`${API}/chat/sessions/${session.session_id}/mark-read`).then(() => {
      setSessions(prev => prev.map(x => x.session_id === session.session_id ? { ...x, unread_count: 0 } : x));
    }).catch(() => {});
    if (session.lead_id) {
      axios.get(`${API}/leads/${session.lead_id}`).then(res => {
        const lead = res.data;
        setLeadInfo({
          id: lead.id, name: lead.name, funnel_stage: lead.funnel_stage,
          whatsapp: lead.whatsapp, city: lead.city, email: lead.email,
          product_interest: lead.product_interest, source: lead.source,
          channel: lead.channel,
          assigned_advisor_name: lead._advisor_name || "",
          needs_advisor: lead.needs_advisor && !lead.assigned_advisor
        });
        setBotPaused(lead.bot_paused || false);
      }).catch(() => setLeadInfo({ name: session.lead_name, funnel_stage: null }));
    } else {
      setLeadInfo(null);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || sending || !activeLeadId) return;
    setSending(true);
    const optimisticMsg = { role: "assistant", content: input, timestamp: new Date().toISOString(), sent_by: "crm_agent" };
    setMessages(prev => [...prev, optimisticMsg]);
    const msg = input;
    setInput("");
    try {
      await axios.post(`${API}/chat/whatsapp-reply`, { lead_id: activeLeadId, message: msg });
      toast.success("Mensaje enviado por WhatsApp");
      const res = await axios.get(`${API}/chat/history/${activeSession}`);
      setMessages(res.data);
      fetchSessions();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Error al enviar mensaje");
      setMessages(prev => prev.slice(0, -1));
    }
    setSending(false);
  };

  // Compress image client-side when > 2MB: downscale to max 1920px on longest edge and re-encode as JPEG q=0.85.
  // Returns the original file untouched if it is not an image or it is already small.
  const compressIfImage = (file) => new Promise((resolve) => {
    const TWO_MB = 2 * 1024 * 1024;
    if (!file.type.startsWith("image/") || file.type === "image/gif" || file.size <= TWO_MB) {
      resolve(file); return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const MAX = 1920;
        let { width, height } = img;
        if (width > MAX || height > MAX) {
          const ratio = Math.min(MAX / width, MAX / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
        }
        const canvas = document.createElement("canvas");
        canvas.width = width; canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => {
          if (!blob) { resolve(file); return; }
          const newName = (file.name.replace(/\.[^/.]+$/, "") || "imagen") + ".jpg";
          const compressed = new File([blob], newName, { type: "image/jpeg" });
          resolve(compressed);
        }, "image/jpeg", 0.85);
      };
      img.onerror = () => resolve(file);
      img.src = reader.result;
    };
    reader.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });

  const handleImageUpload = async (e) => {
    const rawFile = e.target.files?.[0];
    if (e.target) e.target.value = "";
    if (!rawFile || !activeLeadId) return;
    // Optional client-side compression for big images
    const originalSize = rawFile.size;
    const file = await compressIfImage(rawFile);
    if (file !== rawFile) {
      const origKb = Math.round(originalSize / 1024);
      const newKb = Math.round(file.size / 1024);
      toast.info(`Imagen comprimida: ${origKb}KB → ${newKb}KB`);
    }
    // Accept images, PDFs/documents, audio and video. WhatsApp Cloud API limits enforced server-side.
    const caption = input.trim();
    setInput("");
    setSending(true);
    const isImage = file.type.startsWith("image/");
    const localUrl = isImage ? URL.createObjectURL(file) : "";
    const mediaType = file.type.startsWith("image/") ? "image"
      : file.type.startsWith("audio/") ? "audio"
      : file.type.startsWith("video/") ? "video"
      : "document";
    const optimistic = {
      role: "assistant",
      content: caption || `[${mediaType}] ${file.name}`,
      ...(isImage ? { image_url: localUrl } : {}),
      media_type: mediaType,
      filename: file.name,
      message_type: mediaType,
      timestamp: new Date().toISOString(),
      sent_by: "crm_agent",
    };
    setMessages(prev => [...prev, optimistic]);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("lead_id", activeLeadId);
      fd.append("caption", caption);
      await axios.post(`${API}/chat/whatsapp-reply-media`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`${mediaType === "image" ? "Imagen" : mediaType === "document" ? "Documento" : mediaType === "audio" ? "Audio" : "Video"} enviado por WhatsApp`);
      const res = await axios.get(`${API}/chat/history/${activeSession}`);
      setMessages(res.data);
      fetchSessions();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Error al enviar archivo");
      setMessages(prev => prev.slice(0, -1));
    }
    setSending(false);
  };

  const deleteMessage = async (msgId, index) => {
    if (!msgId) { setMessages(prev => prev.filter((_, i) => i !== index)); return; }
    try {
      await axios.delete(`${API}/chat/messages/${msgId}`);
      setMessages(prev => prev.filter(m => m.id !== msgId));
      toast.success("Mensaje eliminado");
    } catch { toast.error("Error al eliminar mensaje"); }
  };

  const deleteConversation = async () => {
    if (!activeSession || !window.confirm("¿Eliminar toda la conversación?")) return;
    try {
      await axios.delete(`${API}/chat/sessions/${activeSession}`);
      setMessages([]);
      setActiveSession(null);
      setActiveLeadId(null);
      setLeadInfo(null);
      setBotPaused(false);
      fetchSessions();
      toast.success("Conversación eliminada");
    } catch { toast.error("Error al eliminar conversación"); }
  };

  const resetBotContext = async () => {
    if (!activeLeadId) return;
    if (!window.confirm("¿Resetear el contexto del bot?\n\nEl bot ignorará el historial previo y empezará fresco.\nLos mensajes anteriores seguirán visibles en el CRM.\nSe limpiarán: cantidad, dirección, CI/RUC y producto de interés.")) return;
    try {
      await axios.post(`${API}/leads/${activeLeadId}/reset-bot-context`);
      // Refresh lead info so UI reflects cleared fields
      const res = await axios.get(`${API}/leads/${activeLeadId}`);
      const lead = res.data;
      setLeadInfo(prev => prev ? {
        ...prev,
        quantity_requested: lead.quantity_requested,
        address: lead.address,
        ci_ruc: lead.ci_ruc,
        product_interest: lead.product_interest
      } : prev);
      toast.success("Bot reseteado. Empieza fresco en la próxima interacción.");
    } catch { toast.error("Error al resetear contexto del bot"); }
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.put(`${API}/chat/alerts/${alertId}/resolve`);
      fetchAlerts();
      fetchSessions();
      toast.success("Alerta resuelta");
    } catch { toast.error("Error al resolver alerta"); }
  };

  const takeOverConversation = async (leadId, alertId) => {
    try {
      await axios.put(`${API}/leads/${leadId}/pause-bot`);
      if (alertId) await axios.put(`${API}/chat/alerts/${alertId}/resolve`);
      setBotPaused(true);
      fetchAlerts();
      fetchSessions();
      toast.success("Has tomado el control. El bot está pausado para este lead.");
    } catch { toast.error("Error al tomar control"); }
  };

  const resumeBot = async () => {
    if (!activeLeadId) return;
    try {
      await axios.put(`${API}/leads/${activeLeadId}/resume-bot`);
      setBotPaused(false);
      fetchSessions();
      toast.success("Bot reactivado para este lead.");
    } catch { toast.error("Error al reactivar bot"); }
  };

  const pauseBot = async () => {
    if (!activeLeadId) return;
    try {
      await axios.put(`${API}/leads/${activeLeadId}/pause-bot`);
      setBotPaused(true);
      fetchSessions();
      toast.success("Bot pausado. Tienes el control de la conversación.");
    } catch { toast.error("Error al pausar bot"); }
  };

  const assignAdvisor = async (advisorId) => {
    if (!activeLeadId) return;
    try {
      await axios.put(`${API}/leads/${activeLeadId}/assign`, { advisor_id: advisorId });
      const advisorName = advisorId ? advisors.find(a => a.id === advisorId)?.name || "" : "";
      setLeadInfo(prev => prev ? { ...prev, assigned_advisor_name: advisorName, needs_advisor: advisorId ? false : prev.needs_advisor } : prev);
      setShowAssignAdvisor(false);
      fetchSessions();
      toast.success(advisorId ? "Asesor asignado" : "Asesor removido");
    } catch { toast.error("Error al asignar asesor"); }
  };

  const analyzeConversation = async () => {
    if (!activeSession) return;
    setAnalyzing(true);
    setAiAnalysis(null);
    try {
      const res = await axios.post(`${API}/chat/analyze/${activeSession}`);
      setAiAnalysis(res.data);
      toast.success("Análisis completado");
    } catch (e) { toast.error(e?.response?.data?.detail || "Error en análisis IA"); }
    setAnalyzing(false);
  };

  const applySuggestion = (text) => {
    setInput(text);
  };

  const pendingAlertCount = alerts.filter(a => a.status === "pending").length;

  return (
    <div data-testid="chat-page" className="animate-fade-in-up">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">WhatsApp Bot</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-green-500/10 border border-green-500/20 rounded-full px-3 py-1.5">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-green-600">EN VIVO</span>
          </div>
        </div>
      </div>

      <AlertPanel alerts={alerts} onResolve={resolveAlert} onTakeOver={takeOverConversation} />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" style={{ height: `calc(100vh - ${pendingAlertCount > 0 ? "180px" : "120px"})` }}>
        {/* Sessions Sidebar */}
        <Card className="bg-card border-border rounded-2xl md:col-span-1 hidden md:block overflow-hidden">
          <CardContent className="p-3 h-full flex flex-col">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3 font-semibold">
              Conversaciones ({sessions.length})
            </p>
            <ScrollArea className="flex-1">
              <div className="space-y-1.5">
                {sessions.map(s => (
                  <SessionItem key={s.session_id} s={s} isActive={activeSession === s.session_id} onClick={() => loadSession(s)} />
                ))}
                {sessions.length === 0 && (
                  <div className="text-center py-8">
                    <Phone size={24} className="text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground text-xs">Sin conversaciones</p>
                    <p className="text-muted-foreground text-[10px] mt-1">Las conversaciones aparecen cuando un cliente escribe al bot</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="bg-card border-border rounded-2xl md:col-span-3 flex flex-col overflow-hidden">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            {/* Header with Customer Context Card */}
            <div className="p-3 border-b border-input">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${botPaused ? "bg-amber-500/10" : "bg-green-500/10"}`}>
                    {botPaused ? <UserCheck size={15} className="text-amber-500" /> : <Phone size={15} className="text-green-500" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-foreground font-medium">
                        {leadInfo?.name || "Selecciona una conversación"}
                      </span>
                      {leadInfo?.needs_advisor && (
                        <span data-testid="hot-lead-header-bell" className="hot-lead-bell" title="Lead caliente - asigna un asesor para cerrar la venta">
                          <Bell size={14} className="text-amber-500" />
                        </span>
                      )}
                      {leadInfo?.funnel_stage && (
                        <Badge variant="outline" className="text-[10px] h-5 px-2 leading-none inline-flex items-center whitespace-nowrap" style={{ borderColor: STAGE_CONFIG[leadInfo.funnel_stage]?.color, color: STAGE_CONFIG[leadInfo.funnel_stage]?.color }}>
                          {STAGE_CONFIG[leadInfo.funnel_stage]?.label}
                        </Badge>
                      )}
                      {botPaused && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-500 font-medium animate-pulse">BOT PAUSADO</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {activeLeadId && (
                    <>
                      {botPaused ? (
                        <Button data-testid="resume-bot-btn" variant="outline" size="sm" className="text-green-500 hover:text-green-600 hover:bg-green-500/10 h-8 text-xs" onClick={resumeBot}>
                          <Play size={12} className="mr-1" /> Reactivar Bot
                        </Button>
                      ) : (
                        <Button data-testid="pause-bot-btn" variant="outline" size="sm" className="text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 h-8 text-xs" onClick={pauseBot}>
                          <Pause size={12} className="mr-1" /> Tomar Control
                        </Button>
                      )}
                      <Button data-testid="assign-advisor-btn" variant="outline" size="sm" className="text-orange-500 hover:text-orange-600 hover:bg-orange-500/10 h-8 text-xs" onClick={() => setShowAssignAdvisor(!showAssignAdvisor)}>
                        <UserCheck size={12} className="mr-1" /> Asignar Asesor
                      </Button>
                      <Button data-testid="reset-bot-context-btn" variant="outline" size="sm" className="text-blue-500 hover:text-blue-600 hover:bg-blue-500/10 h-8 text-xs" onClick={resetBotContext} title="Resetea el contexto del bot — el historial sigue visible pero el bot lo ignora y empieza fresco">
                        <RotateCcw size={12} className="mr-1" /> Resetear Bot
                      </Button>
                    </>
                  )}
                  {activeSession && messages.length > 0 && (
                    <Button data-testid="delete-conversation-btn" variant="ghost" size="sm" className="text-muted-foreground hover:text-red-400 h-8" onClick={deleteConversation}>
                      <Trash2 size={14} />
                    </Button>
                  )}
                  {activeSession && messages.length > 0 && (
                    <Button data-testid="analyze-btn" variant="outline" size="sm" disabled={analyzing}
                      className="text-violet-500 hover:text-violet-600 hover:bg-violet-500/10 h-8 text-xs" onClick={analyzeConversation}>
                      {analyzing ? <Loader2 size={12} className="mr-1 animate-spin" /> : <Brain size={12} className="mr-1" />}
                      {analyzing ? "Analizando..." : "IA Análisis"}
                    </Button>
                  )}
                </div>
              </div>
              {/* Customer Context Card - Block 8 */}
              {leadInfo && activeSession && (
                <div data-testid="customer-context-card" className="mt-2 p-2.5 rounded-lg bg-muted/40 border border-border/50">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1.5 text-[11px]">
                    {leadInfo.whatsapp && (
                      <div><span className="text-muted-foreground">Tel:</span> <span className="text-foreground font-medium">{leadInfo.whatsapp}</span></div>
                    )}
                    {leadInfo.email && (
                      <div><span className="text-muted-foreground">Email:</span> <span className="text-foreground font-medium">{leadInfo.email}</span></div>
                    )}
                    {leadInfo.city && (
                      <div><span className="text-muted-foreground">Ciudad:</span> <span className="text-foreground font-medium">{leadInfo.city}</span></div>
                    )}
                    {leadInfo.source && (
                      <div><span className="text-muted-foreground">Fuente:</span> <span className="text-foreground font-medium">{leadInfo.source}</span></div>
                    )}
                    {leadInfo.channel && (
                      <div><span className="text-muted-foreground">Canal:</span> <span className="text-emerald-500 font-medium">{leadInfo.channel}</span></div>
                    )}
                    {leadInfo.product_interest && (
                      <div><span className="text-muted-foreground">Producto:</span> <span className="text-blue-400 font-medium">{leadInfo.product_interest}</span></div>
                    )}
                    {leadInfo.assigned_advisor_name && (
                      <div><span className="text-muted-foreground">Asesor:</span> <span className="text-orange-500 font-medium">{leadInfo.assigned_advisor_name}</span></div>
                    )}
                  </div>
                </div>
              )}
              {/* Bot status indicator */}
              {showAssignAdvisor && activeLeadId && advisors.length > 0 && (
                <div className="mt-2 p-2 rounded-lg bg-orange-500/5 border border-orange-500/20" data-testid="assign-advisor-dropdown">
                  <p className="text-[10px] text-orange-500 font-medium mb-1.5">Asignar asesor a esta conversación:</p>
                  <Select
                    value={leadInfo?.assigned_advisor_name ? advisors.find(a => a.name === leadInfo.assigned_advisor_name)?.id || "none" : "none"}
                    onValueChange={(v) => assignAdvisor(v === "none" ? "" : v)}
                  >
                    <SelectTrigger className="h-8 text-xs bg-card border-orange-500/30">
                      <SelectValue placeholder="Seleccionar asesor" />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-input">
                      <SelectItem value="none">Sin asesor</SelectItem>
                      {advisors.map(a => <SelectItem key={a.id} value={a.id}>{a.name} {a.specialization ? `(${a.specialization})` : ""}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {activeSession && (
                <div className={`mt-2 flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-md ${botPaused ? "bg-amber-500/10 text-amber-500" : "bg-green-500/10 text-green-500"}`}>
                  {botPaused ? (
                    <>
                      <UserCheck size={10} />
                      <span>Modo humano activo — el bot NO responde automáticamente. Tus mensajes se envían directamente por WhatsApp.</span>
                    </>
                  ) : (
                    <>
                      <Bot size={10} />
                      <span>Bot activo — respondiendo automáticamente{leadInfo?.product_interest ? ` (especializado en ${leadInfo.product_interest})` : ""}. Puedes tomar el control en cualquier momento.</span>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* AI Analysis Panel - Block 13 */}
            {aiAnalysis && (
              <div data-testid="ai-analysis-panel" className="p-3 border-b border-input bg-violet-500/5">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Brain size={14} className="text-violet-500" />
                    <span className="text-xs font-semibold text-violet-500 uppercase tracking-wider">Análisis IA</span>
                  </div>
                  <button onClick={() => setAiAnalysis(null)} className="p-0.5 rounded hover:bg-muted text-muted-foreground"><X size={12} /></button>
                </div>
                <p className="text-xs text-foreground mb-2">{aiAnalysis.resumen}</p>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {aiAnalysis.sentimiento && <span className={`text-[10px] px-1.5 py-0 rounded ${aiAnalysis.sentimiento === "positivo" ? "bg-green-500/15 text-green-500" : aiAnalysis.sentimiento === "negativo" ? "bg-red-500/15 text-red-400" : "bg-muted text-muted-foreground"}`}>Sentimiento: {aiAnalysis.sentimiento}</span>}
                  {aiAnalysis.nivel_urgencia && <span className={`text-[10px] px-1.5 py-0 rounded ${aiAnalysis.nivel_urgencia === "alto" ? "bg-red-500/15 text-red-400" : aiAnalysis.nivel_urgencia === "medio" ? "bg-amber-500/15 text-amber-500" : "bg-muted text-muted-foreground"}`}>Urgencia: {aiAnalysis.nivel_urgencia}</span>}
                  {aiAnalysis.interes_producto && <span className="text-[10px] px-1.5 py-0 rounded bg-blue-500/15 text-blue-400">Producto: {aiAnalysis.interes_producto}</span>}
                  {aiAnalysis.etapa_sugerida && <span className="text-[10px] px-1.5 py-0 rounded bg-violet-500/15 text-violet-400">Etapa: {aiAnalysis.etapa_sugerida}</span>}
                  {aiAnalysis.temas_clave?.map((t, i) => <span key={i} className="text-[10px] px-1.5 py-0 rounded bg-muted text-muted-foreground">{t}</span>)}
                </div>
                {aiAnalysis.respuestas_sugeridas?.length > 0 && (
                  <div>
                    <p className="text-[10px] text-muted-foreground mb-1">Respuestas sugeridas:</p>
                    <div className="space-y-1">
                      {aiAnalysis.respuestas_sugeridas.map((s, i) => (
                        <button key={i} data-testid={`suggestion-${i}`} onClick={() => applySuggestion(s)}
                          className="w-full text-left text-[11px] p-1.5 rounded bg-muted/50 text-foreground/80 hover:bg-violet-500/10 hover:text-violet-500 transition-colors truncate">
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-2 pb-4">
                {!activeSession && messages.length === 0 && (
                  <div className="text-center py-12">
                    <Activity size={40} className="text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">Selecciona una conversación de WhatsApp</p>
                    <p className="text-muted-foreground text-xs mt-1">Los mensajes del bot aparecen en tiempo real</p>
                  </div>
                )}
                {activeSession && messages.length === 0 && (
                  <div className="text-center py-12">
                    <Phone size={40} className="text-green-500/30 mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">Esperando mensajes...</p>
                  </div>
                )}
                {messages.map((msg, i) => {
                  const isUser = msg.role === "user";
                  const isCrmAgent = msg.sent_by === "crm_agent";
                  return (
                    <div key={msg.id || i} className={`group flex gap-2 mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
                      {!isUser && (
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
                          isCrmAgent ? "bg-blue-500/10" : "bg-green-500/10"
                        }`}>
                          {isCrmAgent ? <Shield size={13} className="text-blue-500" /> : <Phone size={13} className="text-green-500" />}
                        </div>
                      )}
                      <div className="relative max-w-[80%]">
                        <div className={`px-4 py-2.5 text-sm ${isUser ? "chat-bubble-user" : "chat-bubble-bot"} ${isCrmAgent ? "!border-l-2 !border-l-blue-500" : ""}`} data-testid={`chat-msg-${i}`}>
                          {isCrmAgent && <p className="text-[10px] text-blue-500 font-medium mb-1">Agente CRM</p>}
                          <div className="whitespace-pre-wrap">
                            {msg.image_url ? (
                              <>
                                <img
                                  src={msg.image_url}
                                  alt={msg.content || "Imagen enviada"}
                                  className="rounded-lg max-w-full max-h-60 object-cover cursor-pointer mb-1"
                                  onClick={() => window.open(msg.image_url, "_blank")}
                                  data-testid={`chat-msg-image-${i}`}
                                />
                                {msg.content && msg.content !== "[imagen]" && <p>{msg.content}</p>}
                              </>
                            ) : msg.media_type === "document" && msg.media_url ? (
                              <>
                                <a
                                  href={msg.media_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  data-testid={`chat-msg-doc-${i}`}
                                  className="flex items-center gap-2 p-2 rounded-lg bg-background/40 border border-border hover:bg-background/60 transition-colors mb-1"
                                >
                                  <span className="w-8 h-8 rounded bg-red-500/15 text-red-500 flex items-center justify-center text-[10px] font-bold shrink-0">PDF</span>
                                  <span className="text-xs truncate">{msg.filename || "documento"}</span>
                                </a>
                                {msg.content && !msg.content.startsWith("[") && <p>{msg.content}</p>}
                              </>
                            ) : msg.media_type === "audio" && msg.media_url ? (
                              <>
                                <audio controls src={msg.media_url} data-testid={`chat-msg-audio-${i}`} className="max-w-full mb-1" preload="metadata">Tu navegador no soporta audio.</audio>
                                {msg.content && !msg.content.startsWith("[") && <p>{msg.content}</p>}
                              </>
                            ) : msg.media_type === "video" && msg.media_url ? (
                              <>
                                <video controls src={msg.media_url} data-testid={`chat-msg-video-${i}`} className="rounded-lg max-w-full max-h-60 mb-1" preload="metadata">Tu navegador no soporta video.</video>
                                {msg.content && !msg.content.startsWith("[") && <p>{msg.content}</p>}
                              </>
                            ) : msg.content && msg.content.includes("[Imagen:") ? (
                              <>
                                <p>{msg.content.replace(/\n?\[Imagen:.*?\]/g, "")}</p>
                                {(() => {
                                  const match = msg.content.match(/\[Imagen:\s*(.*?)\]/);
                                  if (match && match[1]) {
                                    const src = match[1].startsWith("/api/") ? `${process.env.REACT_APP_BACKEND_URL}${match[1]}` : match[1];
                                    return <img src={src} alt="Campaña" className="mt-2 rounded-lg max-w-full max-h-48 object-cover cursor-pointer" onClick={() => window.open(src, "_blank")} />;
                                  }
                                  return null;
                                })()}
                              </>
                            ) : (
                              <p>{msg.content}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-[10px] text-muted-foreground">
                              {msg.timestamp ? `${new Date(msg.timestamp).toLocaleDateString("es-EC", { day: "2-digit", month: "2-digit", year: "2-digit" })} · ${new Date(msg.timestamp).toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" })}` : ""}
                            </p>
                            {msg.response_time_ms && (
                              <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                                <Clock size={9} /> {(msg.response_time_ms / 1000).toFixed(1)}s
                              </p>
                            )}
                          </div>
                        </div>
                        <button
                          data-testid={`delete-msg-${i}`}
                          onClick={() => deleteMessage(msg.id, i)}
                          className="absolute -top-2 -right-2 hidden group-hover:flex w-5 h-5 rounded-full bg-red-500/90 text-white items-center justify-center text-xs hover:bg-red-600 transition-all"
                        >
                          <X size={10} />
                        </button>
                      </div>
                      {isUser && (
                        <div className="w-7 h-7 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0 mt-1">
                          <Phone size={13} className="text-green-500" />
                        </div>
                      )}
                    </div>
                  );
                })}
                {sending && (
                  <div className="flex gap-2">
                    <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center">
                      <Shield size={13} className="text-blue-500" />
                    </div>
                    <div className="chat-bubble-bot px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input - CRM Agent Reply */}
            <div className="p-3 border-t border-input">
              <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
                <input
                  data-testid="chat-image-input"
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/webp,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,audio/*,video/mp4,video/3gpp"
                  id="chat-image-file"
                  className="hidden"
                  onChange={handleImageUpload}
                  disabled={sending || !activeSession}
                />
                <Button
                  data-testid="chat-attach-btn"
                  type="button"
                  variant="outline"
                  className="h-10 w-10 p-0 shrink-0"
                  disabled={sending || !activeSession}
                  onClick={() => document.getElementById("chat-image-file")?.click()}
                  title="Adjuntar archivo (imagen, PDF, audio, video)"
                >
                  <Paperclip size={15} />
                </Button>
                <Input
                  data-testid="chat-input"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={activeSession ? (botPaused ? "Escribe como agente humano..." : "Responder como agente por WhatsApp...") : "Selecciona una conversación..."}
                  className="flex-1 bg-muted/50 border-input text-foreground h-10"
                  disabled={sending || !activeSession}
                />
                <Button
                  data-testid="chat-send-btn"
                  type="submit"
                  disabled={sending || !input.trim() || !activeSession}
                  className={`${botPaused ? "bg-amber-600 hover:bg-amber-700" : "bg-green-600 hover:bg-green-700"} text-white h-10 px-4 rounded-lg`}
                >
                  <Send size={15} />
                </Button>
              </form>
              {activeSession && (
                <p className="text-[10px] text-muted-foreground mt-1.5 flex items-center gap-1">
                  {botPaused ? (
                    <><UserCheck size={9} className="text-amber-500" /> Modo humano — tu mensaje se envía directamente al WhatsApp del cliente</>
                  ) : (
                    <><Shield size={9} className="text-blue-500" /> Tu respuesta se envía directamente al WhatsApp del cliente como agente humano</>
                  )}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
