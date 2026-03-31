import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Key, Bell, CheckCircle, Clock } from "lucide-react";

export default function DevAlertsPage() {
  const [resetRequests, setResetRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(() => {
    setLoading(true);
    axios.get(`${API}/auth/password-reset-requests`).then(r => { setResetRequests(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const approveRequest = async (reqId, userName) => {
    try {
      await axios.post(`${API}/auth/approve-reset/${reqId}`);
      toast.success(`Solicitud aprobada. ${userName} podrá crear su nueva contraseña desde el login.`);
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || "Error al aprobar"); }
  };

  return (
    <div data-testid="dev-alerts-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Panel de Alertas</h1>
        <p className="text-sm text-muted-foreground">Solicitudes y notificaciones del sistema</p>
      </div>

      <Card className="bg-card border-border rounded-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Key size={18} className="text-violet-500" /> Gestión de Accesos</CardTitle>
          <p className="text-xs text-muted-foreground">Cuando un administrador olvida su contraseña, su solicitud aparece aquí. Al aprobarla, podrá crear una nueva contraseña desde el login.</p>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <p className="text-center text-sm text-muted-foreground py-6">Cargando...</p>
          ) : resetRequests.length > 0 ? resetRequests.map(req => (
            <div key={req.id} data-testid={`alert-request-${req.id}`} className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                    <Clock size={16} className="text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{req.user_name}</p>
                    <p className="text-xs text-muted-foreground">{req.user_email} | {new Date(req.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <Button data-testid={`approve-reset-${req.id}`} onClick={() => approveRequest(req.id, req.user_name)} className="bg-emerald-600 text-white font-bold rounded-full hover:bg-emerald-700 text-xs">
                  <CheckCircle size={13} className="mr-1.5" /> Aprobar
                </Button>
              </div>
            </div>
          )) : (
            <div className="text-center py-10">
              <Bell size={32} className="mx-auto text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">Sin alertas pendientes</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
