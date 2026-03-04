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
import { Plus, Trash2, Save, Heart, Clock, Play, UserCheck, Mail, CheckCircle, AlertCircle } from "lucide-react";

export default function LoyaltyPage() {
  const [sequences, setSequences] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [products, setProducts] = useState([]);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showEnroll, setShowEnroll] = useState(false);
  const [tab, setTab] = useState("sequences");
  const [form, setForm] = useState({ product_id: "", product_name: "", messages: [{ day: 1, content: "", active: true }], active: true });
  const [enrollForm, setEnrollForm] = useState({ lead_id: "", sequence_id: "" });

  const fetchData = () => {
    Promise.all([
      axios.get(`${API}/loyalty/sequences`),
      axios.get(`${API}/loyalty/enrollments`),
      axios.get(`${API}/products`),
      axios.get(`${API}/leads?limit=200`)
    ]).then(([s, e, p, l]) => {
      setSequences(s.data);
      setEnrollments(e.data);
      setProducts(p.data);
      setLeads(l.data.leads);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const addMessage = () => {
    const lastDay = form.messages.length > 0 ? form.messages[form.messages.length - 1].day : 0;
    setForm(f => ({ ...f, messages: [...f.messages, { day: lastDay + 3, content: "", active: true }] }));
  };

  const removeMessage = (idx) => {
    setForm(f => ({ ...f, messages: f.messages.filter((_, i) => i !== idx) }));
  };

  const updateMessage = (idx, field, value) => {
    setForm(f => ({ ...f, messages: f.messages.map((m, i) => i === idx ? { ...m, [field]: value } : m) }));
  };

  const handleSave = async () => {
    if (!form.product_id || form.messages.length === 0) return toast.error("Selecciona un producto y agrega al menos un mensaje");
    try {
      await axios.post(`${API}/loyalty/sequences`, form);
      toast.success("Secuencia creada");
      setShowAdd(false);
      setForm({ product_id: "", product_name: "", messages: [{ day: 1, content: "", active: true }], active: true });
      fetchData();
    } catch { toast.error("Error al crear secuencia"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Eliminar esta secuencia?")) return;
    try {
      await axios.delete(`${API}/loyalty/sequences/${id}`);
      toast.success("Secuencia eliminada");
      fetchData();
    } catch { toast.error("Error al eliminar"); }
  };

  const handleEnroll = async () => {
    if (!enrollForm.lead_id || !enrollForm.sequence_id) return toast.error("Selecciona lead y secuencia");
    try {
      await axios.post(`${API}/loyalty/enroll?lead_id=${enrollForm.lead_id}&sequence_id=${enrollForm.sequence_id}`);
      toast.success("Lead inscrito en secuencia");
      setShowEnroll(false);
      setEnrollForm({ lead_id: "", sequence_id: "" });
      fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || "Error al inscribir"); }
  };

  const handleDeleteEnrollment = async (id) => {
    if (!window.confirm("Eliminar esta inscripcion?")) return;
    try {
      await axios.delete(`${API}/loyalty/enrollments/${id}`);
      toast.success("Inscripcion eliminada");
      fetchData();
    } catch { toast.error("Error al eliminar"); }
  };

  const processMessages = async () => {
    try {
      const res = await axios.post(`${API}/loyalty/process`);
      toast.success(res.data.message);
      fetchData();
    } catch { toast.error("Error al procesar mensajes"); }
  };

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando...</div>;

  const activeEnrollments = enrollments.filter(e => e.status === "activo").length;
  const completedEnrollments = enrollments.filter(e => e.status === "completado").length;
  const pendingMsgs = enrollments.reduce((acc, e) => acc + (e.messages || []).filter(m => m.status === "pendiente").length, 0);
  const sentMsgs = enrollments.reduce((acc, e) => acc + (e.messages || []).filter(m => m.status === "enviado").length, 0);

  return (
    <div data-testid="loyalty-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Fidelizacion</h1>
          <p className="text-sm text-muted-foreground">Secuencias automaticas postventa (hasta 24 mensajes)</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button data-testid="process-messages-btn" variant="outline" onClick={processMessages} className="border-primary text-primary hover:bg-primary/10 rounded-full">
            <Play size={14} className="mr-1" /> Procesar Pendientes
          </Button>
          <Button data-testid="enroll-lead-btn" variant="outline" onClick={() => setShowEnroll(true)} className="border-input text-foreground hover:bg-muted rounded-full">
            <UserCheck size={14} className="mr-1" /> Inscribir Lead
          </Button>
          <Button data-testid="add-sequence-btn" onClick={() => setShowAdd(true)} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
            <Plus size={16} className="mr-1" /> Nueva Secuencia
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card p-4" data-testid="stat-sequences">
          <div className="flex items-center gap-2 mb-1"><Heart size={14} className="text-pink-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Secuencias</span></div>
          <p className="text-2xl font-bold text-foreground">{sequences.length}</p>
        </div>
        <div className="stat-card p-4" data-testid="stat-active-enrollments">
          <div className="flex items-center gap-2 mb-1"><UserCheck size={14} className="text-primary" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Inscritos Activos</span></div>
          <p className="text-2xl font-bold text-foreground">{activeEnrollments}</p>
        </div>
        <div className="stat-card p-4" data-testid="stat-pending-msgs">
          <div className="flex items-center gap-2 mb-1"><Clock size={14} className="text-amber-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Msgs Pendientes</span></div>
          <p className="text-2xl font-bold text-foreground">{pendingMsgs}</p>
        </div>
        <div className="stat-card p-4" data-testid="stat-sent-msgs">
          <div className="flex items-center gap-2 mb-1"><Mail size={14} className="text-blue-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Msgs Enviados</span></div>
          <p className="text-2xl font-bold text-foreground">{sentMsgs}</p>
        </div>
      </div>

      <div className="flex gap-2 border-b border-border">
        <button onClick={() => setTab("sequences")} className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === "sequences" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`} data-testid="tab-sequences">
          Secuencias ({sequences.length})
        </button>
        <button onClick={() => setTab("enrollments")} className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === "enrollments" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`} data-testid="tab-enrollments">
          Inscripciones ({enrollments.length})
        </button>
      </div>

      {tab === "sequences" && (
        <div className="grid gap-4">
          {sequences.map(seq => (
            <Card key={seq.id} className="bg-card border-border rounded-2xl" data-testid={`sequence-${seq.id}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-3">
                  <Heart size={18} className="text-primary" />
                  <CardTitle className="text-lg text-foreground">{seq.product_name}</CardTitle>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${seq.active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>{seq.active ? "Activa" : "Inactiva"}</span>
                  <span className="text-xs text-muted-foreground">{seq.messages?.length || 0} mensajes</span>
                </div>
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-red-400" onClick={() => handleDelete(seq.id)}>
                  <Trash2 size={14} />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {seq.messages?.map((msg, i) => (
                    <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-1 bg-muted rounded px-2 py-1 text-xs text-muted-foreground flex-shrink-0">
                        <Clock size={12} /> Dia {msg.day}
                      </div>
                      <p className="text-sm text-foreground/80 flex-1">{msg.content}</p>
                      <span className={`text-xs ${msg.active ? "text-primary" : "text-muted-foreground"}`}>{msg.active ? "ON" : "OFF"}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
          {sequences.length === 0 && <div className="text-center py-12 text-muted-foreground">No hay secuencias de fidelizacion configuradas</div>}
        </div>
      )}

      {tab === "enrollments" && (
        <div className="overflow-x-auto rounded-2xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                <th className="text-left p-3 text-muted-foreground font-medium">Lead</th>
                <th className="text-left p-3 text-muted-foreground font-medium hidden md:table-cell">WhatsApp</th>
                <th className="text-left p-3 text-muted-foreground font-medium">Secuencia</th>
                <th className="text-left p-3 text-muted-foreground font-medium">Progreso</th>
                <th className="text-left p-3 text-muted-foreground font-medium">Estado</th>
                <th className="text-right p-3 text-muted-foreground font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {enrollments.map(e => {
                const totalMsgs = e.messages?.length || 0;
                const sentCount = (e.messages || []).filter(m => m.status === "enviado").length;
                const pct = totalMsgs > 0 ? Math.round((sentCount / totalMsgs) * 100) : 0;
                return (
                  <tr key={e.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`enrollment-${e.id}`}>
                    <td className="p-3">
                      <p className="text-foreground font-medium">{e.lead_name || "Sin nombre"}</p>
                    </td>
                    <td className="p-3 text-muted-foreground hidden md:table-cell">{e.lead_whatsapp}</td>
                    <td className="p-3 text-muted-foreground">{e.sequence_name}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs text-muted-foreground">{sentCount}/{totalMsgs}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge variant="outline" className={`text-xs ${e.status === "activo" ? "border-primary text-primary" : "border-muted-foreground text-muted-foreground"}`}>
                        {e.status === "activo" ? "Activo" : "Completado"}
                      </Badge>
                    </td>
                    <td className="p-3 text-right">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400" onClick={() => handleDeleteEnrollment(e.id)}>
                        <Trash2 size={14} />
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {enrollments.length === 0 && <div className="text-center py-12 text-muted-foreground">No hay leads inscritos en secuencias</div>}
        </div>
      )}

      <Dialog open={showAdd} onOpenChange={setShowAdd}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg max-h-[80vh] overflow-y-auto" data-testid="loyalty-form-dialog">
          <DialogHeader><DialogTitle>Nueva Secuencia de Fidelizacion</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-muted-foreground text-sm">Producto</Label>
              <Select value={form.product_id} onValueChange={v => { const p = products.find(pr => pr.id === v); setForm(f => ({ ...f, product_id: v, product_name: p?.name || "" })); }}>
                <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona producto" /></SelectTrigger>
                <SelectContent className="bg-muted border-input">{products.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-muted-foreground text-sm">Mensajes ({form.messages.length}/24)</Label>
                {form.messages.length < 24 && <Button size="sm" variant="ghost" className="text-primary text-xs" onClick={addMessage}><Plus size={14} className="mr-1" /> Agregar</Button>}
              </div>
              {form.messages.map((msg, i) => (
                <div key={i} className="p-3 rounded-lg bg-muted/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-muted-foreground">Dia</Label>
                    <Input type="number" value={msg.day} onChange={e => updateMessage(i, "day", parseInt(e.target.value) || 1)} className="w-16 h-7 text-xs bg-muted border-input text-foreground" />
                    <div className="flex-1" />
                    <Switch checked={msg.active} onCheckedChange={v => updateMessage(i, "active", v)} />
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-400" onClick={() => removeMessage(i)}><Trash2 size={12} /></Button>
                  </div>
                  <Textarea value={msg.content} onChange={e => updateMessage(i, "content", e.target.value)} placeholder="Contenido del mensaje..." className="bg-muted border-input text-foreground text-sm" rows={2} />
                </div>
              ))}
            </div>

            <Button data-testid="save-sequence-btn" onClick={handleSave} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
              <Save size={16} className="mr-1" /> Guardar Secuencia
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showEnroll} onOpenChange={setShowEnroll}>
        <DialogContent className="bg-card border-input text-foreground max-w-md" data-testid="enroll-form-dialog">
          <DialogHeader><DialogTitle>Inscribir Lead en Secuencia</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-muted-foreground text-sm">Lead</Label>
              <Select value={enrollForm.lead_id} onValueChange={v => setEnrollForm(f => ({ ...f, lead_id: v }))}>
                <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona lead" /></SelectTrigger>
                <SelectContent className="bg-muted border-input max-h-48">
                  {leads.filter(l => l.funnel_stage === "cliente_nuevo" || l.funnel_stage === "cliente_activo").map(l => (
                    <SelectItem key={l.id} value={l.id}>{l.name} - {l.whatsapp}</SelectItem>
                  ))}
                  {leads.filter(l => l.funnel_stage !== "cliente_nuevo" && l.funnel_stage !== "cliente_activo").map(l => (
                    <SelectItem key={l.id} value={l.id}>{l.name} - {l.whatsapp}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-muted-foreground text-sm">Secuencia</Label>
              <Select value={enrollForm.sequence_id} onValueChange={v => setEnrollForm(f => ({ ...f, sequence_id: v }))}>
                <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona secuencia" /></SelectTrigger>
                <SelectContent className="bg-muted border-input">
                  {sequences.filter(s => s.active).map(s => <SelectItem key={s.id} value={s.id}>{s.product_name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <Button data-testid="confirm-enroll-btn" onClick={handleEnroll} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
              <UserCheck size={16} className="mr-1" /> Inscribir
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
