import React, { useState, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Shield, Check, X, RefreshCw, Copy } from "lucide-react";
import { PasswordInput } from "@/components/PasswordInput";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

function checkStrength(pw) {
  const checks = {
    length: pw.length >= 8,
    upper: /[A-Z]/.test(pw),
    lower: /[a-z]/.test(pw),
    digit: /[0-9]/.test(pw),
    special: /[!@#$%^&*()_+\-=[\]{};:'",.<>?/\\|`~]/.test(pw),
  };
  const passed = Object.values(checks).filter(Boolean).length;
  return { checks, passed, total: 5, valid: passed === 5 };
}

function generateSecurePassword() {
  const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lower = "abcdefghjkmnpqrstuvwxyz";
  const digits = "23456789";
  const special = "!@#$%&*";
  const all = upper + lower + digits + special;
  let pw = "";
  pw += upper[Math.floor(Math.random() * upper.length)];
  pw += lower[Math.floor(Math.random() * lower.length)];
  pw += digits[Math.floor(Math.random() * digits.length)];
  pw += special[Math.floor(Math.random() * special.length)];
  for (let i = 0; i < 8; i++) pw += all[Math.floor(Math.random() * all.length)];
  return pw.split("").sort(() => Math.random() - 0.5).join("");
}

export function PasswordStrengthBar({ password }) {
  const { checks, passed, total } = checkStrength(password);
  const pct = (passed / total) * 100;
  const color = pct <= 40 ? "bg-red-500" : pct <= 80 ? "bg-amber-500" : "bg-emerald-500";
  const label = pct <= 40 ? "Débil" : pct <= 80 ? "Media" : "Fuerte";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
          <div className={`h-full ${color} transition-all duration-300 rounded-full`} style={{ width: `${pct}%` }} />
        </div>
        <span className={`text-[10px] font-medium ${pct <= 40 ? "text-red-500" : pct <= 80 ? "text-amber-500" : "text-emerald-500"}`}>{label}</span>
      </div>
      <div className="grid grid-cols-2 gap-1">
        {[
          { key: "length", label: "8+ caracteres" },
          { key: "upper", label: "Mayúscula (A-Z)" },
          { key: "lower", label: "Minúscula (a-z)" },
          { key: "digit", label: "Número (0-9)" },
          { key: "special", label: "Especial (!@#$)" },
        ].map(r => (
          <div key={r.key} className="flex items-center gap-1">
            {checks[r.key] ? <Check size={10} className="text-emerald-500" /> : <X size={10} className="text-muted-foreground/40" />}
            <span className={`text-[10px] ${checks[r.key] ? "text-emerald-500" : "text-muted-foreground/60"}`}>{r.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PasswordGeneratorButton({ onGenerate }) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      data-testid="generate-password-btn"
      onClick={() => {
        const pw = generateSecurePassword();
        onGenerate(pw);
        toast.success("Contraseña segura generada");
      }}
      className="text-[10px] h-6 px-2 gap-1 text-primary hover:text-primary"
    >
      <RefreshCw size={10} /> Generar segura
    </Button>
  );
}

export function CopyPasswordButton({ password }) {
  if (!password) return null;
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      data-testid="copy-password-btn"
      onClick={() => { navigator.clipboard.writeText(password); toast.success("Contraseña copiada al portapapeles"); }}
      className="text-[10px] h-6 px-2 gap-1 text-muted-foreground hover:text-foreground"
    >
      <Copy size={10} /> Copiar
    </Button>
  );
}

export default function ForceChangePasswordModal({ user, onComplete }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const strength = checkStrength(newPassword);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!strength.valid) return toast.error("La contraseña no cumple los requisitos de seguridad");
    if (newPassword !== confirmPassword) return toast.error("Las contraseñas no coinciden");
    setLoading(true);
    try {
      await axios.post(`${API}/auth/change-password`, { new_password: newPassword });
      toast.success("Contraseña actualizada exitosamente");
      onComplete();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al cambiar contraseña");
    } finally {
      setLoading(false);
    }
  }, [newPassword, confirmPassword, strength.valid, onComplete]);

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 flex items-center justify-center p-4">
      <Card data-testid="force-change-password-modal" className="w-full max-w-md bg-card border-border rounded-2xl shadow-2xl">
        <CardHeader className="text-center pb-2">
          <img src={LOGO_URL} alt="Fakulti" className="h-12 mx-auto mb-3" />
          <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center mx-auto mb-3">
            <Shield size={24} className="text-amber-500" />
          </div>
          <h2 className="text-xl font-bold text-foreground">Cambio de Contraseña Obligatorio</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Hola <strong>{user?.name}</strong>, debes establecer una contraseña segura para continuar.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-muted-foreground text-sm">Nueva Contraseña</Label>
                <div className="flex gap-1">
                  <PasswordGeneratorButton onGenerate={(pw) => { setNewPassword(pw); setConfirmPassword(pw); }} />
                  <CopyPasswordButton password={newPassword} />
                </div>
              </div>
              <PasswordInput
                data-testid="force-new-password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Crea una contraseña segura"
                className="bg-muted/50 border-input text-foreground h-11 rounded-lg"
                required
              />
            </div>
            {newPassword && <PasswordStrengthBar password={newPassword} />}
            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-sm">Confirmar Contraseña</Label>
              <PasswordInput
                data-testid="force-confirm-password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Repite tu contraseña"
                className="bg-muted/50 border-input text-foreground h-11 rounded-lg"
                required
              />
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-[10px] text-red-500">Las contraseñas no coinciden</p>
              )}
            </div>
            <Button
              data-testid="force-change-submit"
              type="submit"
              disabled={loading || !strength.valid || newPassword !== confirmPassword}
              className="w-full bg-primary text-primary-foreground font-bold rounded-full h-11 hover:bg-primary/90 transition-all disabled:opacity-50"
            >
              {loading ? "Guardando..." : "Establecer Contraseña"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
