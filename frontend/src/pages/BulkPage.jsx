import React, { useState, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertCircle } from "lucide-react";

export default function BulkPage() {
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [downloadType, setDownloadType] = useState("all");
  const [downloadStage, setDownloadStage] = useState("");
  const [downloadProduct, setDownloadProduct] = useState("");
  const fileRef = useRef(null);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return toast.error("Selecciona un archivo Excel (.xlsx)");
    if (!file.name.endsWith(".xlsx")) return toast.error("Solo se permiten archivos .xlsx");

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/bulk/upload`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      setUploadResult(res.data);
      toast.success("Carga completada");
    } catch (err) { toast.error(err.response?.data?.detail || "Error al subir archivo"); }
    setUploading(false);
  };

  const handleDownload = () => {
    let url = `${API}/bulk/download?download_type=${downloadType}`;
    if (downloadType === "stage" && downloadStage) url += `&stage=${downloadStage}`;
    if (downloadType === "product" && downloadProduct) url += `&product=${downloadProduct}`;
    window.open(url, "_blank");
    toast.success("Descarga iniciada");
  };

  return (
    <div data-testid="bulk-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Carga y Descarga Masiva</h1>
        <p className="text-sm text-muted-foreground">Importa y exporta leads en formato Excel</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader>
            <CardTitle className="text-lg text-foreground flex items-center gap-2"><Upload size={18} className="text-primary" /> Carga Masiva</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Sube un archivo Excel (.xlsx) con los datos de tus leads. Campos mínimos: Nombre, WhatsApp, Ciudad, Producto, Fecha compra.</p>
            <div className="border-2 border-dashed border-input rounded-xl p-8 text-center hover:border-primary/30 transition-colors">
              <FileSpreadsheet size={40} className="text-muted-foreground mx-auto mb-3" />
              <input ref={fileRef} type="file" accept=".xlsx" className="hidden" id="upload-file" data-testid="upload-file-input" />
              <label htmlFor="upload-file" className="cursor-pointer">
                <p className="text-sm text-muted-foreground">Arrastra tu archivo aquí o <span className="text-primary underline">selecciona</span></p>
                <p className="text-xs text-muted-foreground mt-1">Solo archivos .xlsx</p>
              </label>
            </div>
            <Button data-testid="upload-btn" onClick={handleUpload} disabled={uploading} className="w-full bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90">
              {uploading ? "Subiendo..." : "Cargar Archivo"}
            </Button>

            {uploadResult && (
              <div className="p-4 rounded-xl bg-muted/50 space-y-2" data-testid="upload-result">
                <p className="text-sm font-semibold text-foreground">Resultado de la carga:</p>
                <div className="flex items-center gap-2 text-sm"><CheckCircle size={14} className="text-primary" /><span className="text-foreground/80">{uploadResult.created} leads creados</span></div>
                <div className="flex items-center gap-2 text-sm"><CheckCircle size={14} className="text-blue-400" /><span className="text-foreground/80">{uploadResult.updated} leads actualizados</span></div>
                {uploadResult.errors > 0 && <div className="flex items-center gap-2 text-sm"><AlertCircle size={14} className="text-red-400" /><span className="text-foreground/80">{uploadResult.errors} errores</span></div>}
                <p className="text-xs text-muted-foreground">Total procesados: {uploadResult.total_processed}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl">
          <CardHeader>
            <CardTitle className="text-lg text-foreground flex items-center gap-2"><Download size={18} className="text-primary" /> Descarga Excel</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Descarga tu base de datos de leads filtrada por diferentes criterios.</p>
            <div>
              <Label className="text-muted-foreground text-sm">Tipo de Descarga</Label>
              <Select value={downloadType} onValueChange={setDownloadType}>
                <SelectTrigger data-testid="download-type" className="bg-muted border-input text-foreground"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-muted border-input">
                  <SelectItem value="all">Base total</SelectItem>
                  <SelectItem value="stage">Por etapa de embudo</SelectItem>
                  <SelectItem value="product">Por producto</SelectItem>
                  <SelectItem value="fibeca">Leads Fibeca</SelectItem>
                  <SelectItem value="game">Leads juego</SelectItem>
                  <SelectItem value="recompra">Leads recompra</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {downloadType === "stage" && (
              <div>
                <Label className="text-muted-foreground text-sm">Etapa</Label>
                <Select value={downloadStage} onValueChange={setDownloadStage}>
                  <SelectTrigger className="bg-muted border-input text-foreground"><SelectValue placeholder="Selecciona etapa" /></SelectTrigger>
                  <SelectContent className="bg-muted border-input">
                    <SelectItem value="nuevo">Nuevo</SelectItem>
                    <SelectItem value="interesado">Interesado</SelectItem>
                    <SelectItem value="en_negociacion">En Negociación</SelectItem>
                    <SelectItem value="cliente_nuevo">Cliente Nuevo</SelectItem>
                    <SelectItem value="cliente_activo">Cliente Activo</SelectItem>
                    <SelectItem value="perdido">Perdido</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {downloadType === "product" && (
              <div>
                <Label className="text-muted-foreground text-sm">Producto</Label>
                <Input data-testid="download-product" value={downloadProduct} onChange={e => setDownloadProduct(e.target.value)} placeholder="Nombre del producto..." className="bg-muted border-input text-foreground" />
              </div>
            )}

            <Button data-testid="download-btn" onClick={handleDownload} className="w-full bg-muted text-foreground font-bold rounded-full hover:bg-muted/80 border border-input">
              <Download size={16} className="mr-1" /> Descargar Excel
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
