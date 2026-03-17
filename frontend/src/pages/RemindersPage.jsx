import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2, Play, Bell, Clock, Users, CheckCircle } from "lucide-react";

const STAGE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "nuevo", label: "Contacto inicial" },
  { value: "interesado", label: "Chat" },
  { value: "en_negociacion", label: "En Negociación" },
  { value: "cliente_nuevo", label: "Leads ganados" },
  { value: "cliente_activo", label: "Cartera activa" },
  { value: "perdido", label: "Perdido" },
];

export default function RemindersPage() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [executing, setExecuting] = useState(null);
  const [form, setForm] = useState({
    name: "", message_template: "", target_stage: "", target_product: "",
    days_since_last_interaction: 7, batch_size: 10, active: true
  });

  const fetch_ = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/reminders`);
      setReminders(res.data);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);

  const save = async () => {
    if (!form.name || !form.message_template) return toast.error("Nombre y mensaje son requeridos");
    try {
      await axios.post(`${API}/reminders`, form);
      toast.success("Recordatorio creado");
      setShowForm(false);
      setForm({ name: "", message_template: "", target_stage: "", target_product: "", days_since_last_interaction: 7, batch_size: 10, active: true });
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error"); }
  };

  const remove = async (id) => {
    if (!window.confirm("¿Eliminar?")) return;
    try { await axios.delete(`${API}/reminders/${id}`); toast.success("Eliminado"); fetch_(); }
    catch { toast.error("Error"); }
  };

  const execute = async (id) => {
    setExecuting(id);
    try {
      const res = await axios.post(`${API}/reminders/${id}/execute`);
      toast.success(res.data.message);
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error"); }
    setExecuting(null);
  };

  const totalSent = reminders.reduce((s, r) => s + (r.total_sent || 0), 0);

  return (
    <div data-testid="reminders-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Bell className="h-7 w-7 text-amber-500" /> Recordatorios
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Envía recordatorios por lotes a leads inactivos</p>
        </div>
        <Button data-testid="new-reminder-btn" onClick={() => setShowForm(true)} className="bg-amber-600 hover:bg-amber-700 text-white rounded-full">
          <Plus size={16} className="mr-1" /> Nuevo Recordatorio
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{reminders.length}</p>
          <p className="text-xs text-muted-foreground">Recordatorios</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-green-500">{totalSent}</p>
          <p className="text-xs text-muted-foreground">Total Enviados</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-amber-500">{reminders.filter(r => r.active).length}</p>
          <p className="text-xs text-muted-foreground">Activos</p>
        </CardContent></Card>
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Cargando...</div>
      ) : reminders.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">No hay recordatorios configurados.</div>
      ) : (
        <div className="grid gap-4">
          {reminders.map(r => (
            <Card key={r.id} data-testid={`reminder-${r.id}`} className="bg-card border-border rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-foreground">{r.name}</h3>
                      <Badge className={`text-[10px] ${r.active ? "bg-green-500/15 text-green-500" : "bg-muted text-muted-foreground"}`}>
                        {r.active ? "Activo" : "Inactivo"}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      <span className="text-[10px] px-1.5 py-0 rounded bg-amber-500/15 text-amber-500 flex items-center gap-0.5"><Clock size={9} /> {r.days_since_last_interaction}d inactividad</span>
                      <span className="text-[10px] px-1.5 py-0 rounded bg-blue-500/15 text-blue-400 flex items-center gap-0.5"><Users size={9} /> lote de {r.batch_size}</span>
                      {r.target_stage && <span className="text-[10px] px-1.5 py-0 rounded bg-violet-500/15 text-violet-400">Etapa: {STAGE_OPTIONS.find(s => s.value === r.target_stage)?.label}</span>}
                      {r.target_product && <span className="text-[10px] px-1.5 py-0 rounded bg-emerald-500/15 text-emerald-500">Producto: {r.target_product}</span>}
                    </div>
                    <p className="text-xs text-muted-foreground bg-muted/30 rounded p-2 line-clamp-2">{r.message_template}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><CheckCircle size={12} className="text-green-500" /> {r.total_sent || 0} enviados total</span>
                      {r.last_run && <span>Última ejecución: {new Date(r.last_run).toLocaleDateString("es-EC")}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    <Button data-testid={`execute-reminder-${r.id}`} variant="outline" size="sm" disabled={executing === r.id}
                      className="text-amber-500 hover:bg-amber-500/10 h-8 text-xs" onClick={() => execute(r.id)}>
                      <Play size={12} className="mr-1" /> {executing === r.id ? "Enviando..." : "Ejecutar"}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-red-400 h-8" onClick={() => remove(r.id)}>
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="bg-card border-border max-w-md" data-testid="reminder-form-dialog">
          <DialogHeader><DialogTitle>Nuevo Recordatorio</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-muted-foreground text-xs">Nombre *</Label>
              <Input data-testid="reminder-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input" placeholder="Recordatorio leads inactivos" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Días sin interacción</Label>
                <Input type="number" value={form.days_since_last_interaction} onChange={e => setForm(f => ({ ...f, days_since_last_interaction: parseInt(e.target.value) || 7 }))} className="bg-muted border-input" /></div>
              <div><Label className="text-muted-foreground text-xs">Tamaño de lote</Label>
                <Input type="number" value={form.batch_size} onChange={e => setForm(f => ({ ...f, batch_size: parseInt(e.target.value) || 10 }))} className="bg-muted border-input" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Etapa</Label>
                <Select value={form.target_stage || "all"} onValueChange={v => setForm(f => ({ ...f, target_stage: v === "all" ? "" : v }))}>
                  <SelectTrigger className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">{STAGE_OPTIONS.map(s => <SelectItem key={s.value || "all"} value={s.value || "all"}>{s.label}</SelectItem>)}</SelectContent>
                </Select></div>
              <div><Label className="text-muted-foreground text-xs">Producto</Label>
                <Input value={form.target_product} onChange={e => setForm(f => ({ ...f, target_product: e.target.value }))} className="bg-muted border-input" /></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Mensaje (usa {"{nombre}"}) *</Label>
              <Textarea data-testid="reminder-message" value={form.message_template} onChange={e => setForm(f => ({ ...f, message_template: e.target.value }))} className="bg-muted border-input" rows={3} placeholder="Hola {nombre}, te extrañamos..." /></div>
            <Button data-testid="save-reminder-btn" onClick={save} className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-full">Crear Recordatorio</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
