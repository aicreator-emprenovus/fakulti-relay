import React, { useState, useEffect, useRef } from "react";
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
import { Plus, Send, Trash2, Megaphone, Edit, ImagePlus, Link, X, Eye, Smartphone } from "lucide-react";

const STAGE_CONFIG = {
  nuevo: { label: "Contacto inicial", color: "#3B82F6" },
  interesado: { label: "Chat", color: "#8B5CF6" },
  en_negociacion: { label: "En Negociación", color: "#F59E0B" },
  cliente_nuevo: { label: "Leads ganados", color: "#10B981" },
  cliente_activo: { label: "Cartera activa", color: "#059669" },
  perdido: { label: "Perdido", color: "#EF4444" },
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [products, setProducts] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: "", description: "", campaign_type: "promo", target_stage: "", target_product: "", target_channel: "", message_template: "", image_url: "", scheduled_date: "" });
  const [sending, setSending] = useState({});
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => {
    fetchCampaigns();
    axios.get(`${API}/products`).then(res => setProducts(res.data)).catch(() => {});
  }, []);

  const fetchCampaigns = () => axios.get(`${API}/campaigns`).then(res => setCampaigns(res.data)).catch(() => {});

  const resetForm = () => {
    setForm({ name: "", description: "", campaign_type: "promo", target_stage: "", target_product: "", target_channel: "", message_template: "", image_url: "", scheduled_date: "" });
    setEditingId(null);
  };

  const openCreate = () => { resetForm(); setShowDialog(true); };

  const openEdit = (c) => {
    setForm({
      name: c.name || "",
      description: c.description || "",
      campaign_type: c.campaign_type || "promo",
      target_stage: c.target_stage || "",
      target_product: c.target_product || "",
      target_channel: c.target_channel || "",
      message_template: c.message_template || "",
      image_url: c.image_url || "",
      scheduled_date: c.scheduled_date || "",
    });
    setEditingId(c.id);
    setShowDialog(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.message_template) return toast.error("Nombre y mensaje son obligatorios");
    try {
      if (editingId) {
        await axios.put(`${API}/campaigns/${editingId}`, form);
        toast.success("Campaña actualizada");
      } else {
        await axios.post(`${API}/campaigns`, form);
        toast.success("Campaña creada");
      }
      setShowDialog(false);
      resetForm();
      fetchCampaigns();
    } catch (err) { toast.error(err.response?.data?.detail || "Error al guardar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar esta campaña?")) return;
    await axios.delete(`${API}/campaigns/${id}`);
    toast.success("Campaña eliminada");
    fetchCampaigns();
  };

  const handleSend = async (id) => {
    if (!window.confirm("¿Enviar esta campaña a los leads seleccionados?")) return;
    setSending(s => ({ ...s, [id]: true }));
    try {
      const res = await axios.post(`${API}/campaigns/${id}/send`, { batch_size: 50 });
      toast.success(res.data.message);
      fetchCampaigns();
    } catch (err) { toast.error(err.response?.data?.detail || "Error al enviar"); }
    setSending(s => ({ ...s, [id]: false }));
  };

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return toast.error("Solo se permiten imágenes");
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await axios.post(`${API}/upload-image`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      const fullUrl = `${process.env.REACT_APP_BACKEND_URL}${res.data.url}`;
      setForm(f => ({ ...f, image_url: fullUrl }));
      toast.success("Imagen subida");
    } catch (err) { toast.error("Error al subir imagen"); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div data-testid="campaigns-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Campañas</h1>
          <p className="text-sm text-muted-foreground">Promociones y envíos masivos por WhatsApp</p>
        </div>
        <Button data-testid="new-campaign-btn" onClick={openCreate} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
          <Plus size={16} className="mr-1" /> Nueva Campaña
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {campaigns.map(c => (
          <Card key={c.id} data-testid={`campaign-card-${c.id}`} className="bg-card border-border rounded-2xl overflow-hidden">
            {c.image_url && (
              <div className="w-full h-36 overflow-hidden bg-muted">
                <img src={c.image_url} alt={c.name} className="w-full h-full object-cover" onError={e => e.target.style.display = "none"} />
              </div>
            )}
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <CardTitle className="text-base text-foreground">{c.name}</CardTitle>
                <Badge variant={c.status === "sent" ? "default" : "outline"} className={c.status === "sent" ? "bg-emerald-500/20 text-emerald-500 text-[10px]" : "text-[10px]"}>
                  {c.status === "sent" ? "Enviada" : c.status === "draft" ? "Borrador" : c.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {c.description && <p className="text-xs text-muted-foreground">{c.description}</p>}
              <p className="text-xs text-muted-foreground line-clamp-2 italic">"{c.message_template}"</p>
              <div className="flex flex-wrap gap-1">
                {c.target_stage && <span className="text-[10px] px-1.5 py-0 rounded bg-blue-500/15 text-blue-500">{STAGE_CONFIG[c.target_stage]?.label || c.target_stage}</span>}
                {c.target_product && <span className="text-[10px] px-1.5 py-0 rounded bg-amber-500/15 text-amber-500">{c.target_product}</span>}
                {c.target_channel && <span className="text-[10px] px-1.5 py-0 rounded bg-violet-500/15 text-violet-400">{c.target_channel}</span>}
              </div>
              <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                <span>Alcance: {c.target_count || 0} leads</span>
                <span>Enviados: {c.sent_count || 0}</span>
              </div>
              <div className="flex items-center gap-1.5 pt-1">
                <Button data-testid={`edit-campaign-${c.id}`} variant="outline" size="sm" className="h-7 text-xs flex-1" onClick={() => openEdit(c)}>
                  <Edit size={12} className="mr-1" /> Editar
                </Button>
                <Button data-testid={`send-campaign-${c.id}`} variant="outline" size="sm" className="h-7 text-xs flex-1 text-emerald-500 hover:text-emerald-600" onClick={() => handleSend(c.id)} disabled={sending[c.id]}>
                  <Send size={12} className="mr-1" /> {sending[c.id] ? "Enviando..." : "Enviar"}
                </Button>
                <Button data-testid={`delete-campaign-${c.id}`} variant="ghost" size="sm" className="h-7 w-7 p-0 text-red-400 hover:text-red-500" onClick={() => handleDelete(c.id)}>
                  <Trash2 size={13} />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {campaigns.length === 0 && (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            <Megaphone size={40} className="mx-auto mb-3 opacity-30" />
            <p>Sin campañas creadas</p>
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-card border-border max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-foreground">{editingId ? "Editar Campaña" : "Nueva Campaña"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground">Nombre *</Label>
              <Input data-testid="campaign-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input text-foreground" placeholder="Ej: Promo Enero" />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Descripción</Label>
              <Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="bg-muted border-input text-foreground" placeholder="Breve descripción" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-muted-foreground">Etapa objetivo</Label>
                <Select value={form.target_stage || "all"} onValueChange={v => setForm(f => ({ ...f, target_stage: v === "all" ? "" : v }))}>
                  <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Todas" /></SelectTrigger>
                  <SelectContent className="bg-card border-input">
                    <SelectItem value="all">Todas</SelectItem>
                    {Object.entries(STAGE_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Producto objetivo</Label>
                <Select value={form.target_product || "all"} onValueChange={v => setForm(f => ({ ...f, target_product: v === "all" ? "" : v }))}>
                  <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Todos" /></SelectTrigger>
                  <SelectContent className="bg-card border-input">
                    <SelectItem value="all">Todos</SelectItem>
                    {products.map(p => <SelectItem key={p.id} value={p.name}>{p.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Mensaje *</Label>
              <Textarea data-testid="campaign-message" value={form.message_template} onChange={e => setForm(f => ({ ...f, message_template: e.target.value }))} className="bg-muted border-input text-foreground text-sm min-h-[80px]" placeholder="Hola {nombre}, tenemos una promo especial..." />
              <p className="text-[10px] text-muted-foreground mt-1">Usa {"{nombre}"} para personalizar</p>
            </div>

            {/* Image section */}
            <div>
              <Label className="text-xs text-muted-foreground">Imagen (opcional)</Label>
              <div className="flex gap-2 mt-1">
                <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleUpload} />
                <Button type="button" variant="outline" size="sm" className="h-8 text-xs" onClick={() => fileRef.current?.click()} disabled={uploading} data-testid="upload-campaign-image">
                  <ImagePlus size={12} className="mr-1" /> {uploading ? "Subiendo..." : "Subir imagen"}
                </Button>
                <span className="text-xs text-muted-foreground self-center">o</span>
                <Input value={form.image_url} onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))} className="bg-muted border-input text-foreground text-xs h-8 flex-1" placeholder="Pegar URL de imagen" data-testid="campaign-image-url" />
              </div>
              {form.image_url && (
                <div className="mt-2 relative inline-block">
                  <img src={form.image_url} alt="Preview" className="h-20 rounded-lg border border-border object-cover" onError={e => e.target.style.display = "none"} />
                  <button onClick={() => setForm(f => ({ ...f, image_url: "" }))} className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center text-xs">
                    <X size={10} />
                  </button>
                </div>
              )}
            </div>

            {/* WhatsApp Preview */}
            {(form.message_template || form.image_url) && (
              <div>
                <Label className="text-xs text-muted-foreground flex items-center gap-1.5 mb-2">
                  <Smartphone size={12} /> Vista previa WhatsApp
                </Label>
                <div className="rounded-xl border border-border overflow-hidden" style={{ background: "linear-gradient(135deg, #0b1412 0%, #0d1b16 100%)" }}>
                  <div className="flex items-center gap-2 px-3 py-2 bg-[#1f2c34]">
                    <div className="w-6 h-6 rounded-full bg-emerald-600/30 flex items-center justify-center">
                      <span className="text-[9px] text-emerald-400 font-bold">F</span>
                    </div>
                    <span className="text-xs text-gray-300 font-medium">Fakulti</span>
                  </div>
                  <div className="p-3" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }}>
                    <div className="max-w-[85%] ml-auto">
                      <div className="bg-[#005c4b] rounded-lg overflow-hidden shadow-lg">
                        {form.image_url && (
                          <div className="w-full">
                            <img
                              src={form.image_url}
                              alt="Vista previa"
                              className="w-full max-h-40 object-cover"
                              data-testid="campaign-preview-image"
                              onError={e => { e.target.style.display = "none"; }}
                            />
                          </div>
                        )}
                        {form.message_template && (
                          <div className="px-2.5 py-1.5">
                            <p className="text-[11px] text-gray-100 whitespace-pre-wrap leading-relaxed">
                              {form.message_template.replace("{nombre}", "Juan Pérez")}
                            </p>
                          </div>
                        )}
                        <div className="flex justify-end px-2 pb-1">
                          <span className="text-[9px] text-gray-400">
                            {new Date().toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-[10px] text-muted-foreground mt-1.5 italic">
                  Así se verá el mensaje en WhatsApp del lead (nombre de ejemplo: Juan Pérez)
                </p>
              </div>
            )}

            <Button data-testid="save-campaign-btn" onClick={handleSave} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
              {editingId ? "Guardar Cambios" : "Crear Campaña"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
