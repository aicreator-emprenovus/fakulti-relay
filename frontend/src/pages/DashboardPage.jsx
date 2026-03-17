import React, { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, DollarSign, ShoppingCart, Gamepad2, TrendingUp, UserCheck, Award, Target, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

function formatPhoneEC(phone) {
  if (!phone) return "";
  let cleaned = phone.replace(/[\s\-()]/g, "");
  if (cleaned.startsWith("+593")) cleaned = "0" + cleaned.slice(4);
  else if (cleaned.startsWith("593") && cleaned.length > 9) cleaned = "0" + cleaned.slice(3);
  return cleaned;
}

const STAGE_CONFIG = {
  nuevo: { label: "Contacto inicial", color: "#3B82F6" },
  interesado: { label: "Chat", color: "#8B5CF6" },
  en_negociacion: { label: "En Negociación", color: "#F59E0B" },
  cliente_nuevo: { label: "Leads ganados", color: "#10B981" },
  cliente_activo: { label: "Cartera activa", color: "#A3E635" },
  perdido: { label: "Perdido", color: "#64748B" },
};

const CHART_COLORS = ["#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981", "#EF4444"];

export default function DashboardPage() {
  const { user } = useAuth();
  const userRole = user?.role || "admin";
  const [stats, setStats] = useState(null);
  const [advisorStats, setAdvisorStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("general");

  useEffect(() => {
    const fetches = [axios.get(`${API}/dashboard/stats`)];
    if (userRole === "admin") fetches.push(axios.get(`${API}/dashboard/advisor-stats`));
    Promise.all(fetches).then(results => {
      setStats(results[0].data);
      if (results[1]) setAdvisorStats(results[1].data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [userRole]);

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Cargando dashboard...</div>;
  if (!stats) return <div className="text-muted-foreground">Error al cargar estadísticas</div>;

  const funnelData = Object.entries(stats.stages).map(([key, value]) => ({
    name: STAGE_CONFIG[key]?.label || key, value, color: STAGE_CONFIG[key]?.color || "#64748B", key
  }));

  const statCards = [
    { label: "Total Leads", value: stats.total_leads, icon: Users, color: "text-blue-400" },
    { label: "Ventas Totales", value: `$${stats.total_sales}`, icon: DollarSign, color: "text-lime-400" },
    { label: "Órdenes", value: stats.total_orders, icon: ShoppingCart, color: "text-amber-400" },
    { label: "Clientes", value: stats.total_clients, icon: UserCheck, color: "text-emerald-400" },
    { label: "Juegos Jugados", value: stats.game_plays, icon: Gamepad2, color: "text-purple-400" },
    { label: "Conversión", value: `${stats.conversion_rate}%`, icon: TrendingUp, color: "text-lime-400" },
  ];

  return (
    <div data-testid="dashboard-page" className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground font-heading">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Resumen general del CRM Fakulti</p>
        </div>
      </div>

      {userRole === "admin" && advisorStats && (
        <div className="flex gap-2 border-b border-border">
          <button onClick={() => setTab("general")} className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === "general" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`} data-testid="tab-general">General</button>
          <button onClick={() => setTab("advisors")} className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === "advisors" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`} data-testid="tab-advisors">Por Asesor</button>
        </div>
      )}

      {tab === "general" && (
        <>
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
              <CardHeader className="pb-2"><CardTitle className="text-lg text-foreground">Embudo de Ventas</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {funnelData.map((stage, i) => {
                    const maxVal = Math.max(...funnelData.map(s => s.value), 1);
                    const pct = (stage.value / maxVal) * 100;
                    return (
                      <div key={stage.key} className="flex items-center gap-3" data-testid={`funnel-stage-${stage.key}`}>
                        <span className="text-xs text-muted-foreground w-28 truncate">{stage.name}</span>
                        <div className="flex-1 h-8 bg-muted rounded-lg overflow-hidden relative">
                          <div className="h-full rounded-lg transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: stage.color }} />
                          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-foreground">{stage.value}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border rounded-2xl">
              <CardHeader className="pb-2"><CardTitle className="text-lg text-foreground">Ventas por Producto</CardTitle></CardHeader>
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
                ) : <div className="h-48 flex items-center justify-center text-muted-foreground">Sin datos de ventas aun</div>}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border rounded-2xl">
              <CardHeader className="pb-2"><CardTitle className="text-lg text-foreground">Fuentes de Tráfico</CardTitle></CardHeader>
              <CardContent>
                {stats.source_stats.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={stats.source_stats} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, count }) => `${name}: ${count}`}>
                        {stats.source_stats.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))" }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : <div className="h-48 flex items-center justify-center text-muted-foreground">Sin datos de fuentes</div>}
              </CardContent>
            </Card>

            <Card className="bg-card border-border rounded-2xl">
              <CardHeader className="pb-2"><CardTitle className="text-lg text-foreground">Leads Recientes</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {stats.recent_leads.map(lead => (
                    <div key={lead.id} className="flex items-center justify-between p-2 rounded-lg bg-muted/50 hover:bg-muted">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: STAGE_CONFIG[lead.funnel_stage]?.color + "20", color: STAGE_CONFIG[lead.funnel_stage]?.color }}>{lead.name?.[0]}</div>
                        <div>
                          <p className="text-sm text-foreground font-medium">{lead.name}</p>
                          <p className="text-xs text-muted-foreground">{formatPhoneEC(lead.whatsapp)}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-xs" style={{ borderColor: STAGE_CONFIG[lead.funnel_stage]?.color, color: STAGE_CONFIG[lead.funnel_stage]?.color }}>{STAGE_CONFIG[lead.funnel_stage]?.label}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {tab === "advisors" && advisorStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="stat-card p-4" data-testid="adv-stat-total">
              <div className="flex items-center gap-2 mb-1"><UserCheck size={14} className="text-amber-500" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Asesores</span></div>
              <p className="text-2xl font-bold text-foreground">{advisorStats.summary.total_advisors}</p>
            </div>
            <div className="stat-card p-4" data-testid="adv-stat-assigned">
              <div className="flex items-center gap-2 mb-1"><Target size={14} className="text-blue-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Leads Asignados</span></div>
              <p className="text-2xl font-bold text-foreground">{advisorStats.summary.total_assigned}</p>
            </div>
            <div className="stat-card p-4" data-testid="adv-stat-unassigned">
              <div className="flex items-center gap-2 mb-1"><AlertTriangle size={14} className="text-red-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Sin Asignar</span></div>
              <p className="text-2xl font-bold text-foreground">{advisorStats.summary.total_unassigned}</p>
            </div>
            <div className="stat-card p-4" data-testid="adv-stat-revenue">
              <div className="flex items-center gap-2 mb-1"><DollarSign size={14} className="text-lime-400" /><span className="text-xs text-muted-foreground uppercase tracking-wider">Revenue Asesores</span></div>
              <p className="text-2xl font-bold text-foreground">${advisorStats.summary.total_revenue_by_advisors}</p>
            </div>
          </div>

          {advisorStats.advisors.length > 0 ? (
            <>
              <Card className="bg-card border-border rounded-2xl">
                <CardHeader className="pb-2"><CardTitle className="text-lg text-foreground">Rendimiento por Asesor</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={advisorStats.advisors} layout="vertical">
                      <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} width={120} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))", fontSize: 12 }} />
                      <Bar dataKey="won_leads" name="Ganados" fill="#10B981" stackId="a" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="negotiating" name="Negociación" fill="#F59E0B" stackId="a" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="lost_leads" name="Perdidos" fill="#64748B" stackId="a" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {advisorStats.advisors.map((a, i) => (
                  <Card key={a.id} data-testid={`advisor-stat-${a.id}`} className="bg-card border-border rounded-xl">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + "20", color: CHART_COLORS[i % CHART_COLORS.length] }}>{a.name[0]}</div>
                        <div>
                          <h3 className="text-sm font-semibold text-foreground">{a.name}</h3>
                          <p className="text-xs text-muted-foreground">{a.specialization || a.email}</p>
                        </div>
                        <Badge className={`ml-auto text-[10px] ${a.status === "disponible" ? "bg-green-500/15 text-green-500" : a.status === "ocupado" ? "bg-amber-500/15 text-amber-500" : "bg-muted text-muted-foreground"}`}>
                          {a.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-center">
                        <div className="p-2 bg-muted/30 rounded-lg">
                          <p className="text-lg font-bold text-foreground">{a.total_leads}</p>
                          <p className="text-[10px] text-muted-foreground">Leads</p>
                        </div>
                        <div className="p-2 bg-muted/30 rounded-lg">
                          <p className="text-lg font-bold text-green-500">{a.won_leads}</p>
                          <p className="text-[10px] text-muted-foreground">Ganados</p>
                        </div>
                        <div className="p-2 bg-muted/30 rounded-lg">
                          <p className="text-lg font-bold text-primary">${a.revenue}</p>
                          <p className="text-[10px] text-muted-foreground">Revenue</p>
                        </div>
                        <div className="p-2 bg-muted/30 rounded-lg">
                          <p className="text-lg font-bold" style={{ color: CHART_COLORS[i % CHART_COLORS.length] }}>{a.conversion_rate}%</p>
                          <p className="text-[10px] text-muted-foreground">Conversión</p>
                        </div>
                      </div>
                      {a.active_chats > 0 && (
                        <p className="text-[10px] text-amber-500 mt-2 text-center">{a.active_chats} conversación(es) en modo humano</p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">No hay asesores registrados. Crea el primero en "Asesores".</div>
          )}
        </div>
      )}
    </div>
  );
}
