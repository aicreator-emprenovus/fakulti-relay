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
    const r = Math.min(cx, cy) - 50;

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

    // Draw pointer - big red triangle
    ctx.beginPath();
    ctx.moveTo(cx + r - 5, cy);
    ctx.lineTo(cx + r + 45, cy - 26);
    ctx.lineTo(cx + r + 45, cy + 26);
    ctx.closePath();
    ctx.fillStyle = "#DC2626";
    ctx.fill();
    ctx.strokeStyle = "#7F1D1D";
    ctx.lineWidth = 3;
    ctx.stroke();
    // White dot on pointer
    ctx.beginPath();
    ctx.arc(cx + r + 30, cy, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
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
      <canvas ref={canvasRef} width={400} height={360} className="max-w-full" data-testid="roulette-canvas" />
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

function SlotMachineGame({ config, onPlay }) {
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [reels, setReels] = useState([0, 0, 0]);
  const [displayReels, setDisplayReels] = useState([0, 0, 0]);
  const SYMBOLS = ["🦴", "💊", "🌿", "⭐", "💎", "🧬"];
  const intervalRefs = useRef([]);

  const spin = async () => {
    setSpinning(true);
    setResult(null);

    // Start all 3 reels spinning
    for (let r = 0; r < 3; r++) {
      intervalRefs.current[r] = setInterval(() => {
        setDisplayReels(prev => {
          const copy = [...prev];
          copy[r] = (copy[r] + 1) % SYMBOLS.length;
          return copy;
        });
      }, 80 + r * 20);
    }

    try {
      const res = await onPlay();
      // Determine final symbols based on prize index
      const prizeIdx = res.prize_index;
      let finalReels;
      if (prizeIdx <= 1) {
        // Big prizes: 3 matching
        const sym = prizeIdx;
        finalReels = [sym, sym, sym];
      } else if (prizeIdx <= 3) {
        // Medium: 2 matching
        finalReels = [prizeIdx, prizeIdx, (prizeIdx + 2) % SYMBOLS.length];
      } else {
        // Small: all different
        finalReels = [0, 2, 4];
      }

      // Stop reels with staggered timing
      for (let r = 0; r < 3; r++) {
        await new Promise(resolve => setTimeout(resolve, 600 + r * 500));
        clearInterval(intervalRefs.current[r]);
        setDisplayReels(prev => {
          const copy = [...prev];
          copy[r] = finalReels[r];
          return copy;
        });
      }

      setReels(finalReels);
      setSpinning(false);
      setResult(res);
    } catch (err) {
      intervalRefs.current.forEach(clearInterval);
      setSpinning(false);
      toast.error(err.response?.data?.detail || "Error al jugar");
    }
  };

  useEffect(() => {
    return () => intervalRefs.current.forEach(clearInterval);
  }, []);

  return (
    <div className="flex flex-col items-center gap-6">
      {result && <Confetti />}
      <div className="bg-gradient-to-b from-amber-900/80 to-amber-950/90 rounded-2xl p-6 border-2 border-amber-600/50 shadow-lg" data-testid="slot-machine">
        <div className="text-center mb-3">
          <p className="text-amber-400 font-bold text-lg font-heading tracking-wider">TRAGAMONEDAS</p>
        </div>
        <div className="flex gap-2 bg-black/60 rounded-xl p-4">
          {[0, 1, 2].map(r => (
            <div key={r} className="w-20 h-24 bg-white/10 rounded-lg flex items-center justify-center border border-amber-600/30 overflow-hidden">
              <span className={`text-5xl transition-transform ${spinning ? "animate-bounce" : ""}`} style={{ animationDelay: `${r * 100}ms` }}>
                {SYMBOLS[displayReels[r]]}
              </span>
            </div>
          ))}
        </div>
        <div className="flex justify-center mt-1">
          <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-amber-400 to-transparent" />
        </div>
      </div>

      {!result ? (
        <Button data-testid="slot-spin-btn" onClick={spin} disabled={spinning}
          className="bg-gradient-to-r from-amber-500 to-amber-600 text-black font-bold rounded-full px-10 py-3 text-lg hover:from-amber-400 hover:to-amber-500 disabled:opacity-50 shadow-lg">
          {spinning ? "Girando..." : "TIRAR LA PALANCA"}
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

function ScratchCardGame({ config, onPlay }) {
  const canvasRef = useRef(null);
  const [scratching, setScratching] = useState(false);
  const [result, setResult] = useState(null);
  const [revealed, setRevealed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [scratchPercent, setScratchPercent] = useState(0);
  const isDrawing = useRef(false);
  const resultRef = useRef(null);

  const startGame = async () => {
    try {
      const res = await onPlay();
      resultRef.current = res;
      setResult(res);
      setLoaded(true);
      // Draw golden scratch layer after result is ready
      requestAnimationFrame(() => drawScratchLayer());
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al jugar");
    }
  };

  const drawScratchLayer = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    // Golden gradient overlay
    const grad = ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, "#D4A017");
    grad.addColorStop(0.3, "#FFD700");
    grad.addColorStop(0.6, "#DAA520");
    grad.addColorStop(1, "#B8860B");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    // Add texture dots
    for (let i = 0; i < 300; i++) {
      ctx.beginPath();
      ctx.arc(Math.random() * w, Math.random() * h, Math.random() * 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.15})`;
      ctx.fill();
    }
    // "RASPA AQUI" text
    ctx.fillStyle = "#8B6914";
    ctx.font = "bold 20px Manrope";
    ctx.textAlign = "center";
    ctx.fillText("RASPA AQUI", w / 2, h / 2 - 5);
    ctx.font = "14px Manrope";
    ctx.fillText("Usa tu dedo o mouse", w / 2, h / 2 + 20);
  };

  const scratch = (e) => {
    if (!loaded || revealed) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    let x, y;
    if (e.touches) {
      x = (e.touches[0].clientX - rect.left) * scaleX;
      y = (e.touches[0].clientY - rect.top) * scaleY;
    } else {
      x = (e.clientX - rect.left) * scaleX;
      y = (e.clientY - rect.top) * scaleY;
    }
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(x, y, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = "source-over";
    // Calculate scratch percentage
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    let transparent = 0;
    for (let i = 3; i < imageData.data.length; i += 4) {
      if (imageData.data[i] === 0) transparent++;
    }
    const pct = (transparent / (imageData.data.length / 4)) * 100;
    setScratchPercent(pct);
    if (pct > 45 && !revealed) {
      setRevealed(true);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {revealed && <Confetti />}
      {!loaded ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-72 h-44 rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg border-2 border-amber-500/50">
            <div className="text-center">
              <p className="text-5xl mb-2">🎟</p>
              <p className="text-amber-900 font-bold text-lg">Raspadita Faculty</p>
            </div>
          </div>
          <Button data-testid="scratch-start-btn" onClick={startGame}
            className="bg-gradient-to-r from-amber-500 to-amber-600 text-black font-bold rounded-full px-10 py-3 text-lg hover:from-amber-400 hover:to-amber-500 shadow-lg">
            OBTENER MI RASPADITA
          </Button>
        </div>
      ) : (
        <div className="relative w-72 h-44 select-none" data-testid="scratch-card">
          {/* Prize underneath */}
          <div className="absolute inset-0 rounded-2xl bg-card border-2 border-primary flex items-center justify-center">
            <div className="text-center p-4">
              <p className="text-3xl mb-2">🎉</p>
              <p className="text-xl font-bold text-primary">{result?.prize}</p>
              {result?.coupon && <p className="text-sm text-muted-foreground mt-1">Cupon: {result?.coupon}</p>}
            </div>
          </div>
          {/* Scratch canvas on top */}
          {!revealed && (
            <canvas
              ref={canvasRef}
              width={288}
              height={176}
              className="absolute inset-0 w-full h-full rounded-2xl cursor-pointer touch-none"
              data-testid="scratch-canvas"
              onMouseDown={() => { isDrawing.current = true; setScratching(true); }}
              onMouseUp={() => { isDrawing.current = false; }}
              onMouseLeave={() => { isDrawing.current = false; }}
              onMouseMove={e => isDrawing.current && scratch(e)}
              onTouchStart={() => { isDrawing.current = true; setScratching(true); }}
              onTouchEnd={() => { isDrawing.current = false; }}
              onTouchMove={e => { e.preventDefault(); scratch(e); }}
            />
          )}
        </div>
      )}
      {loaded && !revealed && <p className="text-muted-foreground text-sm">Raspa la zona dorada para descubrir tu premio</p>}
      {revealed && result && (
        <div className="text-center animate-fade-in-up" data-testid="prize-result">
          <p className="text-2xl font-bold text-primary mb-2">{result.prize}</p>
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

  const GameComponent = { roulette: RouletteGame, slot_machine: SlotMachineGame, scratch_card: ScratchCardGame }[gameType];

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
