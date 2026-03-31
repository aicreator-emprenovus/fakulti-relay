import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, Footer } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "sonner";
import { Lock, Mail, ArrowLeft } from "lucide-react";
import axios from "axios";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMessage, setForgotMessage] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Bienvenido al CRM Fakulti");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail) return toast.error("Ingresa tu email");
    setForgotLoading(true);
    setForgotMessage("");
    try {
      const res = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/forgot-password`, { email: forgotEmail });
      setForgotMessage(res.data.message);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al enviar solicitud");
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl" />
      </div>

      <Card className="w-full max-w-md relative z-10 bg-card border-border rounded-2xl" data-testid="login-card">
        <CardHeader className="text-center pb-2">
          <img src={LOGO_URL} alt="Fakulti" className="h-16 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-foreground font-heading">{showForgot ? "Recuperar Contraseña" : "Panel CRM"}</h1>
          <p className="text-sm text-muted-foreground">{showForgot ? "Ingresa tu email para solicitar el restablecimiento" : "La Ciencia de lo Natural"}</p>
        </CardHeader>
        <CardContent>
          {!showForgot ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label className="text-muted-foreground text-sm">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3.5 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    data-testid="login-email"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="tu-email@fakulti.com"
                    className="pl-10 bg-muted/50 border-input focus:border-primary/50 text-foreground h-12 rounded-lg"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-muted-foreground text-sm">Contrasena</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3.5 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    data-testid="login-password"
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Ingresa tu contraseña"
                    className="pl-10 bg-muted/50 border-input focus:border-primary/50 text-foreground h-12 rounded-lg"
                    required
                  />
                </div>
              </div>
              <Button
                data-testid="login-submit-btn"
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-primary-foreground font-bold rounded-full h-12 hover:bg-primary/90 transition-all hover:scale-[1.02] active:scale-95"
              >
                {loading ? "Ingresando..." : "Ingresar"}
              </Button>
              <button
                type="button"
                data-testid="forgot-password-link"
                onClick={() => { setShowForgot(true); setForgotMessage(""); }}
                className="w-full text-center text-xs text-primary hover:underline mt-2"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </form>
          ) : (
            <form onSubmit={handleForgotPassword} className="space-y-5">
              <div className="space-y-2">
                <Label className="text-muted-foreground text-sm">Email de tu cuenta</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3.5 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    data-testid="forgot-email"
                    type="email"
                    value={forgotEmail}
                    onChange={e => setForgotEmail(e.target.value)}
                    placeholder="tu-email@fakulti.com"
                    className="pl-10 bg-muted/50 border-input focus:border-primary/50 text-foreground h-12 rounded-lg"
                    required
                  />
                </div>
              </div>
              {forgotMessage && (
                <div data-testid="forgot-message" className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-600 text-center">
                  {forgotMessage}
                </div>
              )}
              <Button
                data-testid="forgot-submit-btn"
                type="submit"
                disabled={forgotLoading}
                className="w-full bg-primary text-primary-foreground font-bold rounded-full h-12 hover:bg-primary/90 transition-all"
              >
                {forgotLoading ? "Enviando..." : "Enviar Solicitud"}
              </Button>
              <button
                type="button"
                data-testid="back-to-login"
                onClick={() => setShowForgot(false)}
                className="w-full flex items-center justify-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft size={12} /> Volver al inicio de sesión
              </button>
            </form>
          )}
        </CardContent>
      </Card>
      <div className="absolute bottom-0 left-0 right-0 z-10">
        <Footer />
      </div>
    </div>
  );
}
