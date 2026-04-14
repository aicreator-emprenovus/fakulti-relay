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
import { Plus, Edit, Trash2, Package, Bot, ChevronDown, ChevronUp, Save, Download, Upload, XCircle } from "lucide-react";
import * as XLSX from "xlsx";

export default function SettingsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editProduct, setEditProduct] = useState(null);
  const [showBotConfig, setShowBotConfig] = useState(null);
  const [botForm, setBotForm] = useState({ personality: "", key_benefits: "", usage_info: "", restrictions: "", faqs: "", sales_flow: "" });
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

  const openBotConfig = async (p) => {
    if (showBotConfig === p.id) {
      setShowBotConfig(null);
      return;
    }
    try {
      const res = await axios.get(`${API}/products/${p.id}/bot-config`);
      setBotForm(res.data);
      setShowBotConfig(p.id);
    } catch { toast.error("Error al cargar config del bot"); }
  };

  const saveBotConfig = async (productId) => {
    try {
      await axios.put(`${API}/products/${productId}/bot-config`, botForm);
      toast.success("Configuración del bot actualizada");
      fetchProducts();
    } catch { toast.error("Error al guardar config del bot"); }
  };

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando productos...</div>;

  const handleExport = async () => {
    try {
      const res = await axios.get(`${API}/products/export`);
      const data = res.data.map(p => ({
        Nombre: p.name, Codigo: p.code || "", Descripcion: p.description || "",
        Precio: p.price, "Precio Original": p.original_price || "", Stock: p.stock || 0,
        Categoria: p.category || "", Activo: p.active ? "Si" : "No", "URL Imagen": p.image_url || "",
        "Bot - Personalidad": p.bot_config?.personality || "",
        "Bot - Beneficios": p.bot_config?.key_benefits || "",
        "Bot - Uso": p.bot_config?.usage_info || "",
        "Bot - Restricciones": p.bot_config?.restrictions || "",
        "Bot - FAQs": p.bot_config?.faqs || "",
        "Bot - Flujo de Ventas": p.bot_config?.sales_flow || "",
      }));
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "Productos");
      XLSX.writeFile(wb, "productos_fakulti.xlsx");
      toast.success(`${data.length} productos exportados`);
    } catch { toast.error("Error al exportar"); }
  };

  const handleImport = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".xlsx,.xls";
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const buf = await file.arrayBuffer();
        const wb = XLSX.read(buf, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(ws);
        const products_to_import = rows.map(r => ({
          name: r["Nombre"] || r["name"] || "",
          code: r["Codigo"] || r["code"] || "",
          description: r["Descripcion"] || r["description"] || "",
          price: parseFloat(r["Precio"] || r["price"] || 0),
          original_price: parseFloat(r["Precio Original"] || r["original_price"] || 0) || null,
          stock: parseInt(r["Stock"] || r["stock"] || 100),
          category: r["Categoria"] || r["category"] || "general",
          active: (r["Activo"] || r["active"] || "Si").toString().toLowerCase() !== "no",
          image_url: r["URL Imagen"] || r["image_url"] || "",
          personality: r["Bot - Personalidad"] || r["personality"] || "",
          key_benefits: r["Bot - Beneficios"] || r["key_benefits"] || "",
          usage_info: r["Bot - Uso"] || r["usage_info"] || "",
          restrictions: r["Bot - Restricciones"] || r["restrictions"] || "",
          faqs: r["Bot - FAQs"] || r["faqs"] || "",
          sales_flow: r["Bot - Flujo de Ventas"] || r["sales_flow"] || "",
        })).filter(p => p.name);
        if (!products_to_import.length) { toast.error("No se encontraron productos validos"); return; }
        const res = await axios.post(`${API}/products/import`, { products: products_to_import });
        toast.success(res.data.message);
        fetchProducts();
      } catch { toast.error("Error al importar archivo"); }
    };
    input.click();
  };

  const handleDeleteAll = async () => {
    if (!window.confirm(`¿Eliminar TODOS los ${products.length} productos? Esta accion no se puede deshacer.`)) return;
    if (!window.confirm("¿Estas seguro? Se borraran todos los productos y sus configuraciones de bot.")) return;
    try {
      const res = await axios.delete(`${API}/products/all`);
      toast.success(res.data.message);
      fetchProducts();
    } catch { toast.error("Error al eliminar productos"); }
  };

  return (
    <div data-testid="settings-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Productos y Bots</h1>
          <p className="text-sm text-muted-foreground">Administra el catálogo de productos y configura los bots especializados por producto</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button data-testid="export-products-btn" variant="outline" onClick={handleExport} className="rounded-full text-xs border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10">
            <Download size={14} className="mr-1" /> Exportar
          </Button>
          <Button data-testid="import-products-btn" variant="outline" onClick={handleImport} className="rounded-full text-xs border-blue-500/30 text-blue-600 hover:bg-blue-500/10">
            <Upload size={14} className="mr-1" /> Importar
          </Button>
          <Button data-testid="delete-all-products-btn" variant="outline" onClick={handleDeleteAll} className="rounded-full text-xs border-red-500/30 text-red-600 hover:bg-red-500/10">
            <XCircle size={14} className="mr-1" /> Borrar Todo
          </Button>
          <Button data-testid="add-product-btn" onClick={() => { setEditProduct(null); setForm({ name: "", code: "", description: "", price: 0, original_price: 0, image_url: "", stock: 100, category: "general", active: true }); setShowForm(true); }} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 shadow-sm">
            <Plus size={16} className="mr-1" /> Nuevo Producto
          </Button>
        </div>
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
                <Button variant="ghost" size="sm" className={`flex-1 text-xs ${showBotConfig === p.id ? "text-violet-500" : "text-muted-foreground hover:text-violet-500"}`} onClick={() => openBotConfig(p)} data-testid={`bot-config-${p.id}`}>
                  <Bot size={12} className="mr-1" /> Bot {showBotConfig === p.id ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                </Button>
                <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-red-400" onClick={() => handleDelete(p.id)} data-testid={`delete-product-${p.id}`}><Trash2 size={12} /></Button>
              </div>

              {/* Bot Config Inline Editor */}
              {showBotConfig === p.id && (
                <div className="mt-3 pt-3 border-t border-border space-y-2.5 animate-fade-in-up">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Bot size={14} className="text-violet-500" />
                    <span className="text-xs font-semibold text-violet-500">Configuración del Bot Especializado</span>
                  </div>
                  <div>
                    <Label className="text-muted-foreground text-[10px]">Personalidad</Label>
                    <Textarea value={botForm.personality} onChange={e => setBotForm(f => ({ ...f, personality: e.target.value }))} className="bg-muted border-input text-foreground text-xs" rows={2} placeholder="Experto en nutricion, amigable..." />
                  </div>
                  <div>
                    <Label className="text-muted-foreground text-[10px]">Beneficios clave</Label>
                    <Textarea value={botForm.key_benefits} onChange={e => setBotForm(f => ({ ...f, key_benefits: e.target.value }))} className="bg-muted border-input text-foreground text-xs" rows={2} placeholder="Mejora digestión, soporte articular..." />
                  </div>
                  <div>
                    <Label className="text-muted-foreground text-[10px]">Cómo se usa</Label>
                    <Textarea value={botForm.usage_info} onChange={e => setBotForm(f => ({ ...f, usage_info: e.target.value }))} className="bg-muted border-input text-foreground text-xs" rows={2} placeholder="Un sachet al dia..." />
                  </div>
                  <div>
                    <Label className="text-muted-foreground text-[10px]">Restricciones</Label>
                    <Textarea value={botForm.restrictions} onChange={e => setBotForm(f => ({ ...f, restrictions: e.target.value }))} className="bg-muted border-input text-foreground text-xs" rows={2} placeholder="No prometer curas..." />
                  </div>
                  <div>
                    <Label className="text-muted-foreground text-[10px]">Preguntas frecuentes</Label>
                    <Textarea value={botForm.faqs} onChange={e => setBotForm(f => ({ ...f, faqs: e.target.value }))} className="bg-muted border-input text-foreground text-xs" rows={2} placeholder="Se toma un sachet al dia..." />
                  </div>
                  <div>
                    <Label className="text-[10px] font-semibold text-amber-500">Flujo de Ventas Avanzado (opcional)</Label>
                    <p className="text-[9px] text-muted-foreground mb-1">Script detallado de ventas: apertura, respuestas por intencion, objeciones, cierre. Si se llena, el bot seguira este flujo.</p>
                    <Textarea value={botForm.sales_flow || ""} onChange={e => setBotForm(f => ({ ...f, sales_flow: e.target.value }))} className="bg-muted border-input text-foreground text-xs font-mono" rows={6} placeholder="FLUJO DE VENTAS - PRODUCTO...&#10;1. MENSAJE DE APERTURA&#10;2. RESPUESTA SEGUN INTENCION&#10;..." />
                    {botForm.sales_flow && <p className="text-[9px] text-amber-500 mt-0.5">{botForm.sales_flow.length} caracteres configurados</p>}
                  </div>
                  <Button data-testid={`save-bot-config-${p.id}`} size="sm" className="w-full bg-violet-600 hover:bg-violet-700 text-white text-xs" onClick={() => saveBotConfig(p.id)}>
                    <Save size={12} className="mr-1" /> Guardar Config del Bot
                  </Button>
                </div>
              )}
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
              <div><Label className="text-muted-foreground text-xs">Código</Label><Input value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
              <div><Label className="text-muted-foreground text-xs">Categoría</Label><Input value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} className="bg-muted border-input text-foreground" /></div>
            </div>
            <div><Label className="text-muted-foreground text-xs">Descripción</Label><Textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="bg-muted border-input text-foreground" rows={2} /></div>
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
