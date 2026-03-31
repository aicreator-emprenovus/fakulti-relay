import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Brain, BookOpen, Plus, Trash2, Edit, Save, TestTube, Send, Key, Users, ChevronDown, ChevronUp } from "lucide-react";
import { PasswordInput } from "@/components/PasswordInput";

export default function DevPanelPage() {
  const [tab, setTab] = useState("training");

  return (
    <div data-testid="dev-panel-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Panel Desarrollador</h1>
        <p className="text-sm text-muted-foreground">Centro de Entrenamiento del Bot y Gestión del Sistema</p>
      </div>

      <div className="flex gap-1 border border-border rounded-lg p-1 w-fit bg-muted/30">
        {[
          { key: "training", icon: Brain, label: "Entrenamiento Bot" },
          { key: "knowledge", icon: BookOpen, label: "Base de Conocimiento" },
          { key: "test", icon: TestTube, label: "Consola de Pruebas" },
          { key: "passwords", icon: Key, label: "Gestión de Accesos" },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} data-testid={`dev-tab-${t.key}`}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-all ${tab === t.key ? "bg-card text-foreground shadow-sm border border-border" : "text-muted-foreground hover:text-foreground"}`}>
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "training" && <BotTrainingTab />}
      {tab === "knowledge" && <KnowledgeBaseTab />}
      {tab === "test" && <TestConsoleTab />}
      {tab === "passwords" && <PasswordManagementTab />}
    </div>
  );
}

function BotTrainingTab() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/bot-training/global-config`).then(r => { setConfig(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const save = async () => {
    try {
      const res = await axios.put(`${API}/bot-training/global-config`, config);
      setConfig(res.data);
      toast.success("Configuración del bot guardada");
    } catch { toast.error("Error al guardar"); }
  };

  if (loading || !config) return <div className="text-muted-foreground text-center py-8">Cargando...</div>;

  const Field = ({ label, field, textarea, type }) => (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground font-medium">{label}</Label>
      {textarea ? (
        <Textarea data-testid={`bot-${field}`} value={config[field] || ""} onChange={e => setConfig(c => ({ ...c, [field]: e.target.value }))} className="bg-muted/50 border-input text-foreground min-h-[80px]" rows={3} />
      ) : (
        <Input data-testid={`bot-${field}`} type={type || "text"} value={config[field] || ""} onChange={e => setConfig(c => ({ ...c, [field]: type === "number" ? parseInt(e.target.value) || 0 : e.target.value }))} className="bg-muted/50 border-input text-foreground" />
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      <Card className="bg-card border-border rounded-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Brain size={18} className="text-violet-500" /> Personalidad Global del Bot</CardTitle>
          <p className="text-xs text-muted-foreground">Estas configuraciones aplican cuando el bot no tiene un producto específico asignado</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nombre del Bot" field="bot_name" />
            <Field label="Nombre de la Marca" field="brand_name" />
          </div>
          <Field label="Tono y Estilo" field="tone" textarea />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Estilo de Saludo" field="greeting_style" textarea />
            <Field label="Estilo de Despedida" field="farewell_style" textarea />
          </div>
          <Field label="Frases Prohibidas" field="prohibited_phrases" textarea />
          <Field label="Instrucciones Generales Adicionales" field="general_instructions" textarea />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Max Emojis por Mensaje" field="max_emojis_per_message" type="number" />
            <Field label="Max Líneas por Mensaje" field="max_lines_per_message" type="number" />
            <Field label="Idioma de Respuesta" field="response_language" />
          </div>
          <Button data-testid="save-bot-config" onClick={save} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
            <Save size={14} className="mr-1.5" /> Guardar Configuración
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function KnowledgeBaseTab() {
  const [entries, setEntries] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState(null);
  const [form, setForm] = useState({ question: "", answer: "", category: "general" });

  const fetch = () => axios.get(`${API}/bot-training/knowledge-base`).then(r => setEntries(r.data)).catch(() => {});
  useEffect(() => { fetch(); }, []);

  const save = async () => {
    if (!form.question || !form.answer) return toast.error("Pregunta y respuesta son requeridas");
    try {
      if (editEntry) {
        await axios.put(`${API}/bot-training/knowledge-base/${editEntry.id}`, form);
        toast.success("Entrada actualizada");
      } else {
        await axios.post(`${API}/bot-training/knowledge-base`, form);
        toast.success("Entrada creada");
      }
      setShowForm(false); setEditEntry(null); setForm({ question: "", answer: "", category: "general" }); fetch();
    } catch { toast.error("Error al guardar"); }
  };

  const remove = async (id) => {
    if (!window.confirm("¿Eliminar esta entrada?")) return;
    try { await axios.delete(`${API}/bot-training/knowledge-base/${id}`); toast.success("Eliminada"); fetch(); } catch { toast.error("Error"); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Base de Conocimiento / FAQ</h2>
          <p className="text-xs text-muted-foreground">{entries.length} entradas — El bot consulta esta base para responder preguntas frecuentes</p>
        </div>
        <Button data-testid="add-kb-entry" onClick={() => { setEditEntry(null); setForm({ question: "", answer: "", category: "general" }); setShowForm(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
          <Plus size={14} className="mr-1" /> Nueva Entrada
        </Button>
      </div>

      <div className="space-y-2">
        {entries.map(e => (
          <KBEntry key={e.id} entry={e} onEdit={() => { setEditEntry(e); setForm({ question: e.question, answer: e.answer, category: e.category }); setShowForm(true); }} onDelete={() => remove(e.id)} />
        ))}
        {entries.length === 0 && <p className="text-center text-sm text-muted-foreground py-8">No hay entradas. Agrega preguntas frecuentes para que el bot las use.</p>}
      </div>

      <Dialog open={showForm} onOpenChange={v => { setShowForm(v); if (!v) setEditEntry(null); }}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg">
          <DialogHeader><DialogTitle>{editEntry ? "Editar Entrada" : "Nueva Entrada"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-xs text-muted-foreground">Pregunta del Cliente *</Label><Textarea data-testid="kb-question" value={form.question} onChange={e => setForm(f => ({ ...f, question: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} placeholder='Ej: "¿Hacen envíos a Galápagos?"' /></div>
            <div><Label className="text-xs text-muted-foreground">Respuesta del Bot *</Label><Textarea data-testid="kb-answer" value={form.answer} onChange={e => setForm(f => ({ ...f, answer: e.target.value }))} className="bg-muted border-input text-foreground" rows={3} placeholder="La respuesta que el bot debe dar" /></div>
            <div><Label className="text-xs text-muted-foreground">Categoría</Label><Input data-testid="kb-category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} className="bg-muted border-input text-foreground" placeholder="general, envíos, pagos, productos..." /></div>
            <Button data-testid="save-kb-entry" onClick={save} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">{editEntry ? "Actualizar" : "Crear Entrada"}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function KBEntry({ entry, onEdit, onDelete }) {
  const [open, setOpen] = useState(false);
  return (
    <Card className="bg-card border-border rounded-xl">
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <button onClick={() => setOpen(!open)} className="flex-1 text-left flex items-center gap-2">
            {open ? <ChevronUp size={14} className="text-muted-foreground flex-shrink-0" /> : <ChevronDown size={14} className="text-muted-foreground flex-shrink-0" />}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{entry.question}</p>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary">{entry.category}</span>
            </div>
          </button>
          <div className="flex gap-1 flex-shrink-0">
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground" onClick={onEdit}><Edit size={13} /></Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400" onClick={onDelete}><Trash2 size={13} /></Button>
          </div>
        </div>
        {open && <div className="mt-2 pl-6 text-sm text-muted-foreground bg-muted/30 rounded-lg p-3">{entry.answer}</div>}
      </CardContent>
    </Card>
  );
}

function TestConsoleTab() {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendTest = async () => {
    if (!message.trim()) return;
    const userMsg = message.trim();
    setConversation(prev => [...prev, { role: "user", content: userMsg }]);
    setMessage("");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/bot-training/test`, { message: userMsg });
      setConversation(prev => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch {
      setConversation(prev => [...prev, { role: "assistant", content: "Error al obtener respuesta del bot" }]);
    }
    setLoading(false);
  };

  const clearChat = () => setConversation([]);

  return (
    <div className="space-y-4">
      <Card className="bg-card border-border rounded-2xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base"><TestTube size={18} className="text-emerald-500" /> Consola de Pruebas</CardTitle>
              <p className="text-xs text-muted-foreground">Prueba cómo responde el bot con la configuración actual. Los datos de prueba se eliminan automáticamente.</p>
            </div>
            <Button variant="outline" size="sm" onClick={clearChat} className="rounded-full text-xs">Limpiar Chat</Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] overflow-y-auto border border-border rounded-xl p-4 mb-4 bg-muted/20 space-y-3">
            {conversation.length === 0 && <p className="text-center text-sm text-muted-foreground py-12">Envía un mensaje para probar el bot</p>}
            {conversation.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${msg.role === "user" ? "bg-primary/10 text-foreground rounded-br-md" : "bg-emerald-500/10 text-foreground rounded-bl-md"}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && <div className="flex justify-start"><div className="bg-emerald-500/10 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm text-muted-foreground animate-pulse">Escribiendo...</div></div>}
          </div>
          <div className="flex gap-2">
            <Input data-testid="test-message-input" value={message} onChange={e => setMessage(e.target.value)} placeholder="Escribe un mensaje de prueba..." className="bg-muted/50 border-input text-foreground" onKeyDown={e => e.key === "Enter" && sendTest()} />
            <Button data-testid="send-test-btn" onClick={sendTest} disabled={loading || !message.trim()} className="bg-primary text-primary-foreground rounded-full px-6"><Send size={14} /></Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PasswordManagementTab() {
  const [admins, setAdmins] = useState([]);
  const [resetRequests, setResetRequests] = useState([]);
  const [resetForm, setResetForm] = useState({ user_id: "", new_password: "" });
  const [selectedAdmin, setSelectedAdmin] = useState(null);

  const fetchData = () => {
    axios.get(`${API}/bot-training/admins`).then(r => setAdmins(r.data)).catch(() => {});
    axios.get(`${API}/auth/password-reset-requests`).then(r => setResetRequests(r.data)).catch(() => {});
  };
  useEffect(() => { fetchData(); }, []);

  const resetDirect = async (userId) => {
    if (!resetForm.new_password || resetForm.new_password.length < 6) return toast.error("La contraseña debe tener al menos 6 caracteres");
    try {
      await axios.post(`${API}/auth/reset-password-direct`, { user_id: userId, new_password: resetForm.new_password });
      toast.success("Contraseña restablecida exitosamente");
      setResetForm({ user_id: "", new_password: "" }); setSelectedAdmin(null);
    } catch (e) { toast.error(e.response?.data?.detail || "Error"); }
  };

  const resolveRequest = async (reqId) => {
    if (!resetForm.new_password || resetForm.new_password.length < 6) return toast.error("La contraseña debe tener al menos 6 caracteres");
    try {
      await axios.post(`${API}/auth/reset-password/${reqId}`, { new_password: resetForm.new_password });
      toast.success("Contraseña restablecida exitosamente");
      setResetForm({ user_id: "", new_password: "" }); fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || "Error"); }
  };

  return (
    <div className="space-y-4">
      {resetRequests.length > 0 && (
        <Card className="bg-card border-l-4 border-l-amber-500 rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-amber-600"><Key size={18} /> Solicitudes de Restablecimiento Pendientes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {resetRequests.map(req => (
              <div key={req.id} className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">{req.user_name} ({req.user_email})</p>
                    <p className="text-xs text-muted-foreground">Rol: {req.user_role} | Solicitado: {new Date(req.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex gap-2 items-end">
                  <div className="flex-1">
                    <Label className="text-xs text-muted-foreground">Nueva Contraseña</Label>
                    <PasswordInput value={resetForm.new_password} onChange={e => setResetForm(f => ({ ...f, new_password: e.target.value }))} placeholder="Min 6 caracteres" className="bg-muted/50 border-input text-foreground" />
                  </div>
                  <Button data-testid={`resolve-reset-${req.id}`} onClick={() => resolveRequest(req.id)} className="bg-amber-500 text-white font-bold rounded-full hover:bg-amber-600">Restablecer</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="bg-card border-border rounded-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Users size={18} className="text-violet-500" /> Administradores del Sistema</CardTitle>
          <p className="text-xs text-muted-foreground">Puedes restablecer la contraseña de cualquier administrador</p>
        </CardHeader>
        <CardContent className="space-y-3">
          {admins.map(admin => (
            <div key={admin.id} className="p-3 rounded-xl bg-muted/30 border border-border/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">{admin.name}</p>
                  <p className="text-xs text-muted-foreground">{admin.email}</p>
                </div>
                <Button data-testid={`reset-admin-${admin.id}`} variant="outline" size="sm" onClick={() => setSelectedAdmin(selectedAdmin === admin.id ? null : admin.id)} className="rounded-full text-xs">
                  <Key size={12} className="mr-1" /> {selectedAdmin === admin.id ? "Cancelar" : "Resetear Contraseña"}
                </Button>
              </div>
              {selectedAdmin === admin.id && (
                <div className="mt-3 flex gap-2 items-end">
                  <div className="flex-1">
                    <Label className="text-xs text-muted-foreground">Nueva Contraseña</Label>
                    <PasswordInput value={resetForm.new_password} onChange={e => setResetForm(f => ({ ...f, new_password: e.target.value }))} placeholder="Min 6 caracteres" className="bg-muted/50 border-input text-foreground" />
                  </div>
                  <Button data-testid={`confirm-reset-${admin.id}`} onClick={() => resetDirect(admin.id)} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">Confirmar</Button>
                </div>
              )}
            </div>
          ))}
          {admins.length === 0 && <p className="text-center text-sm text-muted-foreground py-4">No hay administradores registrados</p>}
        </CardContent>
      </Card>
    </div>
  );
}
