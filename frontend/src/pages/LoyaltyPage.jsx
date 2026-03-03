import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2, Save, Heart, Clock } from "lucide-react";

export default function LoyaltyPage() {
  const [sequences, setSequences] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ product_id: "", product_name: "", messages: [{ day: 1, content: "", active: true }], active: true });

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/loyalty/sequences`),
      axios.get(`${API}/products`)
    ]).then(([s, p]) => {
      setSequences(s.data);
      setProducts(p.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

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
      const res = await axios.get(`${API}/loyalty/sequences`);
      setSequences(res.data);
    } catch { toast.error("Error al crear secuencia"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Eliminar esta secuencia?")) return;
    try {
      await axios.delete(`${API}/loyalty/sequences/${id}`);
      toast.success("Secuencia eliminada");
      setSequences(prev => prev.filter(s => s.id !== id));
    } catch { toast.error("Error al eliminar"); }
  };

  if (loading) return <div className="text-zinc-500 text-center py-12">Cargando secuencias...</div>;

  return (
    <div data-testid="loyalty-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading">Fidelizacion</h1>
          <p className="text-sm text-zinc-500">Secuencias automaticas postventa (hasta 24 mensajes)</p>
        </div>
        <Button data-testid="add-sequence-btn" onClick={() => setShowAdd(true)} className="bg-lime-400 text-black font-bold rounded-full hover:bg-lime-300 shadow-[0_0_20px_rgba(163,230,53,0.3)]">
          <Plus size={16} className="mr-1" /> Nueva Secuencia
        </Button>
      </div>

      <div className="grid gap-4">
        {sequences.map(seq => (
          <Card key={seq.id} className="bg-[#0A0A0A] border-white/6 rounded-2xl" data-testid={`sequence-${seq.id}`}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center gap-3">
                <Heart size={18} className="text-lime-400" />
                <CardTitle className="text-lg text-white">{seq.product_name}</CardTitle>
                <span className={`text-xs px-2 py-0.5 rounded-full ${seq.active ? "bg-lime-400/10 text-lime-400" : "bg-zinc-800 text-zinc-500"}`}>{seq.active ? "Activa" : "Inactiva"}</span>
              </div>
              <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-red-400" onClick={() => handleDelete(seq.id)}>
                <Trash2 size={14} />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {seq.messages?.map((msg, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-zinc-900/30">
                    <div className="flex items-center gap-1 bg-zinc-800 rounded px-2 py-1 text-xs text-zinc-400 flex-shrink-0">
                      <Clock size={12} /> Dia {msg.day}
                    </div>
                    <p className="text-sm text-zinc-300 flex-1">{msg.content}</p>
                    <span className={`text-xs ${msg.active ? "text-lime-400" : "text-zinc-600"}`}>{msg.active ? "ON" : "OFF"}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
        {sequences.length === 0 && <div className="text-center py-12 text-zinc-600">No hay secuencias de fidelizacion configuradas</div>}
      </div>

      <Dialog open={showAdd} onOpenChange={setShowAdd}>
        <DialogContent className="bg-[#0A0A0A] border-zinc-800 text-white max-w-lg max-h-[80vh] overflow-y-auto" data-testid="loyalty-form-dialog">
          <DialogHeader><DialogTitle>Nueva Secuencia de Fidelizacion</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-zinc-400 text-sm">Producto</Label>
              <Select value={form.product_id} onValueChange={v => { const p = products.find(pr => pr.id === v); setForm(f => ({ ...f, product_id: v, product_name: p?.name || "" })); }}>
                <SelectTrigger className="bg-zinc-900 border-zinc-800 text-white"><SelectValue placeholder="Selecciona producto" /></SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">{products.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-zinc-400 text-sm">Mensajes ({form.messages.length}/24)</Label>
                {form.messages.length < 24 && <Button size="sm" variant="ghost" className="text-lime-400 text-xs" onClick={addMessage}><Plus size={14} className="mr-1" /> Agregar</Button>}
              </div>
              {form.messages.map((msg, i) => (
                <div key={i} className="p-3 rounded-lg bg-zinc-900/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-zinc-500">Dia</Label>
                    <Input type="number" value={msg.day} onChange={e => updateMessage(i, "day", parseInt(e.target.value) || 1)} className="w-16 h-7 text-xs bg-zinc-900 border-zinc-800 text-white" />
                    <div className="flex-1" />
                    <Switch checked={msg.active} onCheckedChange={v => updateMessage(i, "active", v)} />
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-zinc-500 hover:text-red-400" onClick={() => removeMessage(i)}><Trash2 size={12} /></Button>
                  </div>
                  <Textarea value={msg.content} onChange={e => updateMessage(i, "content", e.target.value)} placeholder="Contenido del mensaje..." className="bg-zinc-900 border-zinc-800 text-white text-sm" rows={2} />
                </div>
              ))}
            </div>

            <Button data-testid="save-sequence-btn" onClick={handleSave} className="w-full bg-lime-400 text-black font-bold rounded-full hover:bg-lime-300">
              <Save size={16} className="mr-1" /> Guardar Secuencia
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
