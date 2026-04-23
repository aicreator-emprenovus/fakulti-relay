import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { UserCheck, Plus, Pencil, Trash2, Phone, Users, MessageCircle, Key, RefreshCw, Copy, Eye, EyeOff } from "lucide-react";
import { PasswordInput } from "@/components/PasswordInput";
import { PasswordStrengthBar, PasswordGeneratorButton, CopyPasswordButton } from "@/components/ForceChangePassword";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const STATUS_CONFIG = {
  disponible: { label: "Disponible", color: "bg-green-500/20 text-green-400" },
  ocupado: { label: "Ocupado", color: "bg-amber-500/20 text-amber-400" },
  ausente: { label: "Ausente", color: "bg-red-500/20 text-red-400" },
  desconectado: { label: "Desconectado", color: "bg-muted text-muted-foreground" },
};

export default function AdvisorsPage() {
  const [advisors, setAdvisors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", password: "", whatsapp: "", status: "disponible", specialization: "" });
  const [resetTarget, setResetTarget] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetRequests, setResetRequests] = useState([]);
  const [generatedInfo, setGeneratedInfo] = useState(null);
  const [showGenPw, setShowGenPw] = useState(false);

  const fetchAdvisors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/advisors`);
      setAdvisors(res.data);
    } catch { toast.error("Error al cargar asesores"); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAdvisors(); }, [fetchAdvisors]);

  useEffect(() => {
    axios.get(`${API}/auth/password-reset-requests`).then(r => setResetRequests(r.data)).catch(() => {});
  }, []);

  const generateProvisionalForAdvisor = async (advisorId) => {
    try {
      const res = await axios.post(`${API}/auth/generate-provisional-password`, { user_id: advisorId });
      setGeneratedInfo(res.data);
      toast.success(`Contraseña provisional generada para ${res.data.user_name}`);
      // If there was a pending request, approve it
      const pendingReq = resetRequests.find(r => r.user_id === advisorId && r.status === "pending");
      if (pendingReq) {
        await axios.put(`${API}/auth/reset-password-approve/${pendingReq.id}`);
        axios.get(`${API}/auth/password-reset-requests`).then(r => setResetRequests(r.data));
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al generar contraseña");
    }
  };

  const resetAdvisorPassword = async (advisorId) => {
    if (!newPassword || newPassword.length < 8) return toast.error("La contraseña debe tener al menos 8 caracteres");
    const pwCheck = /[A-Z]/.test(newPassword) && /[a-z]/.test(newPassword) && /[0-9]/.test(newPassword) && /[!@#$%^&*()_+\-=[\]{};:'",.<>?/\\|`~]/.test(newPassword);
    if (!pwCheck) return toast.error("La contraseña debe tener mayúscula, minúscula, número y carácter especial");
    try {
      await axios.post(`${API}/auth/reset-password-direct`, { user_id: advisorId, new_password: newPassword });
      toast.success("Contraseña provisional establecida. El asesor deberá cambiarla al iniciar sesión.");
      setResetTarget(null); setNewPassword("");
    } catch (e) { toast.error(e.response?.data?.detail || "Error al restablecer"); }
  };

  const resolveRequest = async (reqId) => {
    if (!newPassword || newPassword.length < 8) return toast.error("La contraseña debe tener al menos 8 caracteres");
    try {
      await axios.post(`${API}/auth/reset-password/${reqId}`, { new_password: newPassword });
      toast.success("Contraseña provisional establecida. Deberá cambiarla al iniciar sesión.");
      setNewPassword("");
      setResetRequests(prev => prev.filter(r => r.id !== reqId));
    } catch (e) { toast.error(e.response?.data?.detail || "Error"); }
  };

  const openNew = () => {
    setEditing(null);
    setForm({ name: "", email: "", password: "", whatsapp: "", status: "disponible", specialization: "" });
    setShowDialog(true);
  };

  const openEdit = (a) => {
    setEditing(a);
    setForm({ name: a.name, email: a.email, password: "", whatsapp: a.whatsapp || "", status: a.status || "disponible", specialization: a.specialization || "" });
    setShowDialog(true);
  };

  const save = async () => {
    if (!form.name || !form.email) {
      toast.error("Nombre y email son requeridos");
      return;
    }
    try {
      if (editing) {
        await axios.put(`${API}/advisors/${editing.id}/status`, {
          name: form.name, whatsapp: form.whatsapp, status: form.status,
          specialization: form.specialization,
          ...(form.password ? { password: form.password } : {}),
        });
        toast.success("Asesor actualizado");
      } else {
        if (!form.password) { toast.error("Contraseña requerida para nuevo asesor"); return; }
        await axios.post(`${API}/advisors`, form);
        toast.success("Asesor creado");
      }
      setShowDialog(false);
      fetchAdvisors();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Error al guardar");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("¿Eliminar este asesor? Sus leads serán desasignados.")) return;
    try {
      await axios.delete(`${API}/advisors/${id}`);
      toast.success("Asesor eliminado");
      fetchAdvisors();
    } catch { toast.error("Error al eliminar"); }
  };

  const updateStatus = async (id, status) => {
    try {
      await axios.put(`${API}/advisors/${id}/status`, { status });
      fetchAdvisors();
    } catch { toast.error("Error al actualizar estado"); }
  };

  return (
    <div data-testid="advisors-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <UserCheck className="h-7 w-7 text-amber-500" />
            Asesores
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Gestiona el equipo de asesores humanos y sus asignaciones</p>
        </div>
        <Button data-testid="new-advisor-btn" onClick={openNew} className="bg-amber-600 hover:bg-amber-700 text-white">
          <Plus className="h-4 w-4 mr-1" /> Nuevo Asesor
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{advisors.length}</p>
          <p className="text-xs text-muted-foreground">Total Asesores</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-green-500">{advisors.filter(a => a.status === "disponible").length}</p>
          <p className="text-xs text-muted-foreground">Disponibles</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-amber-500">{advisors.filter(a => a.status === "ocupado").length}</p>
          <p className="text-xs text-muted-foreground">Ocupados</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-blue-500">{advisors.reduce((sum, a) => sum + (a.leads_count || 0), 0)}</p>
          <p className="text-xs text-muted-foreground">Leads Asignados</p>
        </CardContent></Card>
      </div>

      {/* Reset Requests */}
      {resetRequests.filter(r => r.user_role === "advisor" && r.status === "pending").length > 0 && (
        <Card className="bg-card border-l-4 border-l-amber-500 rounded-2xl">
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold text-amber-600 mb-3 flex items-center gap-1.5"><Key size={14} /> Solicitudes de Restablecimiento de Asesores</h3>
            {resetRequests.filter(r => r.user_role === "advisor" && r.status === "pending").map(req => (
              <div key={req.id} className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-3 mb-2">
                <p className="text-sm font-medium text-foreground">{req.user_name} ({req.user_email})</p>
                <p className="text-xs text-muted-foreground">Solicitado: {new Date(req.created_at).toLocaleString("es-EC")}</p>
                <div className="flex gap-2">
                  <Button data-testid={`gen-prov-advisor-${req.id}`} size="sm" onClick={() => generateProvisionalForAdvisor(req.user_id)} className="bg-amber-500 text-white text-xs h-8 rounded-full hover:bg-amber-600 gap-1">
                    <Key size={12} /> Generar Contraseña Provisional
                  </Button>
                </div>
                {generatedInfo && generatedInfo.user_email === req.user_email && (
                  <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-2">
                    <p className="text-xs text-emerald-400 font-medium">Contraseña provisional generada:</p>
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono bg-muted px-3 py-1.5 rounded-lg flex-1 text-foreground select-all">
                        {showGenPw ? generatedInfo.provisional_password : "************"}
                      </code>
                      <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => setShowGenPw(!showGenPw)}>
                        {showGenPw ? <EyeOff size={12} /> : <Eye size={12} />}
                      </Button>
                      <Button variant="outline" size="sm" className="h-7 px-2 gap-1" onClick={() => { navigator.clipboard.writeText(generatedInfo.provisional_password); toast.success("Copiada"); }}>
                        <Copy size={10} /> Copiar
                      </Button>
                    </div>
                    <p className="text-[10px] text-amber-400">Comparte esta contraseña con {req.user_name}. Al iniciar sesión deberá cambiarla.</p>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Advisor Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">Cargando...</div>
        ) : advisors.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">No hay asesores registrados. Crea el primero.</div>
        ) : (
          advisors.map(a => {
            const st = STATUS_CONFIG[a.status] || STATUS_CONFIG.desconectado;
            return (
              <Card key={a.id} data-testid={`advisor-card-${a.id}`} className="bg-card border-border hover:shadow-lg transition-all">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-500 font-bold text-lg">
                        {a.name[0]}
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground">{a.name}</h3>
                        <p className="text-xs text-muted-foreground">{a.email}</p>
                      </div>
                    </div>
                    <Select value={a.status} onValueChange={v => updateStatus(a.id, v)}>
                      <SelectTrigger className={`w-auto h-6 text-[10px] px-2 border-0 ${st.color}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-input">
                        {Object.entries(STATUS_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    {a.whatsapp && (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Phone size={12} /> {a.whatsapp}
                      </div>
                    )}
                    {a.specialization && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 inline-block">
                        {a.specialization}
                      </span>
                    )}
                    <div className="flex items-center gap-4 pt-2 border-t border-border">
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Users size={12} /> {a.leads_count || 0} leads
                      </div>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MessageCircle size={12} /> {a.active_chats || 0} activos
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-1 mt-3">
                    <Button variant="ghost" size="sm" className="flex-1 text-xs text-muted-foreground hover:text-foreground" onClick={() => openEdit(a)}>
                      <Pencil size={12} className="mr-1" /> Editar
                    </Button>
                    <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-amber-400" onClick={() => setResetTarget(resetTarget === a.id ? null : a.id)}>
                      <Key size={12} className="mr-1" /> Reset
                    </Button>
                    <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-red-400" onClick={() => remove(a.id)}>
                      <Trash2 size={12} />
                    </Button>
                  </div>
                  {resetTarget === a.id && (
                    <div className="mt-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-3">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label className="text-[10px] text-muted-foreground font-medium">Nueva Contraseña Provisional</Label>
                          <PasswordGeneratorButton onGenerate={pw => setNewPassword(pw)} />
                        </div>
                        <PasswordInput value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Min 8 chars, mayúscula, minúscula, número, especial" className="bg-muted/50 border-input text-foreground h-8 text-xs" />
                        {newPassword && <PasswordStrengthBar password={newPassword} />}
                      </div>
                      <div className="flex gap-2">
                        <Button data-testid={`confirm-reset-advisor-${a.id}`} size="sm" onClick={() => resetAdvisorPassword(a.id)} className="bg-amber-500 text-white text-xs h-8 rounded-full hover:bg-amber-600">Establecer Provisional</Button>
                        <Button size="sm" variant="outline" className="text-xs h-8 rounded-full gap-1" onClick={() => generateProvisionalForAdvisor(a.id)}>
                          <Key size={10} /> Auto-generar
                        </Button>
                      </div>
                      {generatedInfo && generatedInfo.user_email === a.email && (
                        <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                          <p className="text-[10px] text-emerald-400 font-medium">Contraseña generada:</p>
                          <div className="flex items-center gap-2">
                            <code className="text-xs font-mono bg-muted px-2 py-1 rounded flex-1 text-foreground select-all">
                              {showGenPw ? generatedInfo.provisional_password : "************"}
                            </code>
                            <Button variant="ghost" size="sm" className="h-6 px-1.5" onClick={() => setShowGenPw(!showGenPw)}>
                              {showGenPw ? <EyeOff size={10} /> : <Eye size={10} />}
                            </Button>
                            <Button variant="ghost" size="sm" className="h-6 px-1.5" onClick={() => { navigator.clipboard.writeText(generatedInfo.provisional_password); toast.success("Copiada"); }}>
                              <Copy size={10} />
                            </Button>
                          </div>
                          <p className="text-[10px] text-amber-400">Al iniciar sesión deberá cambiarla.</p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle className="text-foreground">{editing ? "Editar Asesor" : "Nuevo Asesor"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-muted-foreground text-xs">Nombre completo *</Label>
              <Input data-testid="advisor-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input" placeholder="Carlos Mendez" />
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Email *</Label>
              <Input data-testid="advisor-email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="bg-muted border-input" placeholder="carlos@fakulti.com" disabled={!!editing} />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <Label className="text-muted-foreground text-xs">{editing ? "Nueva contraseña (vacío = no cambiar)" : "Contraseña inicial *"}</Label>
                {!editing && <PasswordGeneratorButton onGenerate={pw => setForm(f => ({ ...f, password: pw }))} />}
              </div>
              <PasswordInput data-testid="advisor-password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} className="bg-muted border-input" placeholder="Min 8 chars" />
              {form.password && <div className="mt-1"><PasswordStrengthBar password={form.password} /></div>}
              {!editing && <p className="text-[10px] text-muted-foreground mt-1">El asesor deberá cambiar esta contraseña la primera vez que inicie sesión.</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-muted-foreground text-xs">WhatsApp</Label>
                <Input value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} className="bg-muted border-input" placeholder="0991234567" />
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Estado</Label>
                <Select value={form.status} onValueChange={v => setForm(f => ({ ...f, status: v }))}>
                  <SelectTrigger className="bg-muted border-input"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-input">
                    {Object.entries(STATUS_CONFIG).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Especialización</Label>
              <Input value={form.specialization} onChange={e => setForm(f => ({ ...f, specialization: e.target.value }))} className="bg-muted border-input" placeholder="Bone Broth, Gomitas..." />
            </div>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" className="flex-1" onClick={() => setShowDialog(false)}>Cancelar</Button>
              <Button data-testid="save-advisor-btn" className="flex-1 bg-amber-600 hover:bg-amber-700 text-white" onClick={save}>
                {editing ? "Actualizar" : "Crear Asesor"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
