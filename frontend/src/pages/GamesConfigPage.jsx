import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Gamepad2, Settings, Trophy, Users } from "lucide-react";

export default function GamesConfigPage() {
  const [configs, setConfigs] = useState([]);
  const [plays, setPlays] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/games/config`),
      axios.get(`${API}/games/plays`)
    ]).then(([c, p]) => {
      setConfigs(c.data);
      setPlays(p.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const updateConfig = async (config) => {
    try {
      await axios.put(`${API}/games/config/${config.id}`, {
        game_type: config.game_type,
        name: config.name,
        prizes: config.prizes,
        active: config.active,
        max_plays_per_whatsapp: config.max_plays_per_whatsapp
      });
      toast.success("Configuracion guardada");
    } catch { toast.error("Error al guardar"); }
  };

  const updatePrize = (configIdx, prizeIdx, field, value) => {
    setConfigs(prev => {
      const copy = [...prev];
      copy[configIdx] = { ...copy[configIdx], prizes: [...copy[configIdx].prizes] };
      copy[configIdx].prizes[prizeIdx] = { ...copy[configIdx].prizes[prizeIdx], [field]: value };
      return copy;
    });
  };

  const toggleActive = (configIdx) => {
    setConfigs(prev => {
      const copy = [...prev];
      copy[configIdx] = { ...copy[configIdx], active: !copy[configIdx].active };
      return copy;
    });
  };

  const gameTypeLabel = { roulette: "Ruleta", mystery_box: "Caja Misteriosa", lucky_button: "Boton de Suerte" };
  const gameTypeIcon = { roulette: "🎡", mystery_box: "🎁", lucky_button: "⚡" };
  const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;

  if (loading) return <div className="text-zinc-500 text-center py-12">Cargando configuracion...</div>;

  return (
    <div data-testid="games-config-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-white font-heading">Juegos</h1>
        <p className="text-sm text-zinc-500 mt-1">Configura probabilidades y premios de cada juego</p>
      </div>

      <Tabs defaultValue="config" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="config" className="data-[state=active]:bg-lime-400/10 data-[state=active]:text-lime-400"><Settings size={14} className="mr-1" /> Configuracion</TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-lime-400/10 data-[state=active]:text-lime-400"><Trophy size={14} className="mr-1" /> Historial</TabsTrigger>
          <TabsTrigger value="links" className="data-[state=active]:bg-lime-400/10 data-[state=active]:text-lime-400"><Users size={14} className="mr-1" /> Links QR</TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-4 mt-4">
          {configs.map((config, ci) => (
            <Card key={config.id} className="bg-[#0A0A0A] border-white/6 rounded-2xl" data-testid={`game-config-${config.game_type}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg text-white flex items-center gap-2">
                  <span className="text-2xl">{gameTypeIcon[config.game_type]}</span>
                  {config.name}
                </CardTitle>
                <div className="flex items-center gap-3">
                  <Label className="text-xs text-zinc-500">Activo</Label>
                  <Switch checked={config.active} onCheckedChange={() => toggleActive(ci)} data-testid={`toggle-${config.game_type}`} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 mb-3">
                  <Label className="text-xs text-zinc-500">Max jugadas por WhatsApp:</Label>
                  <Input type="number" value={config.max_plays_per_whatsapp} onChange={e => setConfigs(prev => { const c = [...prev]; c[ci] = { ...c[ci], max_plays_per_whatsapp: parseInt(e.target.value) || 1 }; return c; })} className="w-20 bg-zinc-900 border-zinc-800 text-white h-8 text-sm" />
                </div>
                <div className="space-y-2">
                  <div className="grid grid-cols-12 gap-2 text-xs text-zinc-500 font-medium px-1">
                    <span className="col-span-4">Premio</span>
                    <span className="col-span-2">Probabilidad</span>
                    <span className="col-span-3">Cupon</span>
                    <span className="col-span-2">Color</span>
                  </div>
                  {config.prizes.map((prize, pi) => (
                    <div key={pi} className="grid grid-cols-12 gap-2 items-center">
                      <Input value={prize.name} onChange={e => updatePrize(ci, pi, "name", e.target.value)} className="col-span-4 bg-zinc-900 border-zinc-800 text-white h-8 text-xs" />
                      <Input type="number" value={prize.probability} onChange={e => updatePrize(ci, pi, "probability", parseFloat(e.target.value) || 0)} className="col-span-2 bg-zinc-900 border-zinc-800 text-white h-8 text-xs" />
                      <Input value={prize.coupon || ""} onChange={e => updatePrize(ci, pi, "coupon", e.target.value)} className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8 text-xs" />
                      <Input type="color" value={prize.color || "#A3E635"} onChange={e => updatePrize(ci, pi, "color", e.target.value)} className="col-span-2 bg-zinc-900 border-zinc-800 h-8 p-1 cursor-pointer" />
                      <span className="col-span-1 text-xs text-zinc-500 text-center">{prize.probability}%</span>
                    </div>
                  ))}
                </div>
                <Button data-testid={`save-game-${config.game_type}`} onClick={() => updateConfig(config)} className="bg-lime-400 text-black font-bold rounded-full hover:bg-lime-300 text-sm">
                  Guardar Cambios
                </Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card className="bg-[#0A0A0A] border-white/6 rounded-2xl">
            <CardContent className="p-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      <th className="text-left p-2 text-zinc-400">Nombre</th>
                      <th className="text-left p-2 text-zinc-400">WhatsApp</th>
                      <th className="text-left p-2 text-zinc-400">Juego</th>
                      <th className="text-left p-2 text-zinc-400">Premio</th>
                      <th className="text-left p-2 text-zinc-400">Fecha</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plays.map(play => (
                      <tr key={play.id} className="border-b border-zinc-900 hover:bg-zinc-900/30">
                        <td className="p-2 text-white">{play.name}</td>
                        <td className="p-2 text-zinc-400">{play.whatsapp}</td>
                        <td className="p-2"><Badge variant="outline" className="text-xs">{gameTypeLabel[play.game_type] || play.game_type}</Badge></td>
                        <td className="p-2 text-lime-400">{play.prize}</td>
                        <td className="p-2 text-zinc-500">{play.played_at?.slice(0, 10)}</td>
                      </tr>
                    ))}
                    {plays.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-zinc-600">Sin jugadas registradas</td></tr>}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="links" className="mt-4">
          <Card className="bg-[#0A0A0A] border-white/6 rounded-2xl">
            <CardContent className="p-6 space-y-4">
              <p className="text-sm text-zinc-400">Comparte estos links para que tus clientes jueguen. Puedes generar codigos QR con ellos.</p>
              {["roulette", "mystery_box", "lucky_button"].map(gt => (
                <div key={gt} className="flex items-center gap-3 p-3 bg-zinc-900/50 rounded-lg">
                  <span className="text-2xl">{gameTypeIcon[gt]}</span>
                  <div className="flex-1">
                    <p className="text-sm text-white font-medium">{gameTypeLabel[gt]}</p>
                    <p className="text-xs text-lime-400 break-all">{backendUrl}/game/{gt}</p>
                  </div>
                  <Button size="sm" variant="outline" className="border-zinc-700 text-zinc-300 text-xs" onClick={() => { navigator.clipboard.writeText(`${backendUrl}/game/${gt}`); toast.success("Link copiado"); }}>Copiar</Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
