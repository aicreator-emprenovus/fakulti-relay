import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Footer } from "@/App";
import { Gift, Star, Sparkles, Trophy } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const LOGO_URL = "https://customer-assets.emergentagent.com/job_59080748-b0e0-4800-8ad6-c0799fc3b737/artifacts/hs7em91m_image.png";

function Confetti() {
  const colors = ["#FFD700", "#FF6B35", "#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#EF4444", "#10B981"];
  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {Array.from({ length: 60 }).map((_, i) => (
        <div key={i} className="confetti-piece" style={{ left: `${Math.random() * 100}%`, backgroundColor: colors[i % colors.length], animationDelay: `${Math.random() * 2}s`, animationDuration: `${2 + Math.random() * 2}s`, borderRadius: Math.random() > 0.5 ? "50%" : "2px", width: `${6 + Math.random() * 10}px`, height: `${6 + Math.random() * 10}px` }} />
      ))}
    </div>
  );
}

/* ========== ROULETTE ========== */
function RouletteGame({ config, onPlay, products }) {
  const canvasRef = useRef(null);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const rotationRef = useRef(0);
  const imgCache = useRef({});

  const prizes = config?.prizes || [];
  const segAngle = 360 / (prizes.length || 1);

  // Preload product images
  useEffect(() => {
    products.forEach(p => {
      if (p.image_url) {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.src = p.image_url;
        img.onload = () => { imgCache.current[p.name] = img; drawWheel(rotationRef.current); };
      }
    });
  }, [products]);

  useEffect(() => { drawWheel(0); }, [config, products]);

  const SEGMENT_COLORS = [
    "#1a1a2e", "#16213e", "#0f3460", "#1a1a2e", "#16213e", "#0f3460",
    "#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"
  ];
  const ACCENT_COLORS = [
    "#FFD700", "#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981",
    "#EF4444", "#06B6D4", "#F97316", "#EC4899"
  ];

  const drawWheel = useCallback((rotation) => {
    const canvas = canvasRef.current;
    if (!canvas || prizes.length === 0) return;
    const ctx = canvas.getContext("2d");
    const size = canvas.width;
    const cx = size / 2;
    const cy = size / 2;
    const r = cx - 60;

    ctx.clearRect(0, 0, size, size);

    // Outer glow ring
    const glowGrad = ctx.createRadialGradient(cx, cy, r + 10, cx, cy, r + 50);
    glowGrad.addColorStop(0, "rgba(163, 230, 53, 0.3)");
    glowGrad.addColorStop(1, "rgba(163, 230, 53, 0)");
    ctx.beginPath();
    ctx.arc(cx, cy, r + 50, 0, Math.PI * 2);
    ctx.fillStyle = glowGrad;
    ctx.fill();

    // LED lights ring
    const numLights = 24;
    for (let i = 0; i < numLights; i++) {
      const angle = (i / numLights) * Math.PI * 2;
      const lx = cx + (r + 25) * Math.cos(angle);
      const ly = cy + (r + 25) * Math.sin(angle);
      const isLit = Math.floor(Date.now() / 300 + i) % 3 === 0;
      ctx.beginPath();
      ctx.arc(lx, ly, 5, 0, Math.PI * 2);
      ctx.fillStyle = isLit ? "#FFD700" : "#4a4a4a";
      ctx.fill();
      if (isLit) {
        ctx.shadowColor = "#FFD700";
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    // Outer ring
    ctx.beginPath();
    ctx.arc(cx, cy, r + 8, 0, Math.PI * 2);
    ctx.strokeStyle = "#FFD700";
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((rotation * Math.PI) / 180);

    prizes.forEach((prize, i) => {
      const start = (i * segAngle * Math.PI) / 180;
      const end = ((i + 1) * segAngle * Math.PI) / 180;

      // Segment fill
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, r, start, end);
      ctx.fillStyle = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
      ctx.fill();

      // Accent border
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, r, start, end);
      ctx.strokeStyle = ACCENT_COLORS[i % ACCENT_COLORS.length] + "60";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Inner accent line
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(r * Math.cos(start), r * Math.sin(start));
      ctx.strokeStyle = "rgba(255,215,0,0.3)";
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.save();
      const midAngle = start + (end - start) / 2;
      ctx.rotate(midAngle);

      // Try to draw product image
      const matchedProduct = products.find(p =>
        prize.name.toLowerCase().includes(p.name.split(" ")[0].toLowerCase()) ||
        p.name.toLowerCase().includes(prize.name.split(" ")[0].toLowerCase())
      );
      const img = matchedProduct ? imgCache.current[matchedProduct.name] : null;

      if (img) {
        ctx.save();
        ctx.translate(r * 0.45, 0);
        ctx.rotate(-midAngle - (rotation * Math.PI) / 180);
        const imgSize = 32;
        ctx.drawImage(img, -imgSize / 2, -imgSize / 2, imgSize, imgSize);
        ctx.restore();
      }

      // Prize text
      ctx.translate(r * 0.7, 0);
      ctx.rotate(Math.PI / 2);
      ctx.fillStyle = ACCENT_COLORS[i % ACCENT_COLORS.length];
      ctx.font = "bold 10px Manrope";
      ctx.textAlign = "center";
      const words = prize.name.split(" ");
      words.forEach((w, wi) => ctx.fillText(w, 0, wi * 12 - (words.length - 1) * 5));
      ctx.restore();
    });

    ctx.restore();

    // Pointer - premium arrow
    const pointerX = cx + r + 8;
    ctx.beginPath();
    ctx.moveTo(pointerX - 5, cy);
    ctx.lineTo(pointerX + 35, cy - 22);
    ctx.lineTo(pointerX + 35, cy + 22);
    ctx.closePath();
    const pGrad = ctx.createLinearGradient(pointerX, cy - 22, pointerX, cy + 22);
    pGrad.addColorStop(0, "#FF4444");
    pGrad.addColorStop(0.5, "#FF6666");
    pGrad.addColorStop(1, "#CC0000");
    ctx.fillStyle = pGrad;
    ctx.fill();
    ctx.strokeStyle = "#8B0000";
    ctx.lineWidth = 2;
    ctx.stroke();
    // Pointer dot
    ctx.beginPath();
    ctx.arc(pointerX + 22, cy, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();

    // Center button
    const centerGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 30);
    centerGrad.addColorStop(0, "#2a2a2a");
    centerGrad.addColorStop(1, "#0a0a0a");
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, Math.PI * 2);
    ctx.fillStyle = centerGrad;
    ctx.fill();
    ctx.strokeStyle = "#FFD700";
    ctx.lineWidth = 3;
    ctx.stroke();
    // Center logo
    ctx.fillStyle = "#A3E635";
    ctx.font = "bold 9px Manrope";
    ctx.textAlign = "center";
    ctx.fillText("FAKULTI", cx, cy + 3);
  }, [prizes, segAngle, products]);

  const spin = async () => {
    setSpinning(true);
    setResult(null);
    try {
      const res = await onPlay();
      const targetAngle = 360 - (res.prize_index * segAngle + segAngle / 2);
      const totalRotation = 360 * 6 + targetAngle;
      let startTime = null;
      const duration = 5000;
      const animate = (time) => {
        if (!startTime) startTime = time;
        const progress = Math.min((time - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4);
        rotationRef.current = eased * totalRotation;
        drawWheel(rotationRef.current);
        if (progress < 1) requestAnimationFrame(animate);
        else { setSpinning(false); setResult(res); }
      };
      requestAnimationFrame(animate);
    } catch (err) { setSpinning(false); toast.error(err.response?.data?.detail || "Error"); }
  };

  return (
    <div className="flex flex-col items-center gap-5">
      {result && <Confetti />}
      <div className="relative">
        <canvas ref={canvasRef} width={440} height={440} className="max-w-full" data-testid="roulette-canvas" />
      </div>
      {!result ? (
        <Button data-testid="spin-btn" onClick={spin} disabled={spinning}
          className="relative bg-gradient-to-r from-[#A3E635] to-[#65a30d] text-black font-black rounded-full px-12 py-4 text-lg hover:shadow-[0_0_30px_rgba(163,230,53,0.5)] transition-all disabled:opacity-50 uppercase tracking-wider">
          {spinning ? (
            <span className="flex items-center gap-2"><Sparkles size={18} className="animate-spin" /> Girando...</span>
          ) : (
            <span className="flex items-center gap-2"><Star size={18} /> Girar la Ruleta</span>
          )}
        </Button>
      ) : (
        <div className="text-center animate-fade-in-up bg-gradient-to-b from-card to-muted/30 rounded-2xl p-6 border border-primary/30 shadow-lg" data-testid="prize-result">
          <Trophy size={32} className="text-yellow-500 mx-auto mb-2" />
          <p className="text-2xl font-black text-primary mb-1">{result.prize}</p>
          <p className="text-muted-foreground text-sm">{result.message}</p>
          {result.coupon && (
            <div className="mt-3 bg-primary/10 border border-primary/30 rounded-xl px-5 py-2 inline-block">
              <p className="text-xs text-muted-foreground">Tu codigo</p>
              <p className="text-lg font-black text-primary tracking-widest">{result.coupon}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ========== SLOT MACHINE ========== */
function SlotMachineGame({ config, onPlay, products }) {
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [displayReels, setDisplayReels] = useState([0, 0, 0]);
  const intervalRefs = useRef([]);

  // Use product images as symbols
  const productSymbols = products.map(p => ({
    name: p.name.split(" ")[0],
    image: p.image_url,
    emoji: p.category === "nutricion" ? "🦴" : p.category === "bienestar" ? "💊" : p.category === "cbd" ? "🌿" : "⚡"
  }));
  // Add extra symbols
  const SYMBOLS = [
    ...productSymbols,
    { name: "Star", image: null, emoji: "⭐" },
    { name: "Diamond", image: null, emoji: "💎" },
  ];

  const spin = async () => {
    setSpinning(true);
    setResult(null);
    for (let r = 0; r < 3; r++) {
      intervalRefs.current[r] = setInterval(() => {
        setDisplayReels(prev => { const c = [...prev]; c[r] = (c[r] + 1) % SYMBOLS.length; return c; });
      }, 70 + r * 25);
    }
    try {
      const res = await onPlay();
      const pi = res.prize_index;
      let finalReels;
      if (pi <= 1) finalReels = [pi % SYMBOLS.length, pi % SYMBOLS.length, pi % SYMBOLS.length];
      else if (pi <= 3) finalReels = [pi % SYMBOLS.length, pi % SYMBOLS.length, (pi + 2) % SYMBOLS.length];
      else finalReels = [0, 2, 4 % SYMBOLS.length];
      for (let r = 0; r < 3; r++) {
        await new Promise(resolve => setTimeout(resolve, 800 + r * 600));
        clearInterval(intervalRefs.current[r]);
        setDisplayReels(prev => { const c = [...prev]; c[r] = finalReels[r]; return c; });
      }
      setSpinning(false);
      setResult(res);
    } catch (err) { intervalRefs.current.forEach(clearInterval); setSpinning(false); toast.error(err.response?.data?.detail || "Error"); }
  };

  useEffect(() => { return () => intervalRefs.current.forEach(clearInterval); }, []);

  return (
    <div className="flex flex-col items-center gap-5">
      {result && <Confetti />}
      {/* Machine frame */}
      <div className="relative" data-testid="slot-machine">
        {/* Top sign */}
        <div className="relative z-10 text-center -mb-3">
          <div className="inline-block bg-gradient-to-r from-red-700 via-red-500 to-red-700 px-8 py-2 rounded-t-2xl border-2 border-yellow-500/60">
            <p className="text-yellow-300 font-black text-xl tracking-[0.3em] uppercase" style={{ textShadow: "0 0 10px rgba(255,215,0,0.5)" }}>
              Tragamonedas
            </p>
          </div>
        </div>

        {/* Machine body */}
        <div className="bg-gradient-to-b from-[#2a0a0a] via-[#1a0505] to-[#0a0000] rounded-2xl p-5 border-2 border-yellow-600/40 shadow-[0_0_40px_rgba(200,50,50,0.15)] relative overflow-hidden">
          {/* Decorative rivets */}
          <div className="absolute top-3 left-3 w-3 h-3 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-700 shadow-inner" />
          <div className="absolute top-3 right-3 w-3 h-3 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-700 shadow-inner" />
          <div className="absolute bottom-3 left-3 w-3 h-3 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-700 shadow-inner" />
          <div className="absolute bottom-3 right-3 w-3 h-3 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-700 shadow-inner" />

          {/* Display window */}
          <div className="bg-black/80 rounded-xl p-4 border border-yellow-600/20 relative">
            {/* Win line */}
            <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[2px] bg-red-500/40 z-10" />
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-6 bg-red-500 rounded-r-sm z-10" />
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-6 bg-red-500 rounded-l-sm z-10" />

            <div className="flex gap-3 justify-center">
              {[0, 1, 2].map(r => (
                <div key={r}
                  className="w-24 h-28 rounded-xl flex flex-col items-center justify-center border border-yellow-600/20 overflow-hidden relative"
                  style={{ background: "linear-gradient(180deg, rgba(255,215,0,0.05) 0%, rgba(0,0,0,0.3) 50%, rgba(255,215,0,0.05) 100%)" }}>
                  {/* Reel content */}
                  <div className={`flex flex-col items-center justify-center transition-transform ${spinning ? "animate-bounce" : ""}`} style={{ animationDelay: `${r * 80}ms` }}>
                    {SYMBOLS[displayReels[r]]?.image ? (
                      <img
                        src={SYMBOLS[displayReels[r]].image}
                        alt={SYMBOLS[displayReels[r]].name}
                        className="w-14 h-14 object-contain drop-shadow-[0_0_8px_rgba(163,230,53,0.4)]"
                      />
                    ) : (
                      <span className="text-5xl">{SYMBOLS[displayReels[r]]?.emoji}</span>
                    )}
                    <span className="text-[9px] text-yellow-500/70 mt-1 font-medium">{SYMBOLS[displayReels[r]]?.name}</span>
                  </div>
                  {/* Reel shine overlay */}
                  <div className="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-white/5 pointer-events-none" />
                </div>
              ))}
            </div>
          </div>

          {/* Bottom accent */}
          <div className="flex justify-center mt-3 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className={`w-2.5 h-2.5 rounded-full ${spinning ? "animate-pulse" : ""}`}
                style={{ backgroundColor: i % 2 === 0 ? "#FFD700" : "#EF4444", animationDelay: `${i * 200}ms` }} />
            ))}
          </div>
        </div>
      </div>

      {!result ? (
        <Button data-testid="slot-spin-btn" onClick={spin} disabled={spinning}
          className="relative bg-gradient-to-r from-red-600 via-red-500 to-red-600 text-white font-black rounded-full px-12 py-4 text-lg hover:shadow-[0_0_30px_rgba(220,38,38,0.4)] transition-all disabled:opacity-50 uppercase tracking-wider border border-yellow-500/30">
          {spinning ? (
            <span className="flex items-center gap-2"><Sparkles size={18} className="animate-spin" /> Girando...</span>
          ) : (
            <span className="flex items-center gap-2"><Sparkles size={18} /> Tirar la Palanca</span>
          )}
        </Button>
      ) : (
        <div className="text-center animate-fade-in-up bg-gradient-to-b from-card to-muted/30 rounded-2xl p-6 border border-primary/30 shadow-lg" data-testid="prize-result">
          <Trophy size={32} className="text-yellow-500 mx-auto mb-2" />
          <p className="text-2xl font-black text-primary mb-1">{result.prize}</p>
          <p className="text-muted-foreground text-sm">{result.message}</p>
          {result.coupon && (
            <div className="mt-3 bg-primary/10 border border-primary/30 rounded-xl px-5 py-2 inline-block">
              <p className="text-xs text-muted-foreground">Tu codigo</p>
              <p className="text-lg font-black text-primary tracking-widest">{result.coupon}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ========== SCRATCH CARD - Golden Ticket Willy Wonka ========== */
function ScratchCardGame({ config, onPlay }) {
  const canvasRef = useRef(null);
  const [result, setResult] = useState(null);
  const [revealed, setRevealed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [scratching, setScratching] = useState(false);
  const isDrawing = useRef(false);
  const coinCursor = useRef(null);

  const startGame = async () => {
    try {
      const res = await onPlay();
      setResult(res);
      setLoaded(true);
      requestAnimationFrame(() => drawGoldenTicket());
    } catch (err) { toast.error(err.response?.data?.detail || "Error"); }
  };

  const drawGoldenTicket = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    // Golden ticket base
    const goldGrad = ctx.createLinearGradient(0, 0, w, h);
    goldGrad.addColorStop(0, "#C9961A");
    goldGrad.addColorStop(0.15, "#FFD700");
    goldGrad.addColorStop(0.3, "#DAA520");
    goldGrad.addColorStop(0.5, "#FFD700");
    goldGrad.addColorStop(0.7, "#B8860B");
    goldGrad.addColorStop(0.85, "#FFD700");
    goldGrad.addColorStop(1, "#C9961A");
    ctx.fillStyle = goldGrad;
    ctx.fillRect(0, 0, w, h);

    // Ticket border pattern (perforated edge look)
    ctx.strokeStyle = "#8B6914";
    ctx.lineWidth = 3;
    ctx.setLineDash([8, 4]);
    ctx.strokeRect(8, 8, w - 16, h - 16);
    ctx.setLineDash([]);

    // Inner border
    ctx.strokeStyle = "#B8860B";
    ctx.lineWidth = 1;
    ctx.strokeRect(16, 16, w - 32, h - 32);

    // Decorative corner ornaments
    const cornerSize = 20;
    const corners = [[20, 20], [w - 20, 20], [20, h - 20], [w - 20, h - 20]];
    corners.forEach(([cx, cy]) => {
      ctx.beginPath();
      ctx.arc(cx, cy, cornerSize / 2, 0, Math.PI * 2);
      ctx.strokeStyle = "#8B6914";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#8B6914";
      ctx.fill();
    });

    // Stars pattern
    for (let i = 0; i < 12; i++) {
      const sx = 40 + Math.random() * (w - 80);
      const sy = 40 + Math.random() * (h - 80);
      drawStar(ctx, sx, sy, 4, 8, 4);
      ctx.fillStyle = `rgba(139, 105, 20, ${0.1 + Math.random() * 0.15})`;
      ctx.fill();
    }

    // Sparkle texture
    for (let i = 0; i < 200; i++) {
      ctx.beginPath();
      ctx.arc(Math.random() * w, Math.random() * h, Math.random() * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.2})`;
      ctx.fill();
    }

    // "GOLDEN TICKET" header
    ctx.save();
    ctx.fillStyle = "#5C3D0E";
    ctx.font = "bold 22px Manrope";
    ctx.textAlign = "center";
    ctx.fillText("GOLDEN TICKET", w / 2, 52);

    // Fakulti text
    ctx.fillStyle = "#7B5C28";
    ctx.font = "italic 11px Manrope";
    ctx.fillText("Fakulti Laboratorios", w / 2, 70);

    // Scratch instruction
    ctx.fillStyle = "#5C3D0E";
    ctx.font = "bold 14px Manrope";
    ctx.fillText("RASPA CON LA MONEDA", w / 2, h / 2 + 5);

    // Coin icon instruction
    ctx.font = "28px sans-serif";
    ctx.fillText("\uD83E\uDE99", w / 2, h / 2 + 40);

    // Bottom text
    ctx.fillStyle = "#7B5C28";
    ctx.font = "10px Manrope";
    ctx.fillText("Descubre tu premio especial", w / 2, h - 28);
    ctx.restore();
  };

  function drawStar(ctx, cx, cy, spikes, outerR, innerR) {
    let rot = Math.PI / 2 * 3;
    let step = Math.PI / spikes;
    ctx.beginPath();
    ctx.moveTo(cx, cy - outerR);
    for (let i = 0; i < spikes; i++) {
      ctx.lineTo(cx + Math.cos(rot) * outerR, cy + Math.sin(rot) * outerR);
      rot += step;
      ctx.lineTo(cx + Math.cos(rot) * innerR, cy + Math.sin(rot) * innerR);
      rot += step;
    }
    ctx.closePath();
  }

  const scratch = (e) => {
    if (!loaded || revealed) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    let x, y;
    if (e.touches) { x = (e.touches[0].clientX - rect.left) * scaleX; y = (e.touches[0].clientY - rect.top) * scaleY; }
    else { x = (e.clientX - rect.left) * scaleX; y = (e.clientY - rect.top) * scaleY; }

    ctx.globalCompositeOperation = "destination-out";
    // Coin-shaped scratch (circular with slight texture)
    ctx.beginPath();
    ctx.arc(x, y, 24, 0, Math.PI * 2);
    ctx.fill();
    // Add smaller scratches around for realism
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.arc(x + (Math.random() - 0.5) * 20, y + (Math.random() - 0.5) * 20, 8, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";

    // Check scratch percentage
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    let transparent = 0;
    for (let i = 3; i < imageData.data.length; i += 4) { if (imageData.data[i] === 0) transparent++; }
    const pct = (transparent / (imageData.data.length / 4)) * 100;
    if (pct > 40 && !revealed) {
      setRevealed(true);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  return (
    <div className="flex flex-col items-center gap-5">
      {revealed && <Confetti />}
      {!loaded ? (
        <div className="flex flex-col items-center gap-5">
          {/* Preview ticket */}
          <div className="relative w-80 h-48 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(218,165,32,0.3)]"
            style={{ background: "linear-gradient(135deg, #C9961A, #FFD700, #DAA520, #FFD700, #B8860B)" }}>
            <div className="absolute inset-2 border-2 border-dashed border-[#8B6914]/40 rounded-lg" />
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-[#5C3D0E] font-black text-2xl tracking-wider" style={{ textShadow: "0 1px 2px rgba(255,215,0,0.5)" }}>GOLDEN TICKET</p>
              <p className="text-[#7B5C28] text-xs italic mt-1">Fakulti Laboratorios</p>
              <div className="mt-3 flex items-center gap-2">
                <Gift size={20} className="text-[#5C3D0E]" />
                <p className="text-[#5C3D0E] font-bold text-sm">Premio Especial</p>
              </div>
            </div>
            {/* Shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-shimmer" />
          </div>
          <Button data-testid="scratch-start-btn" onClick={startGame}
            className="bg-gradient-to-r from-amber-600 via-yellow-500 to-amber-600 text-[#3d2400] font-black rounded-full px-10 py-4 text-lg hover:shadow-[0_0_30px_rgba(218,165,32,0.5)] transition-all shadow-lg uppercase tracking-wider border border-yellow-300/30">
            <span className="flex items-center gap-2"><Gift size={18} /> Obtener Mi Ticket</span>
          </Button>
        </div>
      ) : (
        <div className="relative w-80 h-48 select-none rounded-xl overflow-hidden shadow-[0_0_40px_rgba(218,165,32,0.3)]" data-testid="scratch-card">
          {/* Prize underneath */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#0a1628] to-[#1a0a28] flex items-center justify-center border-2 border-primary/30 rounded-xl">
            <div className="text-center p-4">
              <Trophy size={36} className="text-yellow-500 mx-auto mb-2" />
              <p className="text-2xl font-black text-primary">{result?.prize}</p>
              <p className="text-muted-foreground text-xs mt-1">{result?.message}</p>
              {result?.coupon && (
                <div className="mt-2 bg-primary/10 border border-primary/30 rounded-lg px-4 py-1 inline-block">
                  <p className="text-sm font-black text-primary tracking-widest">{result?.coupon}</p>
                </div>
              )}
            </div>
          </div>
          {/* Scratch canvas */}
          {!revealed && (
            <canvas ref={canvasRef} width={320} height={192}
              className="absolute inset-0 w-full h-full rounded-xl touch-none"
              style={{ cursor: `url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' fill='%23DAA520' stroke='%238B6914' stroke-width='2'/><circle cx='12' cy='12' r='2' fill='%238B6914' opacity='0.3'/><circle cx='20' cy='18' r='1.5' fill='%238B6914' opacity='0.3'/></svg>") 16 16, pointer` }}
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
      {loaded && !revealed && (
        <p className="text-muted-foreground text-sm flex items-center gap-1.5">
          <span className="text-lg">🪙</span> Raspa el ticket dorado con la moneda
        </p>
      )}
      {revealed && result && (
        <div className="text-center animate-fade-in-up bg-gradient-to-b from-card to-muted/30 rounded-2xl p-6 border border-primary/30 shadow-lg" data-testid="prize-result">
          <Trophy size={32} className="text-yellow-500 mx-auto mb-2" />
          <p className="text-2xl font-black text-primary mb-1">{result.prize}</p>
          <p className="text-muted-foreground text-sm">{result.message}</p>
          {result.coupon && (
            <div className="mt-3 bg-primary/10 border border-primary/30 rounded-xl px-5 py-2 inline-block">
              <p className="text-xs text-muted-foreground">Tu codigo</p>
              <p className="text-lg font-black text-primary tracking-widest">{result.coupon}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ========== MAIN PAGE ========== */
export default function GamePublicPage() {
  const { gameType } = useParams();
  const [config, setConfig] = useState(null);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ name: "", whatsapp: "", city: "" });
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/games/public/${gameType}`),
      axios.get(`${API}/products`).catch(() => ({ data: [] }))
    ]).then(([gameRes, prodRes]) => {
      setConfig(gameRes.data);
      setProducts(prodRes.data.filter(p => p.active));
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

  if (loading) return (
    <div className="min-h-screen bg-[#050510] flex items-center justify-center">
      <div className="animate-pulse flex flex-col items-center">
        <Sparkles size={32} className="text-primary mb-3" />
        <p className="text-muted-foreground">Cargando juego...</p>
      </div>
    </div>
  );
  if (error) return <div className="min-h-screen bg-background flex items-center justify-center text-red-400">{error}</div>;

  const GameComponent = { roulette: RouletteGame, slot_machine: SlotMachineGame, scratch_card: ScratchCardGame }[gameType];
  const gameTitle = { roulette: "Ruleta de Premios", slot_machine: "Tragamonedas", scratch_card: "Golden Ticket" }[gameType] || config?.name;

  return (
    <div className="min-h-screen bg-[#050510] flex flex-col items-center justify-center p-4 relative overflow-hidden" data-testid="game-public-page">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary/3 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-amber-500/3 rounded-full blur-[100px]" />
        <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-blue-500/3 rounded-full blur-[80px]" />
      </div>

      <div className="relative z-10 w-full max-w-md mx-auto">
        <div className="text-center mb-6">
          <img src={LOGO_URL} alt="Faculty" className="h-10 mx-auto mb-3 drop-shadow-[0_0_10px_rgba(163,230,53,0.3)]" />
          <h1 className="text-3xl font-black text-white tracking-tight">{gameTitle}</h1>
          <p className="text-sm text-gray-400 mt-1">Juega y gana premios exclusivos</p>
        </div>

        {!registered ? (
          <Card className="bg-white/5 backdrop-blur-xl border-white/10 rounded-2xl shadow-2xl" data-testid="game-register-form">
            <CardContent className="p-6">
              <div className="text-center mb-5">
                <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3 border border-primary/20">
                  <Star size={24} className="text-primary" />
                </div>
                <p className="text-white font-bold">Registrate para jugar</p>
                <p className="text-gray-400 text-xs mt-1">Solo toma unos segundos</p>
              </div>
              <form onSubmit={handleRegister} className="space-y-3">
                <div>
                  <Label className="text-gray-400 text-xs">Tu Nombre *</Label>
                  <Input data-testid="game-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="bg-white/5 border-white/10 text-white h-11 focus:border-primary/50" placeholder="Ingresa tu nombre" required />
                </div>
                <div>
                  <Label className="text-gray-400 text-xs">WhatsApp *</Label>
                  <Input data-testid="game-whatsapp" value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} className="bg-white/5 border-white/10 text-white h-11 focus:border-primary/50" placeholder="+593..." required />
                </div>
                <div>
                  <Label className="text-gray-400 text-xs">Ciudad</Label>
                  <Input value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} className="bg-white/5 border-white/10 text-white h-11 focus:border-primary/50" placeholder="Tu ciudad" />
                </div>
                <Button data-testid="game-register-btn" type="submit"
                  className="w-full bg-gradient-to-r from-primary to-[#65a30d] text-black font-black rounded-full h-12 hover:shadow-[0_0_20px_rgba(163,230,53,0.4)] transition-all uppercase tracking-wider text-sm">
                  Jugar Ahora
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          GameComponent && <GameComponent config={config} onPlay={handlePlay} products={products} />
        )}
      </div>
      <div className="absolute bottom-0 left-0 right-0 z-10">
        <Footer />
      </div>
    </div>
  );
}
