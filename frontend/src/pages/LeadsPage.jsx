import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Plus, Search, Filter, Trash2, Edit, Eye, Phone, MapPin, ChevronLeft, ChevronRight } from "lucide-react";

const STAGE_CONFIG = {
  nuevo: { label: "Nuevo", color: "#3B82F6" },
  interesado: { label: "Interesado", color: "#8B5CF6" },
  caliente: { label: "Caliente", color: "#F59E0B" },
  cliente_nuevo: { label: "Cliente Nuevo", color: "#10B981" },
  cliente_activo: { label: "Cliente Activo", color: "#A3E635" },
  frio: { label: "Frio", color: "#64748B" },
};

const SOURCES = ["TV", "QR", "Fibeca", "pauta_digital", "web", "referido", "otro"];

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [editLead, setEditLead] = useState(null);
  const [form, setForm] = useState({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" });

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: 20 };
      if (search) params.search = search;
      if (stageFilter) params.stage = stageFilter;
      if (sourceFilter) params.source = sourceFilter;
      const res = await axios.get(`${API}/leads`, { params });
      setLeads(res.data.leads);
      setTotal(res.data.total);
      setPages(res.data.pages);
    } catch { toast.error("Error al cargar leads"); }
    setLoading(false);
  }, [page, search, stageFilter, sourceFilter]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  const handleSave = async () => {
    try {
      if (editLead) {
        await axios.put(`${API}/leads/${editLead.id}`, form);
        toast.success("Lead actualizado");
      } else {
        await axios.post(`${API}/leads`, form);
        toast.success("Lead creado");
      }
      setShowAdd(false);
      setEditLead(null);
      setForm({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" });
      fetchLeads();
    } catch (err) { toast.error(err.response?.data?.detail || "Error al guardar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Eliminar este lead?")) return;
    try {
      await axios.delete(`${API}/leads/${id}`);
      toast.success("Lead eliminado");
      fetchLeads();
    } catch { toast.error("Error al eliminar"); }
  };

  const openEdit = (lead) => {
    setEditLead(lead);
    setForm({ name: lead.name, whatsapp: lead.whatsapp, city: lead.city || "", email: lead.email || "", product_interest: lead.product_interest || "", source: lead.source || "web", notes: lead.notes || "", funnel_stage: lead.funnel_stage });
    setShowAdd(true);
  };

  const handleStageChange = async (leadId, newStage) => {
    try {
      await axios.put(`${API}/leads/${leadId}/stage?stage=${newStage}`);
      toast.success("Etapa actualizada");
      fetchLeads();
      if (showDetail?.id === leadId) setShowDetail(prev => ({ ...prev, funnel_stage: newStage }));
    } catch { toast.error("Error al cambiar etapa"); }
  };

  return (
    <div data-testid="leads-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Leads</h1>
          <p className="text-sm text-muted-foreground">{total} leads en total</p>
        </div>
        <Button data-testid="add-lead-btn" onClick={() => { setEditLead(null); setForm({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" }); setShowAdd(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
          <Plus size={16} className="mr-1" /> Agregar Lead
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input data-testid="leads-search" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Buscar por nombre, WhatsApp..." className="pl-10 bg-muted/50 border-input text-foreground h-10" />
        </div>
        <Select value={stageFilter} onValueChange={v => { setStageFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger data-testid="stage-filter" className="w-44 bg-muted/50 border-input text-foreground h-10"><SelectValue placeholder="Etapa" /></SelectTrigger>
          <SelectContent className="bg-muted border-input">
            <SelectItem value="all">Todas las etapas</SelectItem>
            {Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={sourceFilter} onValueChange={v => { setSourceFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger data-testid="source-filter" className="w-40 bg-muted/50 border-input text-foreground h-10"><SelectValue placeholder="Fuente" /></SelectTrigger>
          <SelectContent className="bg-muted border-input">
            <SelectItem value="all">Todas</SelectItem>
            {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-muted/50 border-b border-border">
              <th className="text-left p-3 text-muted-foreground font-medium">Nombre</th>
              <th className="text-left p-3 text-muted-foreground font-medium hidden md:table-cell">WhatsApp</th>
              <th className="text-left p-3 text-muted-foreground font-medium hidden lg:table-cell">Ciudad</th>
              <th className="text-left p-3 text-muted-foreground font-medium hidden lg:table-cell">Fuente</th>
              <th className="text-left p-3 text-muted-foreground font-medium">Etapa</th>
              <th className="text-right p-3 text-muted-foreground font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors" data-testid={`lead-row-${lead.id}`}>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "20", color: STAGE_CONFIG[lead.funnel_stage]?.color }}>
                      {lead.name?.[0]}
                    </div>
                    <div>
                      <p className="text-foreground font-medium">{lead.name}</p>
                      <p className="text-xs text-muted-foreground md:hidden">{lead.whatsapp}</p>
                    </div>
                  </div>
                </td>
                <td className="p-3 text-muted-foreground hidden md:table-cell">{lead.whatsapp}</td>
                <td className="p-3 text-muted-foreground hidden lg:table-cell">{lead.city}</td>
                <td className="p-3 hidden lg:table-cell">
                  <Badge variant="outline" className="text-xs" style={{ borderColor: "#52525b" }}>{lead.source}</Badge>
                </td>
                <td className="p-3">
                  <Select value={lead.funnel_stage} onValueChange={v => handleStageChange(lead.id, v)}>
                    <SelectTrigger className="h-7 text-xs w-32 border-0 p-1" style={{ color: STAGE_CONFIG[lead.funnel_stage]?.color, backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "15" }}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-muted border-input">
                      {Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}><span style={{ color: v.color }}>{v.label}</span></SelectItem>)}
                    </SelectContent>
                  </Select>
                </td>
                <td className="p-3 text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground" onClick={() => setShowDetail(lead)} data-testid={`view-lead-${lead.id}`}><Eye size={14} /></Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-primary" onClick={() => openEdit(lead)} data-testid={`edit-lead-${lead.id}`}><Edit size={14} /></Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400" onClick={() => handleDelete(lead.id)} data-testid={`delete-lead-${lead.id}`}><Trash2 size={14} /></Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {leads.length === 0 && <div className="text-center py-12 text-muted-foreground">No se encontraron leads</div>}
      </div>

      {pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /></Button>
          <span className="text-sm text-muted-foreground flex items-center">{page} / {pages}</span>
          <Button variant="ghost" size="sm" disabled={page >= pages} onClick={() => setPage(p => p + 1)}><ChevronRight size={16} /></Button>
        </div>
      )}

      <Dialog open={showAdd} onOpenChange={v => { setShowAdd(v); if (!v) setEditLead(null); }}>
        <DialogContent className="bg-card border-input text-foreground max-w-md" data-testid="lead-form-dialog">
          <DialogHeader><DialogTitle>{editLead ? "Editar Lead" : "Nuevo Lead"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-muted-foreground text-xs">Nombre *</Label><Input data-testid="lead-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            <div><Label className="text-muted-foreground text-xs">WhatsApp *</Label><Input data-testid="lead-whatsapp" value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} className="bg-muted border-input text-foreground" placeholder="+593..." /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Ciudad</Label><Input value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
              <div><Label className="text-muted-foreground text-xs">Email</Label><Input value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Producto Interes</Label><Input value={form.product_interest} onChange={e => setForm(f => ({ ...f, product_interest: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Fuente</Label>
                <Select value={form.source} onValueChange={v => setForm(f => ({ ...f, source: v }))}><SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger><SelectContent className="bg-muted border-input">{SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
              </div>
              <div><Label className="text-muted-foreground text-xs">Etapa</Label>
                <Select value={form.funnel_stage} onValueChange={v => setForm(f => ({ ...f, funnel_stage: v }))}><SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger><SelectContent className="bg-muted border-input">{Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent></Select>
              </div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Notas</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
            <Button data-testid="save-lead-btn" onClick={handleSave} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">{editLead ? "Actualizar" : "Crear Lead"}</Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDetail} onOpenChange={() => setShowDetail(null)}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg" data-testid="lead-detail-dialog">
          {showDetail && (
            <>
              <DialogHeader><DialogTitle className="flex items-center gap-2">{showDetail.name} <Badge style={{ borderColor: STAGE_CONFIG[showDetail.funnel_stage]?.color, color: STAGE_CONFIG[showDetail.funnel_stage]?.color }}>{STAGE_CONFIG[showDetail.funnel_stage]?.label}</Badge></DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-muted-foreground">WhatsApp:</span><p className="text-foreground">{showDetail.whatsapp}</p></div>
                  <div><span className="text-muted-foreground">Ciudad:</span><p className="text-foreground">{showDetail.city || "N/A"}</p></div>
                  <div><span className="text-muted-foreground">Email:</span><p className="text-foreground">{showDetail.email || "N/A"}</p></div>
                  <div><span className="text-muted-foreground">Fuente:</span><p className="text-foreground">{showDetail.source}</p></div>
                  <div><span className="text-muted-foreground">Producto Interes:</span><p className="text-foreground">{showDetail.product_interest || "N/A"}</p></div>
                  <div><span className="text-muted-foreground">Juego Usado:</span><p className="text-foreground">{showDetail.game_used || "Ninguno"}</p></div>
                  <div><span className="text-muted-foreground">Premio:</span><p className="text-foreground">{showDetail.prize_obtained || "N/A"}</p></div>
                  <div><span className="text-muted-foreground">Cupon:</span><p className="text-foreground">{showDetail.coupon_used || "N/A"}</p></div>
                </div>
                {showDetail.purchase_history?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-muted-foreground mb-2">Historial de Compras</h4>
                    {showDetail.purchase_history.map((p, i) => (
                      <div key={i} className="flex justify-between items-center p-2 rounded bg-muted/50 mb-1 text-sm">
                        <span className="text-foreground">{p.product_name} x{p.quantity}</span>
                        <span className="text-primary">${p.price}</span>
                      </div>
                    ))}
                  </div>
                )}
                {showDetail.notes && <div><span className="text-muted-foreground text-sm">Notas:</span><p className="text-sm text-foreground/80">{showDetail.notes}</p></div>}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
