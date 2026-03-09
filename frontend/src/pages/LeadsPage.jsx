import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { Plus, Search, Trash2, Edit, Eye, MessageSquare, GripVertical } from "lucide-react";

const STAGE_CONFIG = {
  nuevo: { label: "Prospecto", color: "#3B82F6", bg: "#DBEAFE" },
  interesado: { label: "Interesado", color: "#8B5CF6", bg: "#EDE9FE" },
  en_negociacion: { label: "En Negociacion", color: "#F59E0B", bg: "#FEF3C7" },
  cliente_nuevo: { label: "Cliente Nuevo", color: "#10B981", bg: "#D1FAE5" },
  cliente_activo: { label: "Cliente Activo", color: "#059669", bg: "#A7F3D0" },
  perdido: { label: "Perdido", color: "#EF4444", bg: "#FEE2E2" },
};
const STAGE_KEYS = Object.keys(STAGE_CONFIG);
const SOURCES = ["TV", "QR", "Fibeca", "pauta_digital", "web", "referido", "otro", "WhatsApp", "Chat IA", "Carga masiva"];

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [editLead, setEditLead] = useState(null);
  const [draggedLead, setDraggedLead] = useState(null);
  const [dragOverStage, setDragOverStage] = useState(null);
  const [form, setForm] = useState({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" });

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (search) params.search = search;
      if (sourceFilter) params.source = sourceFilter;
      const res = await axios.get(`${API}/leads`, { params });
      setLeads(res.data.leads);
      setTotal(res.data.total);
    } catch { toast.error("Error al cargar leads"); }
    setLoading(false);
  }, [search, sourceFilter]);

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
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, funnel_stage: newStage } : l));
      toast.success("Etapa actualizada");
    } catch { toast.error("Error al cambiar etapa"); }
  };

  const openWhatsApp = (whatsapp) => {
    if (!whatsapp) return toast.error("Sin numero de WhatsApp");
    const clean = whatsapp.replace(/[^0-9]/g, "");
    window.open(`https://wa.me/${clean}`, "_blank");
  };

  const formatDate = (d) => {
    if (!d) return "";
    try {
      const date = new Date(d);
      return date.toLocaleDateString("es-EC", { day: "2-digit", month: "2-digit", year: "2-digit" }) + " " + date.toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" });
    } catch { return d.slice(0, 16); }
  };

  // Drag and drop handlers
  const onDragStart = (e, lead) => {
    setDraggedLead(lead);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", lead.id);
  };
  const onDragOver = (e, stage) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverStage(stage);
  };
  const onDragLeave = () => { setDragOverStage(null); };
  const onDrop = (e, stage) => {
    e.preventDefault();
    setDragOverStage(null);
    if (draggedLead && draggedLead.funnel_stage !== stage) {
      handleStageChange(draggedLead.id, stage);
    }
    setDraggedLead(null);
  };
  const onDragEnd = () => { setDraggedLead(null); setDragOverStage(null); };

  const leadsByStage = {};
  STAGE_KEYS.forEach(s => { leadsByStage[s] = []; });
  leads.forEach(l => {
    const s = l.funnel_stage || "nuevo";
    if (leadsByStage[s]) leadsByStage[s].push(l);
    else leadsByStage["nuevo"].push(l);
  });

  return (
    <div data-testid="leads-page" className="space-y-4 animate-fade-in-up h-full flex flex-col">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Gestion de Leads</h1>
          <p className="text-sm text-muted-foreground">Funnel de ventas con IA &middot; {total} leads</p>
        </div>
        <Button data-testid="add-lead-btn" onClick={() => { setEditLead(null); setForm({ name: "", whatsapp: "", city: "", email: "", product_interest: "", source: "web", notes: "", funnel_stage: "nuevo" }); setShowAdd(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
          <Plus size={16} className="mr-1" /> Nuevo Lead
        </Button>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input data-testid="leads-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nombre o telefono..." className="pl-10 bg-muted/50 border-input text-foreground h-10" />
        </div>
        <Select value={sourceFilter || "all"} onValueChange={v => setSourceFilter(v === "all" ? "" : v)}>
          <SelectTrigger data-testid="source-filter" className="w-36 bg-muted/50 border-input text-foreground h-10"><SelectValue placeholder="Todas" /></SelectTrigger>
          <SelectContent className="bg-card border-input">
            <SelectItem value="all">Todas</SelectItem>
            {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48 text-muted-foreground">Cargando leads...</div>
      ) : (
        <div className="flex-1 overflow-x-auto pb-4">
          <div className="flex gap-3 min-w-max h-full">
            {STAGE_KEYS.map(stageKey => {
              const cfg = STAGE_CONFIG[stageKey];
              const stageLeads = leadsByStage[stageKey];
              const isOver = dragOverStage === stageKey;
              return (
                <div
                  key={stageKey}
                  className={`flex flex-col w-[240px] flex-shrink-0 rounded-xl transition-all ${isOver ? "ring-2 ring-primary/50" : ""}`}
                  onDragOver={e => onDragOver(e, stageKey)}
                  onDragLeave={onDragLeave}
                  onDrop={e => onDrop(e, stageKey)}
                  data-testid={`stage-column-${stageKey}`}
                >
                  <div className="flex items-center justify-between px-3 py-2.5 rounded-lg mb-2" style={{ backgroundColor: cfg.bg }}>
                    <span className="text-sm font-semibold" style={{ color: cfg.color }}>{cfg.label}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-white/70 text-foreground">{stageLeads.length}</span>
                  </div>

                  <div className="flex-1 space-y-2 overflow-y-auto max-h-[calc(100vh-310px)] pr-1 pb-1 kanban-scroll">
                    {stageLeads.length === 0 && (
                      <div className="text-center py-8 text-xs text-muted-foreground">Sin leads</div>
                    )}
                    {stageLeads.map(lead => (
                      <LeadCard
                        key={lead.id}
                        lead={lead}
                        onView={() => setShowDetail(lead)}
                        onEdit={() => openEdit(lead)}
                        onDelete={() => handleDelete(lead.id)}
                        onWhatsApp={() => openWhatsApp(lead.whatsapp)}
                        onStageChange={(s) => handleStageChange(lead.id, s)}
                        onDragStart={(e) => onDragStart(e, lead)}
                        onDragEnd={onDragEnd}
                        isDragging={draggedLead?.id === lead.id}
                        formatDate={formatDate}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Add/Edit Dialog */}
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
                <Select value={form.source} onValueChange={v => setForm(f => ({ ...f, source: v }))}><SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger><SelectContent className="bg-card border-input">{SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
              </div>
              <div><Label className="text-muted-foreground text-xs">Etapa</Label>
                <Select value={form.funnel_stage} onValueChange={v => setForm(f => ({ ...f, funnel_stage: v }))}><SelectTrigger className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger><SelectContent className="bg-card border-input">{Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent></Select>
              </div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Notas</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
            <Button data-testid="save-lead-btn" onClick={handleSave} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">{editLead ? "Actualizar" : "Crear Lead"}</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!showDetail} onOpenChange={() => setShowDetail(null)}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg" data-testid="lead-detail-dialog">
          {showDetail && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {showDetail.name || "Sin nombre"}
                  <Badge style={{ borderColor: STAGE_CONFIG[showDetail.funnel_stage]?.color, color: STAGE_CONFIG[showDetail.funnel_stage]?.color }}>
                    {STAGE_CONFIG[showDetail.funnel_stage]?.label}
                  </Badge>
                </DialogTitle>
              </DialogHeader>
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

function LeadCard({ lead, onView, onEdit, onDelete, onWhatsApp, onStageChange, onDragStart, onDragEnd, isDragging, formatDate }) {
  const cfg = STAGE_CONFIG[lead.funnel_stage] || STAGE_CONFIG.nuevo;

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={`bg-card border border-border rounded-xl p-3 cursor-grab active:cursor-grabbing transition-all hover:shadow-md ${isDragging ? "opacity-40 scale-95" : "opacity-100"}`}
      data-testid={`lead-card-${lead.id}`}
    >
      <div className="flex items-start justify-between gap-1 mb-1.5">
        <p className="text-sm font-semibold text-foreground leading-tight truncate flex-1">
          {lead.name || "Sin nombre"}
        </p>
        <Badge
          variant="outline"
          className="text-[10px] px-1.5 py-0 h-5 flex-shrink-0 whitespace-nowrap"
          style={{ borderColor: cfg.color, color: cfg.color, backgroundColor: cfg.bg }}
        >
          {cfg.label}
        </Badge>
      </div>

      <p className="text-xs text-muted-foreground mb-1">{lead.whatsapp || "Sin telefono"}</p>

      {(lead.source || lead.city || lead.product_interest) && (
        <div className="text-[11px] text-muted-foreground/70 mb-1.5 space-y-0">
          {lead.source && <p>{lead.source}</p>}
          {lead.city && <p>{lead.city}</p>}
          {lead.product_interest && <p>{lead.product_interest}</p>}
        </div>
      )}

      <div className="border-t border-border/50 pt-1.5 mt-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">{formatDate(lead.last_interaction || lead.created_at)}</span>
          <div className="flex items-center gap-0.5">
            <button onClick={onView} className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="Ver datos" data-testid={`view-lead-${lead.id}`}>
              <Eye size={13} />
            </button>
            <button onClick={onEdit} className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="Editar" data-testid={`edit-lead-${lead.id}`}>
              <Edit size={13} />
            </button>
            <button onClick={onWhatsApp} className="p-1 rounded hover:bg-muted text-emerald-500 hover:text-emerald-400 transition-colors" title="WhatsApp" data-testid={`whatsapp-lead-${lead.id}`}>
              <MessageSquare size={13} />
            </button>
            <button onClick={onDelete} className="p-1 rounded hover:bg-muted text-red-400 hover:text-red-500 transition-colors" title="Eliminar" data-testid={`delete-lead-${lead.id}`}>
              <Trash2 size={13} />
            </button>
          </div>
        </div>
      </div>

      <div className="mt-1.5">
        <Select value={lead.funnel_stage} onValueChange={onStageChange}>
          <SelectTrigger
            className="h-7 text-xs w-full border-border/60 bg-muted/30 text-muted-foreground"
            data-testid={`stage-select-${lead.id}`}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-card border-input">
            {Object.entries(STAGE_CONFIG).map(([k, v]) => (
              <SelectItem key={k} value={k}>
                <span style={{ color: v.color }}>{v.label}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
