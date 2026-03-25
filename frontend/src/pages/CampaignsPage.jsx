import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2, Send, Megaphone, Users, CheckCircle, AlertCircle, Calendar } from "lucide-react";

const STAGE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "nuevo", label: "Contacto inicial" },
  { value: "interesado", label: "Chat" },
  { value: "en_negociacion", label: "En Negociación" },
  { value: "cliente_nuevo", label: "Leads ganados" },
  { value: "cliente_activo", label: "Cartera activa" },
  { value: "perdido", label: "Perdido" },
];

const STATUS_COLORS = {
  draft: "bg-muted text-muted-foreground",
  sent: "bg-green-500/15 text-green-500",
  scheduled: "bg-blue-500/15 text-blue-500",
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", description: "", campaign_type: "promo", target_stage: "", target_product: "",
    target_channel: "", message_template: "", image_url: "", active: true
  });
  const [sending, setSending] = useState(null);

  const fetch_ = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/campaigns`);
      setCampaigns(res.data);
    } catch { toast.error("Error al cargar campañas"); }
    setLoading(false);
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);

  const save = async () => {
    if (!form.name || !form.message_template) return toast.error("Nombre y mensaje son requeridos");
    try {
      await axios.post(`${API}/campaigns`, form);
      toast.success("Campaña creada");
      setShowForm(false);
      setForm({ name: "", description: "", campaign_type: "promo", target_stage: "", target_product: "", target_channel: "", message_template: "", image_url: "", active: true });
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error"); }
  };

  const remove = async (id) => {
    if (!window.confirm("¿Eliminar esta campaña?")) return;
    try {
      await axios.delete(`${API}/campaigns/${id}`);
      toast.success("Eliminada");
      fetch_();
    } catch { toast.error("Error"); }
  };

  const sendCampaign = async (id) => {
    setSending(id);
    try {
      const res = await axios.post(`${API}/campaigns/${id}/send`, { batch_size: 10 });
      toast.success(res.data.message);
      fetch_();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error al enviar"); }
    setSending(null);
  };

  const totalSent = campaigns.reduce((s, c) => s + (c.sent_count || 0), 0);
  const totalTargets = campaigns.reduce((s, c) => s + (c.target_count || 0), 0);

  return (
    <div data-testid="campaigns-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Megaphone className="h-7 w-7 text-primary" /> Promociones y Campañas
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Crea y envía campañas promocionales segmentadas</p>
        </div>
        <Button data-testid="new-campaign-btn" onClick={() => setShowForm(true)} className="bg-primary text-primary-foreground font-bold rounded-full">
          <Plus size={16} className="mr-1" /> Nueva Campaña
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{campaigns.length}</p>
          <p className="text-xs text-muted-foreground">Total Campañas</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-green-500">{campaigns.filter(c => c.status === "sent").length}</p>
          <p className="text-xs text-muted-foreground">Enviadas</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-blue-500">{totalTargets}</p>
          <p className="text-xs text-muted-foreground">Leads Objetivo</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-primary">{totalSent}</p>
          <p className="text-xs text-muted-foreground">Mensajes Enviados</p>
        </CardContent></Card>
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Cargando...</div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">No hay campañas. Crea la primera.</div>
      ) : (
        <div className="grid gap-4">
          {campaigns.map(c => (
            <Card key={c.id} data-testid={`campaign-${c.id}`} className="bg-card border-border rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-foreground">{c.name}</h3>
                      <Badge className={`text-[10px] ${STATUS_COLORS[c.status] || STATUS_COLORS.draft}`}>
                        {c.status === "sent" ? "Enviada" : c.status === "scheduled" ? "Programada" : "Borrador"}
                      </Badge>
                    </div>
                    {c.description && <p className="text-xs text-muted-foreground mb-2">{c.description}</p>}
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {c.target_stage && <span className="text-[10px] px-1.5 py-0 rounded bg-violet-500/15 text-violet-400">Etapa: {STAGE_OPTIONS.find(s => s.value === c.target_stage)?.label || c.target_stage}</span>}
                      {c.target_product && <span className="text-[10px] px-1.5 py-0 rounded bg-amber-500/15 text-amber-500">Producto: {c.target_product}</span>}
                      {c.target_channel && <span className="text-[10px] px-1.5 py-0 rounded bg-emerald-500/15 text-emerald-500">Canal: {c.target_channel}</span>}
                    </div>
                    <p className="text-xs text-muted-foreground bg-muted/30 rounded p-2 line-clamp-2">{c.message_template}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Users size={12} /> {c.target_count} leads</span>
                      <span className="flex items-center gap-1"><CheckCircle size={12} className="text-green-500" /> {c.sent_count} enviados</span>
                      {c.failed_count > 0 && <span className="flex items-center gap-1"><AlertCircle size={12} className="text-red-400" /> {c.failed_count} fallidos</span>}
                      {c.last_sent_at && <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(c.last_sent_at).toLocaleDateString("es-EC")}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    <Button data-testid={`send-campaign-${c.id}`} variant="outline" size="sm" disabled={sending === c.id}
                      className="text-primary hover:bg-primary/10 h-8 text-xs" onClick={() => sendCampaign(c.id)}>
                      <Send size={12} className="mr-1" /> {sending === c.id ? "Enviando..." : "Enviar"}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-red-400 h-8" onClick={() => remove(c.id)}>
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
        <DialogContent className="bg-card border-border max-w-lg max-h-[80vh] overflow-y-auto" data-testid="campaign-form-dialog">
          <DialogHeader><DialogTitle>Nueva Campaña</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-muted-foreground text-xs">Nombre *</Label>
              <Input data-testid="campaign-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input" placeholder="Promo Verano 2026" /></div>
            <div><Label className="text-muted-foreground text-xs">Descripción</Label>
              <Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="bg-muted border-input" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Etapa objetivo</Label>
                <Select value={form.target_stage || "all"} onValueChange={v => setForm(f => ({ ...f, target_stage: v === "all" ? "" : v }))}>
                  <SelectTrigger className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">{STAGE_OPTIONS.map(s => <SelectItem key={s.value || "all"} value={s.value || "all"}>{s.label}</SelectItem>)}</SelectContent>
                </Select></div>
              <div><Label className="text-muted-foreground text-xs">Producto</Label>
                <Input value={form.target_product} onChange={e => setForm(f => ({ ...f, target_product: e.target.value }))} className="bg-muted border-input" placeholder="Bombro, Gomitas..." /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Canal</Label>
                <Select value={form.target_channel || "all"} onValueChange={v => setForm(f => ({ ...f, target_channel: v === "all" ? "" : v }))}>
                  <SelectTrigger className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input"><SelectItem value="all">Todos</SelectItem><SelectItem value="TV/QR">TV/QR</SelectItem><SelectItem value="Fibeca">Fibeca</SelectItem><SelectItem value="Evento">Evento</SelectItem><SelectItem value="WhatsApp">WhatsApp</SelectItem></SelectContent>
                </Select></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Mensaje (usa {"{nombre}"} para personalizar) *</Label>
              <Textarea data-testid="campaign-message" value={form.message_template} onChange={e => setForm(f => ({ ...f, message_template: e.target.value }))} className="bg-muted border-input" rows={3} placeholder="Hola {nombre}, tenemos una promoción especial..." /></div>
            <div><Label className="text-muted-foreground text-xs">URL de imagen (opcional)</Label>
              <Input value={form.image_url} onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))} className="bg-muted border-input" placeholder="https://..." /></div>
            <Button data-testid="save-campaign-btn" onClick={save} className="w-full bg-primary text-primary-foreground font-bold rounded-full">Crear Campaña</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
