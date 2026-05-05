import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { ShieldCheck, Plus, Pencil, Trash2, Phone, Key, Copy, Eye, EyeOff, Lock } from "lucide-react";
import { PasswordInput } from "@/components/PasswordInput";
import { PasswordStrengthBar, PasswordGeneratorButton } from "@/components/ForceChangePassword";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const STATUS_CONFIG = {
  disponible: { label: "Disponible", color: "bg-green-500/20 text-green-400" },
  ocupado: { label: "Ocupado", color: "bg-amber-500/20 text-amber-400" },
  ausente: { label: "Ausente", color: "bg-red-500/20 text-red-400" },
  desconectado: { label: "Desconectado", color: "bg-muted text-muted-foreground" },
};

export default function AdminsPage() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", password: "", whatsapp: "", status: "disponible", specialization: "" });
  const [resetTarget, setResetTarget] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [generatedInfo, setGeneratedInfo] = useState(null);
  const [showGenPw, setShowGenPw] = useState(false);

  const fetchAdmins = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admins`);
      setAdmins(res.data);
    } catch { toast.error("Error al cargar administradores"); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAdmins(); }, [fetchAdmins]);

  const generateProvisionalForAdmin = async (adminId) => {
    try {
      const res = await axios.post(`${API}/auth/generate-provisional-password`, { user_id: adminId });
      setGeneratedInfo(res.data);
      toast.success(`Contraseña provisional generada para ${res.data.user_name}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error al generar contraseña");
    }
  };

  const resetAdminPassword = async (adminId) => {
    if (!newPassword || newPassword.length < 8) return toast.error("La contraseña debe tener al menos 8 caracteres");
    const ok = /[A-Z]/.test(newPassword) && /[a-z]/.test(newPassword) && /[0-9]/.test(newPassword) && /[!@#$%^&*()_+\-=[\]{};:'",.<>?/\\|`~]/.test(newPassword);
    if (!ok) return toast.error("Mayúscula, minúscula, número y carácter especial requeridos");
    try {
      await axios.post(`${API}/auth/reset-password-direct`, { user_id: adminId, new_password: newPassword });
      toast.success("Contraseña provisional establecida. Deberá cambiarla al iniciar sesión.");
      setResetTarget(null); setNewPassword("");
    } catch (e) { toast.error(e.response?.data?.detail || "Error al restablecer"); }
  };

  const openNew = () => {
    setEditing(null);
    setForm({ name: "", email: "", password: "", whatsapp: "", status: "disponible", specialization: "" });
    setShowDialog(true);
  };

  const openEdit = (a) => {
    if (a.is_protected) return toast.error("El usuario principal no se puede modificar");
    setEditing(a);
    setForm({ name: a.name, email: a.email, password: "", whatsapp: a.whatsapp || "", status: a.status || "disponible", specialization: a.specialization || "" });
    setShowDialog(true);
  };

  const save = async () => {
    if (!form.name || !form.email) return toast.error("Nombre y email son requeridos");
    try {
      if (editing) {
        await axios.put(`${API}/admins/${editing.id}`, {
          name: form.name, whatsapp: form.whatsapp, status: form.status,
          specialization: form.specialization,
        });
        toast.success("Administrador actualizado");
      } else {
        if (!form.password) { toast.error("Contraseña requerida para nuevo administrador"); return; }
        await axios.post(`${API}/admins`, form);
        toast.success("Administrador creado");
      }
      setShowDialog(false);
      fetchAdmins();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Error al guardar");
    }
  };

  const remove = async (a) => {
    if (a.is_protected) return toast.error("El usuario principal no se puede eliminar");
    if (!window.confirm(`¿Eliminar al administrador "${a.name}"? Esta acción no se puede deshacer.`)) return;
    try {
      await axios.delete(`${API}/admins/${a.id}`);
      toast.success("Administrador eliminado");
      fetchAdmins();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error al eliminar"); }
  };

  return (
    <div data-testid="admins-page" className="space-y-6 animate-fade-in-up">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <ShieldCheck className="h-7 w-7 text-primary" />
            Administradores
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Gestiona las cuentas con permisos de administrador del CRM</p>
        </div>
        <Button data-testid="new-admin-btn" onClick={openNew} className="bg-primary hover:bg-primary/90 text-primary-foreground">
          <Plus className="h-4 w-4 mr-1" /> Nuevo Administrador
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{admins.length}</p>
          <p className="text-xs text-muted-foreground">Total Administradores</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-primary">{admins.filter(a => !a.is_protected).length}</p>
          <p className="text-xs text-muted-foreground">Editables</p>
        </CardContent></Card>
        <Card className="bg-card border-border"><CardContent className="p-3 text-center">
          <p className="text-2xl font-bold text-amber-500">1</p>
          <p className="text-xs text-muted-foreground">Protegido</p>
        </CardContent></Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">Cargando...</div>
        ) : admins.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">No hay administradores registrados.</div>
        ) : (
          admins.map(a => {
            const st = STATUS_CONFIG[a.status] || STATUS_CONFIG.desconectado;
            return (
              <Card key={a.id} data-testid={`admin-card-${a.id}`} className={`bg-card border-border hover:shadow-lg transition-all ${a.is_protected ? "ring-1 ring-amber-500/30" : ""}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-lg">
                        {a.name?.[0] || "A"}
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                          {a.name}
                          {a.is_protected && <Lock size={11} className="text-amber-500" data-testid="protected-icon" />}
                        </h3>
                        <p className="text-xs text-muted-foreground">{a.email}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded ${st.color}`}>{st.label}</span>
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
                    {a.is_protected && (
                      <div className="text-[10px] text-amber-500 bg-amber-500/5 border border-amber-500/20 rounded px-2 py-1.5">
                        Usuario principal — protegido contra eliminación y cambio de contraseña.
                      </div>
                    )}
                  </div>

                  <div className="flex gap-1 mt-3">
                    <Button data-testid={`edit-admin-${a.id}`} variant="ghost" size="sm" disabled={a.is_protected} className="flex-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-40" onClick={() => openEdit(a)}>
                      <Pencil size={12} className="mr-1" /> Editar
                    </Button>
                    <Button data-testid={`reset-admin-${a.id}`} variant="ghost" size="sm" disabled={a.is_protected} className="text-xs text-muted-foreground hover:text-amber-400 disabled:opacity-40" onClick={() => setResetTarget(resetTarget === a.id ? null : a.id)}>
                      <Key size={12} className="mr-1" /> Reset
                    </Button>
                    <Button data-testid={`delete-admin-${a.id}`} variant="ghost" size="sm" disabled={a.is_protected} className="text-xs text-muted-foreground hover:text-red-400 disabled:opacity-40" onClick={() => remove(a)}>
                      <Trash2 size={12} />
                    </Button>
                  </div>
                  {resetTarget === a.id && !a.is_protected && (
                    <div className="mt-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-3">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label className="text-[10px] text-muted-foreground font-medium">Nueva Contraseña Provisional</Label>
                          <PasswordGeneratorButton onGenerate={pw => setNewPassword(pw)} />
                        </div>
                        <PasswordInput value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Min 8 chars, mayús/minús/número/especial" className="bg-muted/50 border-input text-foreground h-8 text-xs" />
                        {newPassword && <PasswordStrengthBar password={newPassword} />}
                      </div>
                      <div className="flex gap-2">
                        <Button data-testid={`confirm-reset-admin-${a.id}`} size="sm" onClick={() => resetAdminPassword(a.id)} className="bg-amber-500 text-white text-xs h-8 rounded-full hover:bg-amber-600">Establecer</Button>
                        <Button size="sm" variant="outline" className="text-xs h-8 rounded-full gap-1" onClick={() => generateProvisionalForAdmin(a.id)}>
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

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle className="text-foreground">{editing ? "Editar Administrador" : "Nuevo Administrador"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-muted-foreground text-xs">Nombre completo *</Label>
              <Input data-testid="admin-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input" placeholder="Juan Pérez" />
            </div>
            <div>
              <Label className="text-muted-foreground text-xs">Email *</Label>
              <Input data-testid="admin-email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="bg-muted border-input" placeholder="juan@fakulti.com" disabled={!!editing} />
            </div>
            {!editing && (
              <div>
                <div className="flex items-center justify-between">
                  <Label className="text-muted-foreground text-xs">Contraseña inicial *</Label>
                  <PasswordGeneratorButton onGenerate={pw => setForm(f => ({ ...f, password: pw }))} />
                </div>
                <PasswordInput data-testid="admin-password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} className="bg-muted border-input" placeholder="Min 8 chars" />
                {form.password && <div className="mt-1"><PasswordStrengthBar password={form.password} /></div>}
                <p className="text-[10px] text-muted-foreground mt-1">El administrador deberá cambiar esta contraseña la primera vez que inicie sesión.</p>
              </div>
            )}
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
              <Label className="text-muted-foreground text-xs">Especialización / Área</Label>
              <Input value={form.specialization} onChange={e => setForm(f => ({ ...f, specialization: e.target.value }))} className="bg-muted border-input" placeholder="Marketing, Operaciones..." />
            </div>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" className="flex-1" onClick={() => setShowDialog(false)}>Cancelar</Button>
              <Button data-testid="save-admin-btn" className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground" onClick={save}>
                {editing ? "Actualizar" : "Crear Administrador"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
