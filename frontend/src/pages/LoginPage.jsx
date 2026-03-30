import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, Footer } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "sonner";
import { Lock, Mail } from "lucide-react";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
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

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl" />
      </div>

      <Card className="w-full max-w-md relative z-10 bg-card border-border rounded-2xl" data-testid="login-card">
        <CardHeader className="text-center pb-2">
          <img src={LOGO_URL} alt="Fakulti" className="h-16 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-foreground font-heading">Panel CRM</h1>
          <p className="text-sm text-muted-foreground">La Ciencia de lo Natural</p>
        </CardHeader>
        <CardContent>
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
                  placeholder="admin@fakulti.com"
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
            <p className="text-center text-xs text-muted-foreground mt-4">
              Demo: admin@fakulti.com / admin123
            </p>
          </form>
        </CardContent>
      </Card>
      <div className="absolute bottom-0 left-0 right-0 z-10">
        <Footer />
      </div>
    </div>
  );
}
