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
      toast.success("Configuración guardada");
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

  const gameTypeLabel = { roulette: "Ruleta", slot_machine: "Tragamonedas", scratch_card: "Raspadita" };
  const gameTypeIcon = { roulette: "🎡", slot_machine: "🎰", scratch_card: "🎟" };
  const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando configuración...</div>;

  return (
    <div data-testid="games-config-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Juegos</h1>
        <p className="text-sm text-muted-foreground mt-1">Configura probabilidades y premios de cada juego</p>
      </div>

      <Tabs defaultValue="config" className="w-full">
        <TabsList className="bg-muted border border-input">
          <TabsTrigger value="config" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary"><Settings size={14} className="mr-1" /> Configuración</TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary"><Trophy size={14} className="mr-1" /> Historial</TabsTrigger>
          <TabsTrigger value="links" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary"><Users size={14} className="mr-1" /> Links QR</TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-4 mt-4">
          {configs.map((config, ci) => (
            <Card key={config.id} className="bg-card border-border rounded-2xl" data-testid={`game-config-${config.game_type}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg text-foreground flex items-center gap-2">
                  <span className="text-2xl">{gameTypeIcon[config.game_type]}</span>
                  {config.name}
                </CardTitle>
                <div className="flex items-center gap-3">
                  <Label className="text-xs text-muted-foreground">Activo</Label>
                  <Switch checked={config.active} onCheckedChange={() => toggleActive(ci)} data-testid={`toggle-${config.game_type}`} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 mb-3">
                  <Label className="text-xs text-muted-foreground">Max jugadas por WhatsApp:</Label>
                  <Input type="number" value={config.max_plays_per_whatsapp} onChange={e => setConfigs(prev => { const c = [...prev]; c[ci] = { ...c[ci], max_plays_per_whatsapp: parseInt(e.target.value) || 1 }; return c; })} className="w-20 bg-muted border-input text-foreground h-8 text-sm" />
                </div>
                <div className="space-y-2">
                  <div className="grid grid-cols-12 gap-2 text-xs text-muted-foreground font-medium px-1">
                    <span className="col-span-4">Premio</span>
                    <span className="col-span-2">Probabilidad</span>
                    <span className="col-span-3">Cupon</span>
                    <span className="col-span-2">Color</span>
                  </div>
                  {config.prizes.map((prize, pi) => (
                    <div key={pi} className="grid grid-cols-12 gap-2 items-center">
                      <Input value={prize.name} onChange={e => updatePrize(ci, pi, "name", e.target.value)} className="col-span-4 bg-muted border-input text-foreground h-8 text-xs" />
                      <Input type="number" value={prize.probability} onChange={e => updatePrize(ci, pi, "probability", parseFloat(e.target.value) || 0)} className="col-span-2 bg-muted border-input text-foreground h-8 text-xs" />
                      <Input value={prize.coupon || ""} onChange={e => updatePrize(ci, pi, "coupon", e.target.value)} className="col-span-3 bg-muted border-input text-foreground h-8 text-xs" />
                      <Input type="color" value={prize.color || "#A3E635"} onChange={e => updatePrize(ci, pi, "color", e.target.value)} className="col-span-2 bg-muted border-input h-8 p-1 cursor-pointer" />
                      <span className="col-span-1 text-xs text-muted-foreground text-center">{prize.probability}%</span>
                    </div>
                  ))}
                </div>
                <Button data-testid={`save-game-${config.game_type}`} onClick={() => updateConfig(config)} className="bg-primary text-primary-foreground font-bold rounded-full hover:bg-primary/90 text-sm">
                  Guardar Cambios
                </Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card className="bg-card border-border rounded-2xl">
            <CardContent className="p-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-input">
                      <th className="text-left p-2 text-muted-foreground">Nombre</th>
                      <th className="text-left p-2 text-muted-foreground">WhatsApp</th>
                      <th className="text-left p-2 text-muted-foreground">Juego</th>
                      <th className="text-left p-2 text-muted-foreground">Premio</th>
                      <th className="text-left p-2 text-muted-foreground">Fecha</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plays.map(play => (
                      <tr key={play.id} className="border-b border-muted hover:bg-muted/30">
                        <td className="p-2 text-foreground">{play.name}</td>
                        <td className="p-2 text-muted-foreground">{play.whatsapp}</td>
                        <td className="p-2"><Badge variant="outline" className="text-xs">{gameTypeLabel[play.game_type] || play.game_type}</Badge></td>
                        <td className="p-2 text-primary">{play.prize}</td>
                        <td className="p-2 text-muted-foreground">{play.played_at?.slice(0, 10)}</td>
                      </tr>
                    ))}
                    {plays.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-muted-foreground">Sin jugadas registradas</td></tr>}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="links" className="mt-4">
          <Card className="bg-card border-border rounded-2xl">
            <CardContent className="p-6 space-y-4">
              <p className="text-sm text-muted-foreground">Comparte estos links para que tus clientes jueguen. Puedes generar códigos QR con ellos.</p>
              {["roulette", "slot_machine", "scratch_card"].map(gt => (
                <div key={gt} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                  <span className="text-2xl">{gameTypeIcon[gt]}</span>
                  <div className="flex-1">
                    <p className="text-sm text-foreground font-medium">{gameTypeLabel[gt]}</p>
                    <p className="text-xs text-primary break-all">{backendUrl}/game/{gt}</p>
                  </div>
                  <Button size="sm" variant="outline" className="border-input text-foreground/80 text-xs" onClick={() => { navigator.clipboard.writeText(`${backendUrl}/game/${gt}`); toast.success("Link copiado"); }}>Copiar</Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
