import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Send, MessageSquare, Bot, User, Trash2, X } from "lucide-react";

const STAGE_CONFIG = {
  nuevo: { label: "Nuevo", color: "#3B82F6" },
  interesado: { label: "Interesado", color: "#8B5CF6" },
  en_negociacion: { label: "En Negociacion", color: "#F59E0B" },
  cliente_nuevo: { label: "Cliente Nuevo", color: "#10B981" },
  cliente_activo: { label: "Cliente Activo", color: "#A3E635" },
  perdido: { label: "Perdido", color: "#64748B" },
};

export default function ChatPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [leadInfo, setLeadInfo] = useState(null);
  const messagesEndRef = useRef(null);

  const fetchSessions = () => {
    axios.get(`${API}/chat/sessions`).then(res => setSessions(res.data)).catch(() => {});
  };

  useEffect(() => { fetchSessions(); }, []);

  useEffect(() => {
    if (activeSession) {
      axios.get(`${API}/chat/history/${activeSession}`).then(res => setMessages(res.data)).catch(() => {});
    }
  }, [activeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startNewSession = () => {
    const sid = `session_${Date.now()}`;
    setActiveSession(sid);
    setMessages([]);
    setLeadInfo(null);
  };

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const sessionId = activeSession || `session_${Date.now()}`;
    if (!activeSession) setActiveSession(sessionId);

    const userMsg = { role: "user", content: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await axios.post(`${API}/chat/message`, { session_id: sessionId, message: input });
      const botMsg = { role: "assistant", content: res.data.response, timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, botMsg]);
      if (res.data.lead) setLeadInfo(res.data.lead);
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
      setLeadInfo(null);
      fetchSessions();
      toast.success("Conversacion eliminada");
    } catch { toast.error("Error al eliminar conversacion"); }
  };

  return (
    <div data-testid="chat-page" className="animate-fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Chat IA</h1>
          <p className="text-sm text-muted-foreground">Asesor Virtual Faculty con GPT-5.2</p>
        </div>
        <Button data-testid="new-chat-btn" onClick={startNewSession} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
          <MessageSquare size={16} className="mr-1" /> Nueva Conversacion
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[calc(100vh-200px)]">
        <Card className="bg-card border-border rounded-2xl md:col-span-1 hidden md:block">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3 font-semibold">Sesiones</p>
            <ScrollArea className="h-[calc(100vh-280px)]">
              <div className="space-y-1">
                {sessions.map(s => (
                  <button key={s.session_id} onClick={() => setActiveSession(s.session_id)}
                    className={`w-full text-left p-2 rounded-lg text-xs transition-colors ${activeSession === s.session_id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"}`}
                    data-testid={`session-${s.session_id}`}>
                    <p className="truncate font-medium">{s.lead_name || s.last_message?.slice(0, 30) || "Sin mensajes"}</p>
                    <p className="text-muted-foreground mt-0.5">{s.message_count} msgs</p>
                  </button>
                ))}
                {sessions.length === 0 && <p className="text-muted-foreground text-xs text-center py-4">Sin sesiones</p>}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl md:col-span-3 flex flex-col">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            <div className="p-4 border-b border-input flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot size={16} className="text-primary" />
                </div>
                <div>
                  <p className="text-sm text-foreground font-medium">
                    Asesor Faculty
                    {leadInfo && <span className="text-muted-foreground font-normal"> — {leadInfo.name}</span>}
                  </p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-muted-foreground">Powered by GPT-5.2</p>
                    {leadInfo && (
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

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4 pb-4">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <Bot size={40} className="text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">Inicia una conversacion con el asesor virtual de Faculty</p>
                    <p className="text-muted-foreground text-xs mt-1">El bot saludara al lead y le pedira su nombre para registrarlo automaticamente</p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`group flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "assistant" && <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center flex-shrink-0 mt-1"><Bot size={14} className="text-primary" /></div>}
                    <div className="relative max-w-[80%]">
                      <div className={`px-4 py-2.5 text-sm ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"}`} data-testid={`chat-msg-${i}`}>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
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
                    {msg.role === "user" && <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1"><User size={14} className="text-primary" /></div>}
                  </div>
                ))}
                {sending && (
                  <div className="flex gap-2">
                    <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center"><Bot size={14} className="text-primary" /></div>
                    <div className="chat-bubble-bot px-4 py-3"><div className="flex gap-1"><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" /><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} /><div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} /></div></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="p-4 border-t border-input">
              <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
                <Input data-testid="chat-input" value={input} onChange={e => setInput(e.target.value)} placeholder="Escribe tu mensaje..." className="flex-1 bg-muted/50 border-input text-foreground h-11" disabled={sending} />
                <Button data-testid="chat-send-btn" type="submit" disabled={sending || !input.trim()} className="bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-4 rounded-lg">
                  <Send size={16} />
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
