import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { QrCode, Plus, Pencil, Trash2, Download, Link2, Copy, Eye, EyeOff, Target } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const CHANNELS = ["TV/QR", "Fibeca", "Evento", "Pauta Digital", "Web", "Redes Sociales", "Referido", "Otro"];
const SOURCES = ["TV", "QR", "Fibeca", "pauta_digital", "web", "referido", "Evento", "otro"];

export default function QRCampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCampaignDialog, setShowCampaignDialog] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState(null);
  const [previewQR, setPreviewQR] = useState(null);

  const [campaignForm, setCampaignForm] = useState({
    name: "", channel: "TV/QR", source: "TV", product: "", initial_message: "Hola, vi esto en TV", description: "", active: true,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [camRes, prodRes] = await Promise.all([
        axios.get(`${API}/qr-campaigns`),
        axios.get(`${API}/products`),
      ]);
      setCampaigns(camRes.data);
      setProducts(prodRes.data);
    } catch { toast.error("Error al cargar datos"); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Campaign CRUD
  const openNewCampaign = () => {
    setEditingCampaign(null);
    setCampaignForm({ name: "", channel: "TV/QR", source: "TV", product: "", initial_message: "Hola, vi esto en TV", description: "", active: true });
    setShowCampaignDialog(true);
  };

  const openEditCampaign = (c) => {
    setEditingCampaign(c);
    setCampaignForm({ name: c.name, channel: c.channel, source: c.source, product: c.product || "", initial_message: c.initial_message, description: c.description || "", active: c.active });
    setShowCampaignDialog(true);
  };

  const saveCampaign = async () => {
    if (!campaignForm.name || !campaignForm.initial_message) {
      toast.error("Nombre y mensaje inicial son requeridos");
      return;
    }
    try {
      if (editingCampaign) {
        await axios.put(`${API}/qr-campaigns/${editingCampaign.id}`, campaignForm);
        toast.success("Campaña actualizada");
      } else {
        await axios.post(`${API}/qr-campaigns`, campaignForm);
        toast.success("Campaña creada");
      }
      setShowCampaignDialog(false);
      fetchData();
    } catch { toast.error("Error al guardar"); }
  };

  const deleteCampaign = async (id) => {
    if (!window.confirm("¿Eliminar esta campaña QR?")) return;
    try {
      await axios.delete(`${API}/qr-campaigns/${id}`);
      toast.success("Campaña eliminada");
      fetchData();
    } catch { toast.error("Error al eliminar"); }
  };

  const downloadQR = (id, name) => {
    const link = document.createElement("a");
    link.href = `${API}/qr-campaigns/${id}/qrcode`;
    link.download = `QR_${name.replace(/\s/g, "_")}.png`;
    link.click();
  };

  const copyLink = async (campaign) => {
    try {
      const res = await axios.get(`${API}/qr-campaigns/${campaign.id}/link`);
      await navigator.clipboard.writeText(res.data.link);
      toast.success("Enlace copiado al portapapeles");
    } catch { toast.error("Error al copiar enlace"); }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <QrCode className="h-7 w-7 text-emerald-500" />
            Campañas QR y Canales
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Genera códigos QR para cada campaña y rastrea el origen de tus leads</p>
        </div>
        <div className="flex gap-2">
          <Button data-testid="new-campaign-btn" onClick={openNewCampaign} className="bg-emerald-600 hover:bg-emerald-700 text-white">
            <Plus className="h-4 w-4 mr-1" /> Nueva Campaña QR
          </Button>
        </div>
      </div>

      {/* Campaign Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">Cargando...</div>
        ) : campaigns.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            No hay campañas QR creadas. Crea la primera.
          </div>
        ) : (
          campaigns.map((c) => (
            <Card key={c.id} data-testid={`campaign-card-${c.id}`} className={`bg-card border-border transition-all hover:shadow-lg ${!c.active ? "opacity-50" : ""}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base text-foreground truncate">{c.name}</CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium">{c.channel}</span>
                      {c.product && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">{c.product}</span>}
                      <span className={`text-xs px-2 py-0.5 rounded-full ${c.active ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                        {c.active ? "Activa" : "Inactiva"}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground" onClick={() => openEditCampaign(c)}>
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-red-400" onClick={() => deleteCampaign(c.id)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">Mensaje inicial:</p>
                  <p className="text-sm text-foreground font-medium">"{c.initial_message}"</p>
                </div>
                {c.description && <p className="text-xs text-muted-foreground">{c.description}</p>}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Target className="h-3.5 w-3.5" />{c.leads_count || 0} leads</span>
                    <span className="flex items-center gap-1"><QrCode className="h-3.5 w-3.5" />{c.scan_count || 0} escaneos</span>
                  </div>
                  <span className="text-xs text-muted-foreground">Fuente: {c.source}</span>
                </div>

                {/* QR Preview */}
                <div className="flex items-center justify-center py-2">
                  {previewQR === c.id ? (
                    <div className="text-center">
                      <img
                        src={`${API}/qr-campaigns/${c.id}/qrcode`}
                        alt={`QR ${c.name}`}
                        className="w-40 h-40 mx-auto rounded-lg border border-border"
                      />
                      <Button variant="ghost" size="sm" className="mt-2 text-xs text-muted-foreground" onClick={() => setPreviewQR(null)}>
                        <EyeOff className="h-3 w-3 mr-1" /> Ocultar
                      </Button>
                    </div>
                  ) : (
                    <Button variant="outline" size="sm" className="text-xs" onClick={() => setPreviewQR(c.id)}>
                      <Eye className="h-3 w-3 mr-1" /> Ver QR
                    </Button>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex gap-2">
                  <Button data-testid={`download-qr-${c.id}`} variant="outline" size="sm" className="flex-1 text-xs" onClick={() => downloadQR(c.id, c.name)}>
                    <Download className="h-3 w-3 mr-1" /> Descargar QR
                  </Button>
                  <Button data-testid={`copy-link-${c.id}`} variant="outline" size="sm" className="flex-1 text-xs" onClick={() => copyLink(c)}>
                    <Copy className="h-3 w-3 mr-1" /> Copiar Enlace
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Dialog open={showCampaignDialog} onOpenChange={setShowCampaignDialog}>
        <DialogContent className="bg-card border-border max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-foreground">{editingCampaign ? "Editar Campaña QR" : "Nueva Campaña QR"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-muted-foreground text-xs">Nombre *</Label>
              <Input data-testid="campaign-name" value={campaignForm.name} onChange={e => setCampaignForm(f => ({ ...f, name: e.target.value }))} placeholder="Ej: TV - Anuncio Bone Broth" className="bg-muted border-input" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-muted-foreground text-xs">Canal</Label>
                <Select value={campaignForm.channel} onValueChange={v => setCampaignForm(f => ({ ...f, channel: v }))}>
                  <SelectTrigger data-testid="campaign-channel" className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">
                    {CHANNELS.map(ch => <SelectItem key={ch} value={ch}>{ch}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Fuente</Label>
                <Select value={campaignForm.source} onValueChange={v => setCampaignForm(f => ({ ...f, source: v }))}>
                  <SelectTrigger data-testid="campaign-source" className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">
                    {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Producto (opcional)</Label>
              <Select value={campaignForm.product || "none"} onValueChange={v => setCampaignForm(f => ({ ...f, product: v === "none" ? "" : v }))}>
                <SelectTrigger data-testid="campaign-product" className="bg-muted border-input"><SelectValue placeholder="Sin producto" /></SelectTrigger>
                <SelectContent className="bg-card border-input">
                  <SelectItem value="none">Sin producto</SelectItem>
                  {products.map(p => <SelectItem key={p.id} value={p.name}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Mensaje inicial del QR *</Label>
              <Input data-testid="campaign-message" value={campaignForm.initial_message} onChange={e => setCampaignForm(f => ({ ...f, initial_message: e.target.value }))} placeholder="Hola, vi esto en TV" className="bg-muted border-input" />
              <p className="text-xs text-muted-foreground mt-1">Este mensaje se prellenará cuando el usuario escanee el QR</p>
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Descripción (opcional)</Label>
              <Input value={campaignForm.description} onChange={e => setCampaignForm(f => ({ ...f, description: e.target.value }))} placeholder="Descripción de la campaña..." className="bg-muted border-input" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={campaignForm.active} onChange={e => setCampaignForm(f => ({ ...f, active: e.target.checked }))} className="rounded" />
              <Label className="text-sm text-foreground">Campaña activa</Label>
            </div>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" className="flex-1" onClick={() => setShowCampaignDialog(false)}>Cancelar</Button>
              <Button data-testid="save-campaign-btn" className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white" onClick={saveCampaign}>
                {editingCampaign ? "Actualizar" : "Crear Campaña"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  );
}
