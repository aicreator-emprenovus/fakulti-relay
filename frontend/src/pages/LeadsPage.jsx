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
          <h1 className="text-3xl font-bold text-white font-heading">Leads</h1>
          <p className="text-sm text-zinc-500">{total} leads en total</p>
        </div>
        <Button data-testid="add-lead-btn" onClick={() => { setEditLead(null); setForm({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" }); setShowAdd(true); }} className="bg-lime-400 text-black font-bold rounded-full hover:bg-lime-300 shadow-[0_0_20px_rgba(163,230,53,0.3)]">
          <Plus size={16} className="mr-1" /> Agregar Lead
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-600" />
          <Input data-testid="leads-search" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Buscar por nombre, WhatsApp..." className="pl-10 bg-zinc-900/50 border-zinc-800 text-white h-10" />
        </div>
        <Select value={stageFilter} onValueChange={v => { setStageFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger data-testid="stage-filter" className="w-44 bg-zinc-900/50 border-zinc-800 text-white h-10"><SelectValue placeholder="Etapa" /></SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            <SelectItem value="all">Todas las etapas</SelectItem>
            {Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={sourceFilter} onValueChange={v => { setSourceFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger data-testid="source-filter" className="w-40 bg-zinc-900/50 border-zinc-800 text-white h-10"><SelectValue placeholder="Fuente" /></SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            <SelectItem value="all">Todas</SelectItem>
            {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-white/6">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-zinc-900/50 border-b border-white/6">
              <th className="text-left p-3 text-zinc-400 font-medium">Nombre</th>
              <th className="text-left p-3 text-zinc-400 font-medium hidden md:table-cell">WhatsApp</th>
              <th className="text-left p-3 text-zinc-400 font-medium hidden lg:table-cell">Ciudad</th>
              <th className="text-left p-3 text-zinc-400 font-medium hidden lg:table-cell">Fuente</th>
              <th className="text-left p-3 text-zinc-400 font-medium">Etapa</th>
              <th className="text-right p-3 text-zinc-400 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} className="border-b border-white/3 hover:bg-zinc-900/30 transition-colors" data-testid={`lead-row-${lead.id}`}>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "20", color: STAGE_CONFIG[lead.funnel_stage]?.color }}>
                      {lead.name?.[0]}
                    </div>
                    <div>
                      <p className="text-white font-medium">{lead.name}</p>
                      <p className="text-xs text-zinc-500 md:hidden">{lead.whatsapp}</p>
                    </div>
                  </div>
                </td>
                <td className="p-3 text-zinc-400 hidden md:table-cell">{lead.whatsapp}</td>
                <td className="p-3 text-zinc-400 hidden lg:table-cell">{lead.city}</td>
                <td className="p-3 hidden lg:table-cell">
                  <Badge variant="outline" className="text-xs" style={{ borderColor: "#52525b" }}>{lead.source}</Badge>
                </td>
                <td className="p-3">
                  <Select value={lead.funnel_stage} onValueChange={v => handleStageChange(lead.id, v)}>
                    <SelectTrigger className="h-7 text-xs w-32 border-0 p-1" style={{ color: STAGE_CONFIG[lead.funnel_stage]?.color, backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "15" }}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      {Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}><span style={{ color: v.color }}>{v.label}</span></SelectItem>)}
                    </SelectContent>
                  </Select>
                </td>
                <td className="p-3 text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-zinc-400 hover:text-white" onClick={() => setShowDetail(lead)} data-testid={`view-lead-${lead.id}`}><Eye size={14} /></Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-zinc-400 hover:text-lime-400" onClick={() => openEdit(lead)} data-testid={`edit-lead-${lead.id}`}><Edit size={14} /></Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-zinc-400 hover:text-red-400" onClick={() => handleDelete(lead.id)} data-testid={`delete-lead-${lead.id}`}><Trash2 size={14} /></Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {leads.length === 0 && <div className="text-center py-12 text-zinc-600">No se encontraron leads</div>}
      </div>

      {pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /></Button>
          <span className="text-sm text-zinc-400 flex items-center">{page} / {pages}</span>
          <Button variant="ghost" size="sm" disabled={page >= pages} onClick={() => setPage(p => p + 1)}><ChevronRight size={16} /></Button>
        </div>
      )}

      <Dialog open={showAdd} onOpenChange={v => { setShowAdd(v); if (!v) setEditLead(null); }}>
        <DialogContent className="bg-[#0A0A0A] border-zinc-800 text-white max-w-md" data-testid="lead-form-dialog">
          <DialogHeader><DialogTitle>{editLead ? "Editar Lead" : "Nuevo Lead"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-zinc-400 text-xs">Nombre *</Label><Input data-testid="lead-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" /></div>
            <div><Label className="text-zinc-400 text-xs">WhatsApp *</Label><Input data-testid="lead-whatsapp" value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" placeholder="+593..." /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-zinc-400 text-xs">Ciudad</Label><Input value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" /></div>
              <div><Label className="text-zinc-400 text-xs">Email</Label><Input value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" /></div>
            </div>
            <div><Label className="text-zinc-400 text-xs">Producto Interes</Label><Input value={form.product_interest} onChange={e => setForm(f => ({ ...f, product_interest: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-zinc-400 text-xs">Fuente</Label>
                <Select value={form.source} onValueChange={v => setForm(f => ({ ...f, source: v }))}><SelectTrigger className="bg-zinc-900 border-zinc-800 text-white"><SelectValue /></SelectTrigger><SelectContent className="bg-zinc-900 border-zinc-800">{SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
              </div>
              <div><Label className="text-zinc-400 text-xs">Etapa</Label>
                <Select value={form.funnel_stage} onValueChange={v => setForm(f => ({ ...f, funnel_stage: v }))}><SelectTrigger className="bg-zinc-900 border-zinc-800 text-white"><SelectValue /></SelectTrigger><SelectContent className="bg-zinc-900 border-zinc-800">{Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent></Select>
              </div>
            </div>
            <div><Label className="text-zinc-400 text-xs">Notas</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} className="bg-zinc-900 border-zinc-800 text-white" rows={2} /></div>
            <Button data-testid="save-lead-btn" onClick={handleSave} className="w-full bg-lime-400 text-black font-bold rounded-full hover:bg-lime-300">{editLead ? "Actualizar" : "Crear Lead"}</Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDetail} onOpenChange={() => setShowDetail(null)}>
        <DialogContent className="bg-[#0A0A0A] border-zinc-800 text-white max-w-lg" data-testid="lead-detail-dialog">
          {showDetail && (
            <>
              <DialogHeader><DialogTitle className="flex items-center gap-2">{showDetail.name} <Badge style={{ borderColor: STAGE_CONFIG[showDetail.funnel_stage]?.color, color: STAGE_CONFIG[showDetail.funnel_stage]?.color }}>{STAGE_CONFIG[showDetail.funnel_stage]?.label}</Badge></DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-zinc-500">WhatsApp:</span><p className="text-white">{showDetail.whatsapp}</p></div>
                  <div><span className="text-zinc-500">Ciudad:</span><p className="text-white">{showDetail.city || "N/A"}</p></div>
                  <div><span className="text-zinc-500">Email:</span><p className="text-white">{showDetail.email || "N/A"}</p></div>
                  <div><span className="text-zinc-500">Fuente:</span><p className="text-white">{showDetail.source}</p></div>
                  <div><span className="text-zinc-500">Producto Interes:</span><p className="text-white">{showDetail.product_interest || "N/A"}</p></div>
                  <div><span className="text-zinc-500">Juego Usado:</span><p className="text-white">{showDetail.game_used || "Ninguno"}</p></div>
                  <div><span className="text-zinc-500">Premio:</span><p className="text-white">{showDetail.prize_obtained || "N/A"}</p></div>
                  <div><span className="text-zinc-500">Cupon:</span><p className="text-white">{showDetail.coupon_used || "N/A"}</p></div>
                </div>
                {showDetail.purchase_history?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-zinc-400 mb-2">Historial de Compras</h4>
                    {showDetail.purchase_history.map((p, i) => (
                      <div key={i} className="flex justify-between items-center p-2 rounded bg-zinc-900/50 mb-1 text-sm">
                        <span className="text-white">{p.product_name} x{p.quantity}</span>
                        <span className="text-lime-400">${p.price}</span>
                      </div>
                    ))}
                  </div>
                )}
                {showDetail.notes && <div><span className="text-zinc-500 text-sm">Notas:</span><p className="text-sm text-zinc-300">{showDetail.notes}</p></div>}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
