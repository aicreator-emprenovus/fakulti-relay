import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Send, MessageSquare, Bot, User, Trash2, X,
  Phone, Wifi, Clock, AlertTriangle, CheckCircle,
  MessageCircle, Activity, Shield
} from "lucide-react";

const STAGE_CONFIG = {
  nuevo: { label: "Prospecto", color: "#3B82F6" },
  interesado: { label: "Interesado", color: "#8B5CF6" },
  en_negociacion: { label: "En Negociacion", color: "#F59E0B" },
  cliente_nuevo: { label: "Cliente Nuevo", color: "#10B981" },
  cliente_activo: { label: "Cliente Activo", color: "#A3E635" },
  perdido: { label: "Perdido", color: "#64748B" },
};

function StatsBar({ stats, alertCount }) {
  return (
    <div data-testid="whatsapp-stats-bar" className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2.5">
        <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
          <Wifi size={15} className="text-green-500" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Activas 24h</p>
          <p data-testid="stat-active" className="text-sm font-bold text-foreground">{stats.active_conversations_24h ?? 0}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2.5">
        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <Clock size={15} className="text-blue-500" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Resp. Prom.</p>
          <p data-testid="stat-response-time" className="text-sm font-bold text-foreground">{stats.avg_response_time_ms ? `${(stats.avg_response_time_ms / 1000).toFixed(1)}s` : "—"}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2.5">
        <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
          <MessageCircle size={15} className="text-purple-500" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Msgs Hoy</p>
          <p data-testid="stat-msgs-today" className="text-sm font-bold text-foreground">{stats.messages_today ?? 0}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2.5 relative">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${alertCount > 0 ? "bg-red-500/10" : "bg-muted"}`}>
          <AlertTriangle size={15} className={alertCount > 0 ? "text-red-500" : "text-muted-foreground"} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Alertas</p>
          <p data-testid="stat-alerts" className={`text-sm font-bold ${alertCount > 0 ? "text-red-500" : "text-foreground"}`}>{alertCount}</p>
        </div>
        {alertCount > 0 && <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />}
      </div>
    </div>
  );
}

function SessionItem({ s, isActive, onClick }) {
  const isWA = s.source === "whatsapp";
  const timeAgo = s.timestamp ? formatTimeAgo(s.timestamp) : "";
  return (
    <button
      onClick={onClick}
      data-testid={`session-${s.session_id}`}
      className={`w-full text-left p-2.5 rounded-lg text-xs transition-all relative ${
        isActive ? "bg-primary/10 text-primary border border-primary/20" : "text-muted-foreground hover:bg-muted"
      }`}
    >
      <div className="flex items-center gap-2">
        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
          isWA ? "bg-green-500/10" : "bg-primary/10"
        }`}>
          {isWA ? <Phone size={11} className="text-green-500" /> : <Bot size={11} className="text-primary" />}
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate font-medium text-foreground">{s.lead_name || s.lead_phone || "Sin nombre"}</p>
          <p className="truncate text-muted-foreground mt-0.5">{s.last_message?.slice(0, 35) || "Sin mensajes"}</p>
        </div>
      </div>
      <div className="flex items-center justify-between mt-1.5 pl-8">
        <span className="text-muted-foreground">{s.message_count} msgs</span>
        <span className="text-muted-foreground">{timeAgo}</span>
      </div>
      {s.has_alert && (
        <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
      )}
      {isWA && (
        <Badge variant="outline" className="absolute top-1.5 right-5 text-[9px] h-4 border-green-500/30 text-green-600">WA</Badge>
      )}
    </button>
  );
}

function AlertPanel({ alerts, onResolve }) {
  const pending = alerts.filter(a => a.status === "pending");
  if (pending.length === 0) return null;
  return (
    <div data-testid="alert-panel" className="mb-4 bg-red-500/5 border border-red-500/20 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle size={14} className="text-red-500" />
        <p className="text-xs font-semibold text-red-500 uppercase tracking-wider">Solicitudes de Agente Humano</p>
      </div>
      <div className="space-y-2">
        {pending.map(a => (
          <div key={a.id} className="flex items-center justify-between bg-card rounded-lg p-2 border border-border">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{a.lead_name || a.lead_phone}</p>
              <p className="text-xs text-muted-foreground truncate">"{a.message}"</p>
            </div>
            <Button
              data-testid={`resolve-alert-${a.id}`}
              size="sm" variant="ghost"
              className="text-green-500 hover:text-green-600 hover:bg-green-500/10 h-7 px-2"
              onClick={() => onResolve(a.id)}
            >
              <CheckCircle size={14} />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTimeAgo(ts) {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "ahora";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
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
  const [stats, setStats] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [sessionSource, setSessionSource] = useState("chat_ia");
  const [filter, setFilter] = useState("all"); // all, whatsapp, chat_ia
  const messagesEndRef = useRef(null);
  const pollRef = useRef(null);

  const fetchSessions = useCallback(() => {
    axios.get(`${API}/chat/sessions`).then(res => setSessions(res.data)).catch(() => {});
  }, []);

  const fetchStats = useCallback(() => {
    axios.get(`${API}/chat/whatsapp-stats`).then(res => setStats(res.data)).catch(() => {});
  }, []);

  const fetchAlerts = useCallback(() => {
    axios.get(`${API}/chat/alerts`).then(res => setAlerts(res.data)).catch(() => {});
  }, []);

  // Initial load
  useEffect(() => {
    fetchSessions();
    fetchStats();
    fetchAlerts();
  }, [fetchSessions, fetchStats, fetchAlerts]);

  // Auto-poll every 10s
  useEffect(() => {
    pollRef.current = setInterval(() => {
      fetchSessions();
      fetchStats();
      fetchAlerts();
      // Refresh active session messages if it's a WhatsApp session
      if (activeSession?.startsWith("wa_")) {
        axios.get(`${API}/chat/history/${activeSession}`).then(res => {
          setMessages(prev => {
            if (res.data.length !== prev.length) return res.data;
            return prev;
          });
        }).catch(() => {});
      }
    }, 10000);
    return () => clearInterval(pollRef.current);
  }, [activeSession, fetchSessions, fetchStats, fetchAlerts]);

  // Handle lead_id from URL params
  useEffect(() => {
    if (initialized) return;
    const leadId = searchParams.get("lead_id");
    if (leadId) {
      axios.get(`${API}/chat/lead-session/${leadId}`).then(res => {
        setActiveSession(res.data.session_id);
        setActiveLeadId(leadId);
        setMessages(res.data.messages || []);
        if (res.data.lead) {
          setLeadInfo({ id: res.data.lead.id, name: res.data.lead.name, funnel_stage: res.data.lead.funnel_stage });
        }
        const meta = res.data.session_id?.startsWith("wa_") ? "whatsapp" : "chat_ia";
        setSessionSource(meta);
        setInitialized(true);
        setSearchParams({}, { replace: true });
      }).catch(() => {
        toast.error("Lead no encontrado");
        setInitialized(true);
      });
    } else {
      setInitialized(true);
    }
  }, [searchParams, initialized, setSearchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSession = (session) => {
    setActiveSession(session.session_id);
    setActiveLeadId(session.lead_id || null);
    setSessionSource(session.source || "chat_ia");
    axios.get(`${API}/chat/history/${session.session_id}`).then(res => setMessages(res.data)).catch(() => {});
    if (session.lead_id) {
      axios.get(`${API}/leads`).then(res => {
        const lead = res.data.find(l => l.id === session.lead_id);
        if (lead) setLeadInfo({ id: lead.id, name: lead.name, funnel_stage: lead.funnel_stage, whatsapp: lead.whatsapp });
        else setLeadInfo({ name: session.lead_name, funnel_stage: null });
      }).catch(() => setLeadInfo({ name: session.lead_name, funnel_stage: null }));
    } else {
      setLeadInfo(null);
    }
  };

  const startNewSession = () => {
    const sid = `session_${Date.now()}`;
    setActiveSession(sid);
    setActiveLeadId(null);
    setMessages([]);
    setLeadInfo(null);
    setSessionSource("chat_ia");
  };

  const sendMessage = async () => {
    if (!input.trim() || sending) return;

    // WhatsApp reply via CRM
    if (sessionSource === "whatsapp" && activeLeadId) {
      setSending(true);
      const userMsg = { role: "assistant", content: input, timestamp: new Date().toISOString(), sent_by: "crm_agent" };
      setMessages(prev => [...prev, userMsg]);
      setInput("");
      try {
        await axios.post(`${API}/chat/whatsapp-reply`, { lead_id: activeLeadId, message: input });
        toast.success("Mensaje enviado por WhatsApp");
        // Refresh messages
        const res = await axios.get(`${API}/chat/history/${activeSession}`);
        setMessages(res.data);
        fetchSessions();
      } catch (err) {
        toast.error(err?.response?.data?.detail || "Error al enviar mensaje");
        setMessages(prev => prev.slice(0, -1));
      }
      setSending(false);
      return;
    }

    // Regular Chat IA
    const sessionId = activeSession || `session_${Date.now()}`;
    if (!activeSession) setActiveSession(sessionId);

    const userMsg = { role: "user", content: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const payload = { session_id: sessionId, message: input };
      if (activeLeadId) payload.lead_id = activeLeadId;
      const res = await axios.post(`${API}/chat/message`, payload);
      const botMsg = { role: "assistant", content: res.data.response, timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, botMsg]);
      if (res.data.lead) {
        setLeadInfo(res.data.lead);
        if (!activeLeadId) setActiveLeadId(res.data.lead.id);
      }
      fetchSessions();
    } catch {
      toast.error("Error al enviar mensaje");
      setMessages(prev => [...prev, { role: "assistant", content: "Error al procesar tu mensaje. Intenta de nuevo.", timestamp: new Date().toISOString() }]);
    }
    setSending(false);
  };

  const deleteMessage = async (msgId, index) => {
    if (!msgId) {
      setMessages(prev => prev.filter((_, i) => i !== index));
      return;
    }
    try {
      await axios.delete(`${API}/chat/messages/${msgId}`);
      setMessages(prev => prev.filter(m => m.id !== msgId));
      toast.success("Mensaje eliminado");
    } catch { toast.error("Error al eliminar mensaje"); }
  };

  const deleteConversation = async () => {
    if (!activeSession) return;
    if (!window.confirm("Eliminar toda la conversacion?")) return;
    try {
      await axios.delete(`${API}/chat/sessions/${activeSession}`);
      setMessages([]);
      setActiveSession(null);
      setActiveLeadId(null);
      setLeadInfo(null);
      fetchSessions();
      toast.success("Conversacion eliminada");
    } catch { toast.error("Error al eliminar conversacion"); }
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.put(`${API}/chat/alerts/${alertId}/resolve`);
      fetchAlerts();
      fetchSessions();
      toast.success("Alerta resuelta");
    } catch { toast.error("Error al resolver alerta"); }
  };

  const filteredSessions = sessions.filter(s => {
    if (filter === "whatsapp") return s.source === "whatsapp";
    if (filter === "chat_ia") return s.source !== "whatsapp";
    return true;
  });

  const pendingAlertCount = alerts.filter(a => a.status === "pending").length;

  return (
    <div data-testid="chat-page" className="animate-fade-in-up">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Chat IA</h1>
          <p className="text-sm text-muted-foreground">Asesor Virtual + Monitor WhatsApp en Tiempo Real</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-muted rounded-full p-0.5">
            {[
              { key: "all", label: "Todos" },
              { key: "whatsapp", label: "WhatsApp", icon: Phone },
              { key: "chat_ia", label: "Chat IA", icon: Bot },
            ].map(f => (
              <button
                key={f.key}
                data-testid={`filter-${f.key}`}
                onClick={() => setFilter(f.key)}
                className={`text-xs px-3 py-1.5 rounded-full transition-all font-medium ${
                  filter === f.key ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f.icon && <f.icon size={11} className="inline mr-1" />}{f.label}
              </button>
            ))}
          </div>
          <Button data-testid="new-chat-btn" onClick={startNewSession} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 h-9 text-xs">
            <MessageSquare size={14} className="mr-1" /> Nueva
          </Button>
        </div>
      </div>

      <StatsBar stats={stats} alertCount={pendingAlertCount} />
      <AlertPanel alerts={alerts} onResolve={resolveAlert} />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" style={{ height: "calc(100vh - " + (pendingAlertCount > 0 ? "380px" : "300px") + ")" }}>
        <Card className="bg-card border-border rounded-2xl md:col-span-1 hidden md:block overflow-hidden">
          <CardContent className="p-3 h-full flex flex-col">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3 font-semibold">
              Conversaciones ({filteredSessions.length})
            </p>
            <ScrollArea className="flex-1">
              <div className="space-y-1.5">
                {filteredSessions.map(s => (
                  <SessionItem key={s.session_id} s={s} isActive={activeSession === s.session_id} onClick={() => loadSession(s)} />
                ))}
                {filteredSessions.length === 0 && <p className="text-muted-foreground text-xs text-center py-4">Sin conversaciones</p>}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl md:col-span-3 flex flex-col overflow-hidden">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            {/* Chat Header */}
            <div className="p-3 border-b border-input flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  sessionSource === "whatsapp" ? "bg-green-500/10" : "bg-primary/10"
                }`}>
                  {sessionSource === "whatsapp" ? <Phone size={15} className="text-green-500" /> : <Bot size={15} className="text-primary" />}
                </div>
                <div>
                  <p className="text-sm text-foreground font-medium flex items-center gap-2">
                    {sessionSource === "whatsapp" ? "WhatsApp" : "Asesor Fakulti"}
                    {leadInfo?.name && <span className="text-muted-foreground font-normal">— {leadInfo.name}</span>}
                    {sessionSource === "whatsapp" && (
                      <Badge data-testid="wa-badge" variant="outline" className="text-[9px] h-4 border-green-500/30 text-green-600">EN VIVO</Badge>
                    )}
                  </p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-muted-foreground">
                      {sessionSource === "whatsapp" ? (leadInfo?.whatsapp || "") : "Powered by GPT-5.2"}
                    </p>
                    {leadInfo?.funnel_stage && (
                      <Badge variant="outline" className="text-[10px] h-4" style={{ borderColor: STAGE_CONFIG[leadInfo.funnel_stage]?.color, color: STAGE_CONFIG[leadInfo.funnel_stage]?.color }}>
                        {STAGE_CONFIG[leadInfo.funnel_stage]?.label}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              {activeSession && messages.length > 0 && (
                <Button data-testid="delete-conversation-btn" variant="ghost" size="sm" className="text-muted-foreground hover:text-red-400" onClick={deleteConversation}>
                  <Trash2 size={14} className="mr-1" /> Eliminar
                </Button>
              )}
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4 pb-4">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <Activity size={40} className="text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">
                      {sessionSource === "whatsapp" ? "Conversacion de WhatsApp" : "Inicia una conversacion con el asesor virtual"}
                    </p>
                    <p className="text-muted-foreground text-xs mt-1">
                      {sessionSource === "whatsapp" ? "Los mensajes aparecen en tiempo real" : "El bot solicitara los datos del cliente automaticamente"}
                    </p>
                  </div>
                )}
                {messages.map((msg, i) => {
                  const isUser = msg.role === "user";
                  const isCrmAgent = msg.sent_by === "crm_agent";
                  return (
                    <div key={msg.id || i} className={`group flex gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
                      {!isUser && (
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
                          isCrmAgent ? "bg-blue-500/10" : sessionSource === "whatsapp" ? "bg-green-500/10" : "bg-muted"
                        }`}>
                          {isCrmAgent ? <Shield size={13} className="text-blue-500" /> : sessionSource === "whatsapp" ? <Phone size={13} className="text-green-500" /> : <Bot size={13} className="text-primary" />}
                        </div>
                      )}
                      <div className="relative max-w-[80%]">
                        <div className={`px-4 py-2.5 text-sm ${isUser ? "chat-bubble-user" : "chat-bubble-bot"} ${isCrmAgent ? "!border-l-2 !border-l-blue-500" : ""}`} data-testid={`chat-msg-${i}`}>
                          {isCrmAgent && <p className="text-[10px] text-blue-500 font-medium mb-1">Agente CRM</p>}
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                          {msg.response_time_ms && (
                            <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1">
                              <Clock size={9} /> {(msg.response_time_ms / 1000).toFixed(1)}s
                            </p>
                          )}
                        </div>
                        <button
                          data-testid={`delete-msg-${i}`}
                          onClick={() => deleteMessage(msg.id, i)}
                          className="absolute -top-2 -right-2 hidden group-hover:flex w-5 h-5 rounded-full bg-red-500/90 text-white items-center justify-center text-xs hover:bg-red-600 transition-all"
                          title="Eliminar mensaje"
                        >
                          <X size={10} />
                        </button>
                      </div>
                      {isUser && (
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
                          sessionSource === "whatsapp" ? "bg-green-500/10" : "bg-primary/10"
                        }`}>
                          {sessionSource === "whatsapp" ? <Phone size={13} className="text-green-500" /> : <User size={13} className="text-primary" />}
                        </div>
                      )}
                    </div>
                  );
                })}
                {sending && (
                  <div className="flex gap-2">
                    <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center"><Bot size={14} className="text-primary" /></div>
                    <div className="chat-bubble-bot px-4 py-3"><div className="flex gap-1"><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" /><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} /><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} /></div></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-3 border-t border-input">
              <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
                <Input
                  data-testid="chat-input"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={sessionSource === "whatsapp" ? "Responder por WhatsApp como agente..." : "Escribe tu mensaje..."}
                  className="flex-1 bg-muted/50 border-input text-foreground h-10"
                  disabled={sending}
                />
                <Button data-testid="chat-send-btn" type="submit" disabled={sending || !input.trim()}
                  className={`h-10 px-4 rounded-lg ${sessionSource === "whatsapp" ? "bg-green-600 hover:bg-green-700 text-white" : "bg-primary text-primary-foreground hover:bg-primary/90"}`}>
                  <Send size={15} />
                </Button>
              </form>
              {sessionSource === "whatsapp" && (
                <p className="text-[10px] text-muted-foreground mt-1.5 flex items-center gap-1">
                  <Phone size={9} /> Los mensajes se envian directamente al WhatsApp del cliente
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
