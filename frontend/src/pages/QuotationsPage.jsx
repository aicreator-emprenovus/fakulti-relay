import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { FileText, Download, Plus, Eye } from "lucide-react";

export default function QuotationsPage() {
  const [quotations, setQuotations] = useState([]);
  const [leads, setLeads] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ lead_id: "", items: [], notes: "" });

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/quotations`),
      axios.get(`${API}/leads?limit=200`),
      axios.get(`${API}/products`)
    ]).then(([q, l, p]) => {
      setQuotations(q.data);
      setLeads(l.data.leads);
      setProducts(p.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const addItem = () => {
    setForm(f => ({ ...f, items: [...f.items, { name: "", price: 0, quantity: 1 }] }));
  };

  const updateItem = (idx, field, value) => {
    setForm(f => ({ ...f, items: f.items.map((item, i) => i === idx ? { ...item, [field]: value } : item) }));
  };

  const addProductItem = (productId) => {
    const p = products.find(pr => pr.id === productId);
    if (p) setForm(f => ({ ...f, items: [...f.items, { name: p.name, price: p.price, quantity: 1 }] }));
  };

  const removeItem = (idx) => {
    setForm(f => ({ ...f, items: f.items.filter((_, i) => i !== idx) }));
  };

  const handleCreate = async () => {
    if (!form.lead_id || form.items.length === 0) return toast.error("Selecciona un lead y agrega productos");
    try {
      await axios.post(`${API}/quotations`, form);
      toast.success("Cotizacion creada");
      setShowCreate(false);
      setForm({ lead_id: "", items: [], notes: "" });
      const res = await axios.get(`${API}/quotations`);
      setQuotations(res.data);
    } catch (err) { toast.error(err.response?.data?.detail || "Error al crear cotizacion"); }
  };

  const downloadPdf = (id) => {
    window.open(`${API}/quotations/${id}/pdf`, "_blank");
  };

  const subtotal = form.items.reduce((acc, item) => acc + (item.price * item.quantity), 0);

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando cotizaciones...</div>;

  return (
    <div data-testid="quotations-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Cotizaciones</h1>
          <p className="text-sm text-muted-foreground">Genera y descarga cotizaciones en PDF</p>
        </div>
        <Button data-testid="create-quotation-btn" onClick={() => setShowCreate(true)} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
          <Plus size={16} className="mr-1" /> Nueva Cotizacion
        </Button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-muted/50 border-b border-border">
              <th className="text-left p-3 text-muted-foreground">ID</th>
              <th className="text-left p-3 text-muted-foreground">Cliente</th>
              <th className="text-left p-3 text-muted-foreground">Items</th>
              <th className="text-left p-3 text-muted-foreground">Total</th>
              <th className="text-left p-3 text-muted-foreground">Estado</th>
              <th className="text-left p-3 text-muted-foreground">Fecha</th>
              <th className="text-right p-3 text-muted-foreground">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {quotations.map(q => (
              <tr key={q.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`quotation-${q.id}`}>
                <td className="p-3 text-muted-foreground font-mono text-xs">{q.id.slice(0, 8)}</td>
                <td className="p-3 text-foreground">{q.lead_name}</td>
                <td className="p-3 text-muted-foreground">{q.items?.length || 0} productos</td>
                <td className="p-3 text-primary font-bold">${q.total?.toFixed(2)}</td>
                <td className="p-3"><Badge variant="outline" className="text-xs border-amber-500 text-amber-500">{q.status}</Badge></td>
                <td className="p-3 text-muted-foreground">{q.created_at?.slice(0, 10)}</td>
                <td className="p-3 text-right">
                  <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-primary" onClick={() => downloadPdf(q.id)} data-testid={`download-pdf-${q.id}`}>
                    <Download size={14} className="mr-1" /> PDF
                  </Button>
                </td>
              </tr>
            ))}
            {quotations.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-muted-foreground">No hay cotizaciones</td></tr>}
          </tbody>
        </table>
      </div>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-card border-input text-foreground max-w-lg max-h-[80vh] overflow-y-auto" data-testid="quotation-form-dialog">
          <DialogHeader><DialogTitle>Nueva Cotizacion</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-muted-foreground text-sm">Cliente (Lead)</Label>
              <Select value={form.lead_id} onValueChange={v => setForm(f => ({ ...f, lead_id: v }))}>
                <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona un lead" /></SelectTrigger>
                <SelectContent className="bg-muted border-input max-h-48">
                  {leads.map(l => <SelectItem key={l.id} value={l.id}>{l.name} - {l.whatsapp}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-muted-foreground text-sm">Agregar Producto</Label>
              <Select onValueChange={addProductItem}>
                <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona producto..." /></SelectTrigger>
                <SelectContent className="bg-muted border-input">
                  {products.map(p => <SelectItem key={p.id} value={p.id}>{p.name} - ${p.price}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {form.items.length > 0 && (
              <div className="space-y-2">
                {form.items.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-muted/50 rounded-lg">
                    <span className="text-sm text-foreground flex-1 truncate">{item.name}</span>
                    <Input type="number" value={item.quantity} onChange={e => updateItem(i, "quantity", parseInt(e.target.value) || 1)} className="w-16 h-7 text-xs bg-muted border-input text-foreground" />
                    <span className="text-sm text-primary">${(item.price * item.quantity).toFixed(2)}</span>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-red-400" onClick={() => removeItem(i)}>x</Button>
                  </div>
                ))}
                <div className="text-right text-sm">
                  <span className="text-muted-foreground">Subtotal: </span><span className="text-foreground font-bold">${subtotal.toFixed(2)}</span>
                  <span className="text-muted-foreground ml-4">IVA (12%): </span><span className="text-foreground">${(subtotal * 0.12).toFixed(2)}</span>
                  <span className="text-muted-foreground ml-4">Total: </span><span className="text-primary font-bold">${(subtotal * 1.12).toFixed(2)}</span>
                </div>
              </div>
            )}

            <div><Label className="text-muted-foreground text-xs">Notas</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
            <Button data-testid="save-quotation-btn" onClick={handleCreate} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">Generar Cotizacion</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
