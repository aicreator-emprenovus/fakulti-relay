import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

function Confetti() {
  const colors = ["#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#EF4444", "#10B981"];
  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {Array.from({ length: 40 }).map((_, i) => (
        <div key={i} className="confetti-piece" style={{ left: `${Math.random() * 100}%`, backgroundColor: colors[i % colors.length], animationDelay: `${Math.random() * 2}s`, animationDuration: `${2 + Math.random() * 2}s`, borderRadius: Math.random() > 0.5 ? "50%" : "0", width: `${6 + Math.random() * 8}px`, height: `${6 + Math.random() * 8}px` }} />
      ))}
    </div>
  );
}

function RouletteGame({ config, onPlay }) {
  const canvasRef = useRef(null);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const rotationRef = useRef(0);

  const prizes = config?.prizes || [];
  const segAngle = 360 / (prizes.length || 1);

  useEffect(() => {
    drawWheel(0);
  }, [config]);

  const drawWheel = useCallback((rotation) => {
    const canvas = canvasRef.current;
    if (!canvas || prizes.length === 0) return;
    const ctx = canvas.getContext("2d");
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const r = Math.min(cx, cy) - 10;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((rotation * Math.PI) / 180);

    prizes.forEach((prize, i) => {
      const start = (i * segAngle * Math.PI) / 180;
      const end = ((i + 1) * segAngle * Math.PI) / 180;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, r, start, end);
      ctx.fillStyle = prize.color || "#A3E635";
      ctx.fill();
      ctx.strokeStyle = "#050505";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.save();
      ctx.rotate(start + (end - start) / 2);
      ctx.translate(r * 0.6, 0);
      ctx.rotate(Math.PI / 2);
      ctx.fillStyle = "#000";
      ctx.font = "bold 11px Manrope";
      ctx.textAlign = "center";
      const words = prize.name.split(" ");
      words.forEach((w, wi) => ctx.fillText(w, 0, wi * 13 - (words.length - 1) * 6));
      ctx.restore();
    });

    ctx.restore();

    // Draw pointer
    ctx.beginPath();
    ctx.moveTo(cx + r + 5, cy);
    ctx.lineTo(cx + r + 25, cy - 12);
    ctx.lineTo(cx + r + 25, cy + 12);
    ctx.fillStyle = "#A3E635";
    ctx.fill();

    // Center circle
    ctx.beginPath();
    ctx.arc(cx, cy, 25, 0, Math.PI * 2);
    ctx.fillStyle = "#050505";
    ctx.fill();
    ctx.strokeStyle = "#A3E635";
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = "#A3E635";
    ctx.font = "bold 10px Manrope";
    ctx.textAlign = "center";
    ctx.fillText("GIRAR", cx, cy + 4);
  }, [prizes, segAngle]);

  const spin = async () => {
    setSpinning(true);
    setResult(null);
    try {
      const res = await onPlay();
      const prizeIndex = res.prize_index;
      const targetAngle = 360 - (prizeIndex * segAngle + segAngle / 2);
      const totalRotation = 360 * 5 + targetAngle;

      let startTime = null;
      const duration = 4000;

      const animate = (time) => {
        if (!startTime) startTime = time;
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4);
        const currentRotation = eased * totalRotation;
        rotationRef.current = currentRotation;
        drawWheel(currentRotation);
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setSpinning(false);
          setResult(res);
        }
      };
      requestAnimationFrame(animate);
    } catch (err) {
      setSpinning(false);
      toast.error(err.response?.data?.detail || "Error al jugar");
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {result && <Confetti />}
      <canvas ref={canvasRef} width={340} height={340} className="max-w-full" data-testid="roulette-canvas" />
      {!result ? (
        <Button data-testid="spin-btn" onClick={spin} disabled={spinning} className="bg-primary text-primary-foreground font-bold rounded-full px-10 py-3 text-lg hover:bg-primary/90 shadow-sm disabled:opacity-50">
          {spinning ? "Girando..." : "GIRAR LA RULETA"}
        </Button>
      ) : (
        <div className="text-center animate-fade-in-up" data-testid="prize-result">
          <p className="text-2xl font-bold text-primary mb-2">{result.prize}</p>
          <p className="text-muted-foreground">{result.message}</p>
          {result.coupon && <p className="mt-2 text-lg font-bold text-foreground bg-muted px-4 py-2 rounded-lg inline-block">Cupon: {result.coupon}</p>}
        </div>
      )}
    </div>
  );
}

function MysteryBoxGame({ config, onPlay }) {
  const [phase, setPhase] = useState("idle");
  const [result, setResult] = useState(null);

  const play = async () => {
    setPhase("shaking");
    try {
      const res = await onPlay();
      setTimeout(() => setPhase("opening"), 1500);
      setTimeout(() => { setPhase("revealed"); setResult(res); }, 2300);
    } catch (err) {
      setPhase("idle");
      toast.error(err.response?.data?.detail || "Error al jugar");
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {result && <Confetti />}
      <div className="relative w-48 h-48 cursor-pointer" onClick={phase === "idle" ? play : undefined} data-testid="mystery-box">
        {phase !== "revealed" ? (
          <div className={`w-full h-full rounded-2xl flex items-center justify-center text-7xl transition-all ${phase === "shaking" ? "shake-animation" : ""} ${phase === "opening" ? "box-open" : ""}`}
            style={{ background: "linear-gradient(135deg, #A3E635 0%, #3F6212 100%)", boxShadow: "0 0 40px rgba(163,230,53,0.3)" }}>
            🎁
          </div>
        ) : (
          <div className="prize-reveal w-full h-full rounded-2xl flex items-center justify-center bg-muted border-2 border-primary" data-testid="prize-result">
            <div className="text-center p-4">
              <p className="text-4xl mb-2">🎉</p>
              <p className="text-xl font-bold text-primary">{result?.prize}</p>
            </div>
          </div>
        )}
      </div>
      {phase === "idle" && <p className="text-muted-foreground text-sm">Toca la caja para abrirla</p>}
      {result && (
        <div className="text-center animate-fade-in-up">
          <p className="text-muted-foreground">{result.message}</p>
          {result.coupon && <p className="mt-2 text-lg font-bold text-foreground bg-muted px-4 py-2 rounded-lg inline-block">Cupon: {result.coupon}</p>}
        </div>
      )}
    </div>
  );
}

function LuckyButtonGame({ config, onPlay }) {
  const [pressing, setPressing] = useState(false);
  const [result, setResult] = useState(null);

  const play = async () => {
    setPressing(true);
    try {
      const res = await onPlay();
      setTimeout(() => { setPressing(false); setResult(res); }, 2000);
    } catch (err) {
      setPressing(false);
      toast.error(err.response?.data?.detail || "Error al jugar");
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {result && <Confetti />}
      {!result ? (
        <button data-testid="lucky-btn" onClick={play} disabled={pressing}
          className={`w-40 h-40 rounded-full flex items-center justify-center text-5xl font-bold transition-all ${pressing ? "scale-90 bg-primary/80" : "bg-primary hover:scale-110 lucky-pulse"}`}
          style={{ color: "#000" }}>
          {pressing ? (
            <div className="animate-spin text-3xl">⚡</div>
          ) : "⚡"}
        </button>
      ) : (
        <div className="w-40 h-40 rounded-full flex items-center justify-center bg-muted border-2 border-primary animate-fade-in-up" data-testid="prize-result">
          <div className="text-center">
            <p className="text-3xl mb-1">🎉</p>
            <p className="text-sm font-bold text-primary">{result.prize}</p>
          </div>
        </div>
      )}
      {!result && <p className="text-muted-foreground text-sm">{pressing ? "Buscando tu premio..." : "Presiona el boton de la suerte"}</p>}
      {result && (
        <div className="text-center animate-fade-in-up">
          <p className="text-muted-foreground">{result.message}</p>
          {result.coupon && <p className="mt-2 text-lg font-bold text-foreground bg-muted px-4 py-2 rounded-lg inline-block">Cupon: {result.coupon}</p>}
        </div>
      )}
    </div>
  );
}

export default function GamePublicPage() {
  const { gameType } = useParams();
  const [config, setConfig] = useState(null);
  const [form, setForm] = useState({ name: "", whatsapp: "", city: "" });
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/games/public/${gameType}`).then(res => {
      setConfig(res.data);
      setLoading(false);
    }).catch(() => { setError("Juego no disponible"); setLoading(false); });
  }, [gameType]);

  const handleRegister = (e) => {
    e.preventDefault();
    if (!form.name || !form.whatsapp) return toast.error("Nombre y WhatsApp son requeridos");
    setRegistered(true);
  };

  const handlePlay = async () => {
    const res = await axios.post(`${API}/games/play`, { game_type: gameType, ...form });
    return res.data;
  };

  if (loading) return <div className="min-h-screen bg-background flex items-center justify-center text-muted-foreground">Cargando juego...</div>;
  if (error) return <div className="min-h-screen bg-background flex items-center justify-center text-red-400">{error}</div>;

  const GameComponent = { roulette: RouletteGame, mystery_box: MysteryBoxGame, lucky_button: LuckyButtonGame }[gameType];

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4" data-testid="game-public-page">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
      </div>
      <div className="relative z-10 w-full max-w-md mx-auto">
        <div className="text-center mb-6">
          <img src={LOGO_URL} alt="Faculty" className="h-12 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-foreground font-heading">{config?.name}</h1>
          <p className="text-sm text-muted-foreground">Juega y gana premios exclusivos</p>
        </div>

        {!registered ? (
          <Card className="bg-card border-border rounded-2xl" data-testid="game-register-form">
            <CardContent className="p-6">
              <form onSubmit={handleRegister} className="space-y-4">
                <div><Label className="text-muted-foreground text-sm">Tu Nombre *</Label><Input data-testid="game-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-muted border-input text-foreground h-12" placeholder="Ingresa tu nombre" required /></div>
                <div><Label className="text-muted-foreground text-sm">WhatsApp *</Label><Input data-testid="game-whatsapp" value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} className="bg-muted border-input text-foreground h-12" placeholder="+593..." required /></div>
                <div><Label className="text-muted-foreground text-sm">Ciudad</Label><Input value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} className="bg-muted border-input text-foreground h-12" placeholder="Tu ciudad" /></div>
                <Button data-testid="game-register-btn" type="submit" className="w-full bg-primary text-primary-foreground font-bold rounded-full h-12 hover:bg-primary/90 shadow-sm">
                  JUGAR AHORA
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          GameComponent && <GameComponent config={config} onPlay={handlePlay} />
        )}
      </div>
    </div>
  );
}
