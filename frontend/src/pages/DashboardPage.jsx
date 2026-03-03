import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, DollarSign, ShoppingCart, Gamepad2, TrendingUp, UserCheck } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const STAGE_CONFIG = {
  nuevo: { label: "Nuevo", color: "#3B82F6" },
  interesado: { label: "Interesado", color: "#8B5CF6" },
  caliente: { label: "Caliente", color: "#F59E0B" },
  cliente_nuevo: { label: "Cliente Nuevo", color: "#10B981" },
  cliente_activo: { label: "Cliente Activo", color: "#A3E635" },
  frio: { label: "Frio", color: "#64748B" },
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(res => {
      setStats(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64 text-zinc-500">Cargando dashboard...</div>;
  if (!stats) return <div className="text-zinc-500">Error al cargar estadisticas</div>;

  const funnelData = Object.entries(stats.stages).map(([key, value]) => ({
    name: STAGE_CONFIG[key]?.label || key,
    value,
    color: STAGE_CONFIG[key]?.color || "#64748B",
    key
  }));

  const statCards = [
    { label: "Total Leads", value: stats.total_leads, icon: Users, color: "text-blue-400" },
    { label: "Ventas Totales", value: `$${stats.total_sales}`, icon: DollarSign, color: "text-lime-400" },
    { label: "Ordenes", value: stats.total_orders, icon: ShoppingCart, color: "text-amber-400" },
    { label: "Clientes", value: stats.total_clients, icon: UserCheck, color: "text-emerald-400" },
    { label: "Juegos Jugados", value: stats.game_plays, icon: Gamepad2, color: "text-purple-400" },
    { label: "Conversion", value: `${stats.conversion_rate}%`, icon: TrendingUp, color: "text-lime-400" },
  ];

  return (
    <div data-testid="dashboard-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Resumen general del CRM Faculty</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, i) => (
          <div key={i} className="stat-card p-4" data-testid={`stat-${card.label.toLowerCase().replace(/ /g, "-")}`}>
            <div className="flex items-center gap-2 mb-2">
              <card.icon size={16} className={card.color} />
              <span className="text-xs text-muted-foreground uppercase tracking-wider">{card.label}</span>
            </div>
            <p className="text-2xl font-bold text-foreground font-accent">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-foreground">Embudo de Ventas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {funnelData.map((stage, i) => {
                const maxVal = Math.max(...funnelData.map(s => s.value), 1);
                const pct = (stage.value / maxVal) * 100;
                return (
                  <div key={stage.key} className="flex items-center gap-3" data-testid={`funnel-stage-${stage.key}`}>
                    <span className="text-xs text-muted-foreground w-28 truncate">{stage.name}</span>
                    <div className="flex-1 h-8 bg-muted rounded-lg overflow-hidden relative">
                      <div
                        className="h-full rounded-lg transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: stage.color, animationDelay: `${i * 100}ms` }}
                      />
                      <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-foreground">
                        {stage.value}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-foreground">Ventas por Producto</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.product_stats.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={stats.product_stats}>
                  <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))" }} />
                  <Bar dataKey="revenue" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground">Sin datos de ventas aun</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-foreground">Fuentes de Trafico</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.source_stats.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={stats.source_stats} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, count }) => `${name}: ${count}`}>
                    {stats.source_stats.map((entry, i) => (
                      <Cell key={i} fill={["#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981", "#64748B"][i % 6]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground">Sin datos de fuentes</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-foreground">Leads Recientes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-56 overflow-y-auto">
              {stats.recent_leads.map(lead => (
                <div key={lead.id} className="flex items-center justify-between p-2 rounded-lg bg-muted/50 hover:bg-muted">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "20", color: STAGE_CONFIG[lead.funnel_stage]?.color }}>
                      {lead.name?.[0]}
                    </div>
                    <div>
                      <p className="text-sm text-foreground font-medium">{lead.name}</p>
                      <p className="text-xs text-muted-foreground">{lead.whatsapp}</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs" style={{ borderColor: STAGE_CONFIG[lead.funnel_stage]?.color, color: STAGE_CONFIG[lead.funnel_stage]?.color }}>
                    {STAGE_CONFIG[lead.funnel_stage]?.label}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
