import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ShieldAlert, Key, Clock, CheckCircle2, Copy, AlertTriangle, Eye, EyeOff } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function DevAlertsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingFor, setGeneratingFor] = useState(null);
  const [generatedPasswords, setGeneratedPasswords] = useState({});
  const [showPasswords, setShowPasswords] = useState({});

  const fetchRequests = async () => {
    try {
      const res = await axios.get(`${API}/auth/password-reset-requests`);
      setRequests(res.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchRequests(); const iv = setInterval(fetchRequests, 10000); return () => clearInterval(iv); }, []);

  const generateProvisional = async (req) => {
    setGeneratingFor(req.id);
    try {
      const res = await axios.post(`${API}/auth/generate-provisional-password`, { user_id: req.user_id });
      setGeneratedPasswords(prev => ({ ...prev, [req.id]: res.data }));
      // Mark request as resolved
      await axios.post(`${API}/auth/approve-reset/${req.id}`);
      toast.success(`Contraseña provisional generada para ${res.data.user_name}`);
      fetchRequests();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al generar contraseña");
    }
    setGeneratingFor(null);
  };

  const copyPassword = (pw) => {
    navigator.clipboard.writeText(pw);
    toast.success("Contraseña copiada al portapapeles. Compártela de forma segura.");
  };

  const pending = requests.filter(r => r.status === "pending");
  const resolved = requests.filter(r => r.status !== "pending");

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando solicitudes...</div>;

  return (
    <div data-testid="dev-alerts-page" className="space-y-6 animate-fade-in-up max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <ShieldAlert size={24} className="text-amber-500" /> Panel de Alertas
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Gestiona solicitudes de restablecimiento de contraseña. Genera contraseñas provisionales seguras.
        </p>
      </div>

      {/* Pending Requests */}
      <Card className="bg-card border-border rounded-2xl">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-500" />
            Solicitudes Pendientes
            {pending.length > 0 && <Badge className="bg-amber-500/20 text-amber-400 border-0 ml-2">{pending.length}</Badge>}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {pending.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No hay solicitudes pendientes</p>
          ) : pending.map(req => (
            <div key={req.id} data-testid={`reset-req-${req.id}`} className="p-4 rounded-xl bg-muted/30 border border-amber-500/20 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-foreground">{req.user_name || req.user_email}</p>
                  <p className="text-xs text-muted-foreground">{req.user_email}</p>
                  <Badge className="mt-1 text-[10px] bg-muted text-muted-foreground border-0">{req.user_role === "admin" ? "Administrador" : "Asesor"}</Badge>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground text-[10px]">
                  <Clock size={10} />
                  {new Date(req.created_at).toLocaleString("es-EC")}
                </div>
              </div>

              {generatedPasswords[req.id] ? (
                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-2">
                  <p className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                    <CheckCircle2 size={12} /> Contraseña provisional generada
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 relative">
                      <code className="text-sm font-mono bg-muted px-3 py-2 rounded-lg block text-foreground select-all">
                        {showPasswords[req.id] ? generatedPasswords[req.id].provisional_password : "************"}
                      </code>
                    </div>
                    <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => setShowPasswords(prev => ({ ...prev, [req.id]: !prev[req.id] }))}>
                      {showPasswords[req.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 px-2 gap-1" onClick={() => copyPassword(generatedPasswords[req.id].provisional_password)}>
                      <Copy size={12} /> Copiar
                    </Button>
                  </div>
                  <p className="text-[10px] text-amber-400">
                    Comparte esta contraseña de forma segura con {req.user_name}. Al iniciar sesión, el sistema le exigirá cambiarla.
                  </p>
                </div>
              ) : (
                <Button
                  data-testid={`generate-provisional-${req.id}`}
                  onClick={() => generateProvisional(req)}
                  disabled={generatingFor === req.id}
                  className="bg-amber-500 text-white hover:bg-amber-600 rounded-full text-sm h-9 gap-1.5"
                >
                  <Key size={14} />
                  {generatingFor === req.id ? "Generando..." : "Generar Contraseña Provisional"}
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Resolved History */}
      {resolved.length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-500" />
              Historial Resuelto
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {resolved.slice(0, 10).map(req => (
              <div key={req.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                <div>
                  <p className="text-sm text-foreground">{req.user_name || req.user_email}</p>
                  <p className="text-[10px] text-muted-foreground">{req.user_email} - {req.user_role === "admin" ? "Admin" : "Asesor"}</p>
                </div>
                <div className="flex items-center gap-1.5 text-emerald-500 text-[10px]">
                  <CheckCircle2 size={10} />
                  {req.resolved_at ? new Date(req.resolved_at).toLocaleString("es-EC") : "Resuelto"}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
