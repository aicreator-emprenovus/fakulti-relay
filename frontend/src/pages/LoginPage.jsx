import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
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
      toast.success("Bienvenido al CRM Faculty");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-lime-400/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-lime-400/3 rounded-full blur-3xl" />
      </div>

      <Card className="w-full max-w-md relative z-10 bg-[#0A0A0A] border-white/10 rounded-2xl" data-testid="login-card">
        <CardHeader className="text-center pb-2">
          <img src={LOGO_URL} alt="Faculty" className="h-16 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white font-heading">Panel CRM</h1>
          <p className="text-sm text-zinc-500">La Ciencia de lo Natural</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label className="text-zinc-400 text-sm">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 h-4 w-4 text-zinc-600" />
                <Input
                  data-testid="login-email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="admin@faculty.com"
                  className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-lime-400/50 text-white h-12 rounded-lg"
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-400 text-sm">Contrasena</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 h-4 w-4 text-zinc-600" />
                <Input
                  data-testid="login-password"
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Ingresa tu contrasena"
                  className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-lime-400/50 text-white h-12 rounded-lg"
                  required
                />
              </div>
            </div>
            <Button
              data-testid="login-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full bg-lime-400 text-black font-bold rounded-full h-12 hover:bg-lime-300 transition-all hover:scale-[1.02] active:scale-95 shadow-[0_0_20px_rgba(163,230,53,0.3)]"
            >
              {loading ? "Ingresando..." : "Ingresar"}
            </Button>
            <p className="text-center text-xs text-zinc-600 mt-4">
              Demo: admin@faculty.com / admin123
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
