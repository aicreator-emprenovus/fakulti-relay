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
import { toast } from "sonner";
import { Plus, Edit, Trash2, Package, DollarSign } from "lucide-react";

export default function SettingsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editProduct, setEditProduct] = useState(null);
  const [form, setForm] = useState({ name: "", code: "", description: "", price: 0, original_price: 0, image_url: "", stock: 100, category: "general", active: true });

  const fetchProducts = () => {
    axios.get(`${API}/products`).then(res => { setProducts(res.data); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { fetchProducts(); }, []);

  const handleSave = async () => {
    try {
      if (editProduct) {
        await axios.put(`${API}/products/${editProduct.id}`, form);
        toast.success("Producto actualizado");
      } else {
        await axios.post(`${API}/products`, form);
        toast.success("Producto creado");
      }
      setShowForm(false);
      setEditProduct(null);
      setForm({ name: "", code: "", description: "", price: 0, original_price: 0, image_url: "", stock: 100, category: "general", active: true });
      fetchProducts();
    } catch { toast.error("Error al guardar producto"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar este producto?")) return;
    try {
      await axios.delete(`${API}/products/${id}`);
      toast.success("Producto eliminado");
      fetchProducts();
    } catch { toast.error("Error al eliminar"); }
  };

  const openEdit = (p) => {
    setEditProduct(p);
    setForm({ name: p.name, code: p.code || "", description: p.description || "", price: p.price, original_price: p.original_price || 0, image_url: p.image_url || "", stock: p.stock || 0, category: p.category || "general", active: p.active !== false });
    setShowForm(true);
  };

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando productos...</div>;

  return (
    <div data-testid="settings-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Productos</h1>
          <p className="text-sm text-muted-foreground">Administra el catalogo de productos Faculty</p>
        </div>
        <Button data-testid="add-product-btn" onClick={() => { setEditProduct(null); setForm({ name: "", code: "", description: "", price: 0, original_price: 0, image_url: "", stock: 100, category: "general", active: true }); setShowForm(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
          <Plus size={16} className="mr-1" /> Nuevo Producto
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map(p => (
          <Card key={p.id} className="bg-card border-border rounded-2xl overflow-hidden hover:border-primary/20 transition-colors" data-testid={`product-${p.id}`}>
            {p.image_url && (
              <div className="h-40 bg-muted flex items-center justify-center overflow-hidden">
                <img src={p.image_url} alt={p.name} className="h-full w-full object-contain p-4" />
              </div>
            )}
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-foreground font-semibold text-sm">{p.name}</h3>
                  <p className="text-xs text-muted-foreground">{p.code}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${p.active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>{p.active ? "Activo" : "Inactivo"}</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{p.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-primary">${p.price}</span>
                  {p.original_price > p.price && <span className="text-xs text-muted-foreground line-through">${p.original_price}</span>}
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground"><Package size={12} /> Stock: {p.stock}</div>
              </div>
              <div className="flex gap-1 mt-3">
                <Button variant="ghost" size="sm" className="flex-1 text-xs text-muted-foreground hover:text-primary" onClick={() => openEdit(p)} data-testid={`edit-product-${p.id}`}><Edit size={12} className="mr-1" /> Editar</Button>
                <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-red-400" onClick={() => handleDelete(p.id)} data-testid={`delete-product-${p.id}`}><Trash2 size={12} /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={showForm} onOpenChange={v => { setShowForm(v); if (!v) setEditProduct(null); }}>
        <DialogContent className="bg-card border-input text-foreground max-w-md" data-testid="product-form-dialog">
          <DialogHeader><DialogTitle>{editProduct ? "Editar Producto" : "Nuevo Producto"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="text-muted-foreground text-xs">Nombre *</Label><Input data-testid="product-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-muted-foreground text-xs">Codigo</Label><Input value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
              <div><Label className="text-muted-foreground text-xs">Categoria</Label><Input value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Descripcion</Label><Textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
            <div className="grid grid-cols-3 gap-3">
              <div><Label className="text-muted-foreground text-xs">Precio *</Label><Input type="number" step="0.01" value={form.price} onChange={e => setForm(f => ({ ...f, price: parseFloat(e.target.value) || 0 }))} className="bg-muted border-input text-foreground" /></div>
              <div><Label className="text-muted-foreground text-xs">Precio Orig.</Label><Input type="number" step="0.01" value={form.original_price} onChange={e => setForm(f => ({ ...f, original_price: parseFloat(e.target.value) || 0 }))} className="bg-muted border-input text-foreground" /></div>
              <div><Label className="text-muted-foreground text-xs">Stock</Label><Input type="number" value={form.stock} onChange={e => setForm(f => ({ ...f, stock: parseInt(e.target.value) || 0 }))} className="bg-muted border-input text-foreground" /></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">URL Imagen</Label><Input value={form.image_url} onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            <div className="flex items-center gap-2"><Label className="text-muted-foreground text-xs">Activo</Label><Switch checked={form.active} onCheckedChange={v => setForm(f => ({ ...f, active: v }))} /></div>
            <Button data-testid="save-product-btn" onClick={handleSave} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">{editProduct ? "Actualizar" : "Crear Producto"}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
