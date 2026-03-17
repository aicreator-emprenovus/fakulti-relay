import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Zap, MessageSquare, Bot, Plus, Trash2, Edit, Copy, CheckCircle, AlertTriangle, Wifi } from "lucide-react";

const TRIGGER_TYPES = {
  nuevo_lead: "Nuevo lead",
  lead_sin_datos: "Lead sin datos",
  sin_respuesta: "Sin respuesta (horas)",
  intencion_ia: "Intención IA",
  analisis_conversacion: "Análisis conversación",
  compra_realizada: "Compra realizada",
  dias_post_compra: "Dias post-compra",
};
const ACTION_TYPES = {
  enviar_mensaje: "Enviar mensaje",
  respuesta_ia: "Respuesta IA",
  cambiar_etapa: "Cambiar etapa",
  asignar_agente: "Asignar agente",
  iniciar_secuencia: "Iniciar secuencia",
};

export default function ConfigPage() {
  const [tab, setTab] = useState("automation");
  const [rules, setRules] = useState([]);
  const [waConfig, setWaConfig] = useState({});
  const [aiConfig, setAiConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editRule, setEditRule] = useState(null);
  const [form, setForm] = useState({ name: "", trigger_type: "nuevo_lead", trigger_value: "", action_type: "enviar_mensaje", action_value: "", description: "", active: true });
  const [waForm, setWaForm] = useState({ phone_number_id: "", access_token: "", verify_token: "", business_name: "" });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const webhookUrl = `${window.location.origin}/api/webhook/whatsapp`;

  const fetchAll = () => {
    Promise.all([
      axios.get(`${API}/automation/rules`),
      axios.get(`${API}/config/whatsapp`),
      axios.get(`${API}/config/ai`),
    ]).then(([r, w, a]) => {
      setRules(r.data);
      setWaConfig(w.data);
      setWaForm({ phone_number_id: w.data.phone_number_id || "", access_token: w.data.access_token || "", verify_token: w.data.verify_token || "", business_name: w.data.business_name || "" });
      setAiConfig(a.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };
  useEffect(() => { fetchAll(); }, []);

  const saveRule = async () => {
    if (!form.name) return toast.error("Nombre requerido");
    try {
      if (editRule) {
        await axios.put(`${API}/automation/rules/${editRule.id}`, form);
        toast.success("Regla actualizada");
      } else {
        await axios.post(`${API}/automation/rules`, form);
        toast.success("Regla creada");
      }
      setShowForm(false);
      setEditRule(null);
      fetchAll();
    } catch { toast.error("Error al guardar"); }
  };

  const toggleRule = async (id) => {
    try {
      const res = await axios.patch(`${API}/automation/rules/${id}/toggle`);
      setRules(prev => prev.map(r => r.id === id ? { ...r, active: res.data.active } : r));
    } catch { toast.error("Error"); }
  };

  const deleteRule = async (id) => {
    if (!window.confirm("¿Eliminar esta regla?")) return;
    try {
      await axios.delete(`${API}/automation/rules/${id}`);
      toast.success("Regla eliminada");
      fetchAll();
    } catch { toast.error("Error"); }
  };

  const openEditRule = (r) => {
    setEditRule(r);
    setForm({ name: r.name, trigger_type: r.trigger_type, trigger_value: r.trigger_value || "", action_type: r.action_type, action_value: r.action_value || "", description: r.description || "", active: r.active });
    setShowForm(true);
  };

  const saveWaConfig = async () => {
    try {
      await axios.put(`${API}/config/whatsapp`, waForm);
      toast.success("Configuración de WhatsApp guardada");
      fetchAll();
    } catch { toast.error("Error al guardar"); }
  };

  const testWaConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await axios.post(`${API}/config/whatsapp/test`);
      setTestResult(res.data);
    } catch { setTestResult({ success: false, message: "Error de conexión" }); }
    setTesting(false);
  };

  const toggleAi = async (key) => {
    const updated = { ...aiConfig, [key]: !aiConfig[key] };
    try {
      await axios.put(`${API}/config/ai`, updated);
      setAiConfig(updated);
    } catch { toast.error("Error"); }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado al portapapeles");
  };

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando...</div>;

  return (
    <div data-testid="config-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Configuración</h1>
        <p className="text-sm text-muted-foreground">Automatizaciones y configuración del sistema</p>
      </div>

      <div className="flex gap-1 border border-border rounded-lg p-1 w-fit bg-muted/30">
        {[
          { key: "automation", icon: Zap, label: "Automatización" },
          { key: "whatsapp", icon: MessageSquare, label: "WhatsApp" },
          { key: "ai", icon: Bot, label: "IA" },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} data-testid={`tab-${t.key}`}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-all ${tab === t.key ? "bg-card text-foreground shadow-sm border border-border" : "text-muted-foreground hover:text-foreground"}`}>
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "automation" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Reglas de Automatización</h2>
              <p className="text-xs text-muted-foreground">{rules.length} reglas configuradas</p>
            </div>
            <Button data-testid="add-rule-btn" onClick={() => { setEditRule(null); setForm({ name: "", trigger_type: "nuevo_lead", trigger_value: "", action_type: "enviar_mensaje", action_value: "", description: "", active: true }); setShowForm(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
              <Plus size={14} className="mr-1" /> Nueva Regla
            </Button>
          </div>

          <div className="space-y-3">
            {rules.map(rule => (
              <Card key={rule.id} className={`bg-card border-l-4 rounded-2xl transition-all ${rule.active ? "border-l-primary/60" : "border-l-muted opacity-60"}`} data-testid={`rule-${rule.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-foreground">{rule.name}</h3>
                        <Badge variant="outline" className={`text-[10px] ${rule.active ? "border-primary text-primary" : "border-muted-foreground text-muted-foreground"}`}>{rule.active ? "Activa" : "Inactiva"}</Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs flex-wrap">
                        <span className="text-primary font-medium flex items-center gap-1"><Zap size={11} /> {TRIGGER_TYPES[rule.trigger_type] || rule.trigger_type}{rule.trigger_value ? ` (${rule.trigger_value})` : ""}</span>
                        <span className="text-muted-foreground">→</span>
                        <span className="text-emerald-500 font-medium">{ACTION_TYPES[rule.action_type] || rule.action_type}</span>
                      </div>
                      {rule.description && <p className="text-xs text-muted-foreground">{rule.description}</p>}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Switch checked={rule.active} onCheckedChange={() => toggleRule(rule.id)} data-testid={`toggle-rule-${rule.id}`} />
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground" onClick={() => openEditRule(rule)}><Edit size={13} /></Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400" onClick={() => deleteRule(rule.id)}><Trash2 size={13} /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {tab === "whatsapp" && (
        <div className="space-y-4">
          <Card className="bg-card border-border rounded-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><MessageSquare size={18} className="text-emerald-500" /> Configuración de WhatsApp Business</CardTitle>
              <p className="text-xs text-muted-foreground">Conecta tu cuenta de WhatsApp Business API</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {(!waConfig.phone_number_id || !waConfig.access_token || waConfig.access_token === "****") ? (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
                  <h4 className="text-sm font-semibold text-amber-600 flex items-center gap-1.5"><AlertTriangle size={14} /> Configuración pendiente</h4>
                  <p className="text-xs text-muted-foreground">Para conectar WhatsApp Business API necesitas:</p>
                  <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                    <li>Una cuenta de Meta Business</li>
                    <li>Acceso a WhatsApp Business Cloud API</li>
                    <li>Phone Number ID y Access Token</li>
                  </ul>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <h4 className="text-sm font-semibold text-emerald-600 flex items-center gap-1.5"><CheckCircle size={14} /> WhatsApp Configurado</h4>
                  <p className="text-xs text-muted-foreground">La integracion con WhatsApp Business esta activa.</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Webhook URL</Label>
                  <div className="flex gap-1">
                    <Input value={webhookUrl} readOnly className="bg-muted/50 border-input text-foreground text-xs" data-testid="webhook-url" />
                    <Button variant="outline" size="sm" onClick={() => copyToClipboard(webhookUrl)} className="border-input text-muted-foreground"><Copy size={13} /></Button>
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Verify Token</Label>
                  <div className="flex gap-1">
                    <Input value={waForm.verify_token} onChange={e => setWaForm(f => ({ ...f, verify_token: e.target.value }))} className="bg-muted/50 border-input text-foreground text-xs" data-testid="verify-token" />
                    <Button variant="outline" size="sm" onClick={() => copyToClipboard(waForm.verify_token)} className="border-input text-muted-foreground"><Copy size={13} /></Button>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground">Usa esta URL y token de verificacion al configurar el webhook en Meta for Developers.</p>

              <div className="border-t border-border pt-4 space-y-3">
                <div>
                  <Label className="text-xs text-muted-foreground">Phone Number ID</Label>
                  <Input data-testid="phone-number-id" value={waForm.phone_number_id} onChange={e => setWaForm(f => ({ ...f, phone_number_id: e.target.value }))} placeholder="Ej: 123456789012345" className="bg-muted/50 border-input text-foreground" />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Access Token</Label>
                  <Input data-testid="access-token" value={waForm.access_token} onChange={e => setWaForm(f => ({ ...f, access_token: e.target.value }))} placeholder="Token de acceso de Meta" className="bg-muted/50 border-input text-foreground" type="password" />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Nombre del Negocio</Label>
                  <Input value={waForm.business_name} onChange={e => setWaForm(f => ({ ...f, business_name: e.target.value }))} className="bg-muted/50 border-input text-foreground" />
                </div>
                <div className="flex gap-2">
                  <Button data-testid="save-wa-config" onClick={saveWaConfig} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">Guardar Configuración</Button>
                  <Button data-testid="test-wa-btn" variant="outline" onClick={testWaConnection} disabled={testing} className="border-input text-foreground rounded-full">
                    <Wifi size={14} className="mr-1" /> {testing ? "Probando..." : "Probar Conexión"}
                  </Button>
                </div>
                {testResult && (
                  <div className={`p-3 rounded-lg text-xs ${testResult.success ? "bg-emerald-500/10 text-emerald-600" : "bg-red-500/10 text-red-500"}`}>
                    {testResult.success ? <CheckCircle size={14} className="inline mr-1" /> : <AlertTriangle size={14} className="inline mr-1" />}
                    {testResult.message}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "ai" && (
        <div className="space-y-4">
          <Card className="bg-card border-border rounded-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><Bot size={18} className="text-primary" /> Configuración de IA</CardTitle>
              <p className="text-xs text-muted-foreground">Análisis automático de mensajes con GPT-5.2</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
                <h4 className="text-sm font-semibold text-primary flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-primary animate-pulse" /> IA Activa</h4>
                <p className="text-xs text-muted-foreground mt-1">La integracion con GPT-5.2 esta configurada usando Emergent LLM Key.</p>
              </div>

              {[
                { key: "intent_analysis", label: "Análisis de intención", desc: "Clasifica automáticamente la intención del mensaje" },
                { key: "lead_classification", label: "Clasificación de leads", desc: "Determina la etapa del lead basándose en la conversación" },
                { key: "product_recommendation", label: "Recomendación de productos", desc: "Sugiere productos basados en el mensaje del cliente" },
                { key: "suggested_responses", label: "Respuestas sugeridas", desc: "Genera respuestas automáticas para el asesor" },
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border/50" data-testid={`ai-toggle-${item.key}`}>
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <Switch checked={aiConfig[item.key]} onCheckedChange={() => toggleAi(item.key)} />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      <Dialog open={showForm} onOpenChange={v => { setShowForm(v); if (!v) setEditRule(null); }}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg" data-testid="rule-form-dialog">
          <DialogHeader><DialogTitle>{editRule ? "Editar Regla" : "Nueva Regla"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-xs text-muted-foreground">Nombre *</Label><Input data-testid="rule-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-xs text-muted-foreground">Disparador</Label>
                <Select value={form.trigger_type} onValueChange={v => setForm(f => ({ ...f, trigger_type: v }))}>
                  <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">{Object.entries(TRIGGER_TYPES).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div><Label className="text-xs text-muted-foreground"> Acción</Label>
                <Select value={form.action_type} onValueChange={v => setForm(f => ({ ...f, action_type: v }))}>
                  <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">{Object.entries(ACTION_TYPES).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <div><Label className="text-xs text-muted-foreground">Valor del disparador</Label><Input value={form.trigger_value} onChange={e => setForm(f => ({ ...f, trigger_value: e.target.value }))} placeholder="Ej: 4 (horas), keywords separados por coma" className="bg-muted border-input text-foreground" /></div>
            <div><Label className="text-xs text-muted-foreground">Contenido / Valor de la acción</Label><Textarea value={form.action_value} onChange={e => setForm(f => ({ ...f, action_value: e.target.value }))} className="bg-muted border-input text-foreground" rows={3} /></div>
            <div><Label className="text-xs text-muted-foreground"> Descripción</Label><Textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
            <div className="flex items-center gap-2"><Label className="text-xs text-muted-foreground">Activa</Label><Switch checked={form.active} onCheckedChange={v => setForm(f => ({ ...f, active: v }))} /></div>
            <Button data-testid="save-rule-btn" onClick={saveRule} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">{editRule ? "Actualizar" : "Crear Regla"}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
