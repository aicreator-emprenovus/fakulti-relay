import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Heart, BarChart3, Repeat, TrendingUp, DollarSign, Users, ShieldCheck, MessageSquare, Bot, Send, Target } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const FUNNEL_COLORS = {
  "Contacto inicial": "#3B82F6",
  "Chat": "#8B5CF6",
  "En Negociación": "#F59E0B",
  "Leads ganados": "#10B981",
  "Cartera activa": "#059669",
  "Perdido": "#EF4444",
};

const CHART_COLORS = ["#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981", "#EF4444", "#64748B"];

export default function LoyaltyPage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    axios.get(`${API}/loyalty/metrics`).then(res => {
      setMetrics(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-muted-foreground text-center py-12">Cargando...</div>;
  if (!metrics) return <div className="text-center py-12 text-muted-foreground">Sin métricas disponibles</div>;

  const { summary, funnel_distribution, product_interest, source_distribution, loyalty, sequence_effectiveness, campaigns, product_revenue, top_buyers } = metrics;

  const funnelChartData = (funnel_distribution || []).map(d => ({
    ...d, color: FUNNEL_COLORS[d.stage] || "#64748B"
  }));

  const retentionData = [
    { name: "Convertidos", value: summary.converted, color: "#10B981" },
    { name: "En progreso", value: summary.in_progress, color: "#F59E0B" },
    { name: "Perdidos", value: summary.lost, color: "#EF4444" },
  ].filter(d => d.value > 0);

  return (
    <div data-testid="loyalty-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Fidelización</h1>
        <p className="text-sm text-muted-foreground">Métricas de generación de leads mediante el Bot de WhatsApp</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: "Total Leads", value: summary.total_leads, icon: Users, color: "text-blue-400" },
          { label: "Conversión", value: `${summary.conversion_rate}%`, icon: TrendingUp, color: "text-emerald-400" },
          { label: "Conversaciones", value: summary.total_sessions, icon: MessageSquare, color: "text-purple-400" },
          { label: "Mensajes Bot", value: summary.bot_messages, icon: Bot, color: "text-lime-400" },
          { label: "Msg. Usuarios", value: summary.user_messages, icon: MessageSquare, color: "text-amber-400" },
          { label: "Envíos Campaña", value: summary.total_campaign_sends, icon: Send, color: "text-pink-400" },
        ].map((c, i) => (
          <div key={i} className="stat-card p-4" data-testid={`metric-${c.label.toLowerCase().replace(/ /g, "-")}`}>
            <div className="flex items-center gap-1.5 mb-1">
              <c.icon size={13} className={c.color} />
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{c.label}</span>
            </div>
            <p className="text-xl font-bold text-foreground font-accent">{c.value}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funnel Distribution */}
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Distribución del Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            {funnelChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={funnelChartData}>
                  <XAxis dataKey="stage" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))", fontSize: 12 }} />
                  <Bar dataKey="count" name="Leads" radius={[4, 4, 0, 0]}>
                    {funnelChartData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-muted-foreground text-center py-8">Sin datos de funnel</p>}
          </CardContent>
        </Card>

        {/* Retention Pie */}
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Estado de Leads</CardTitle>
          </CardHeader>
          <CardContent>
            {retentionData.length > 0 ? (
              <div className="flex items-center gap-6">
                <ResponsiveContainer width="50%" height={180}>
                  <PieChart>
                    <Pie data={retentionData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={4}>
                      {retentionData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))", fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-3">
                  {retentionData.map((d, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
                      <span className="text-sm text-muted-foreground">{d.name}:</span>
                      <span className="text-sm text-foreground font-semibold">{d.value}</span>
                    </div>
                  ))}
                  <p className="text-xs text-muted-foreground mt-2">Tasa de conversión: <span className="text-primary font-bold">{summary.conversion_rate}%</span></p>
                </div>
              </div>
            ) : <p className="text-sm text-muted-foreground text-center py-8">Sin datos</p>}
          </CardContent>
        </Card>
      </div>

      {/* Product Interest */}
      {(product_interest || []).length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Interés por Producto</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {product_interest.map((p, i) => (
                <div key={i} className="flex items-center gap-3" data-testid={`product-interest-${i}`}>
                  <span className="text-xs text-muted-foreground w-40 truncate">{p.product}</span>
                  <div className="flex-1 h-6 bg-muted rounded-lg overflow-hidden relative">
                    <div className="h-full rounded-lg transition-all duration-500" style={{ width: `${Math.max((p.leads / summary.total_leads) * 100, 5)}%`, backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-foreground">{p.leads} leads</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Revenue by Product (only if purchase data exists) */}
      {(product_revenue || []).length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Revenue por Producto</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={product_revenue} layout="vertical">
                <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="product" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 9 }} width={120} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))", fontSize: 12 }} formatter={(v) => [`$${v}`, "Revenue"]} />
                <Bar dataKey="revenue" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Loyalty Sequences */}
      {(sequence_effectiveness || []).length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Secuencias de Fidelización</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="stat-card p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase">Inscripciones</p>
                <p className="text-lg font-bold text-foreground">{loyalty.total_enrollments}</p>
              </div>
              <div className="stat-card p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase">Completadas</p>
                <p className="text-lg font-bold text-emerald-400">{loyalty.completed_enrollments}</p>
              </div>
              <div className="stat-card p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase">Msgs Enviados</p>
                <p className="text-lg font-bold text-blue-400">{loyalty.sent_messages}/{loyalty.total_messages}</p>
              </div>
            </div>
            <div className="space-y-2">
              {sequence_effectiveness.map((s, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30 border border-border" data-testid={`seq-${i}`}>
                  <span className="text-sm text-foreground font-medium truncate flex-1">{s.name}</span>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-[10px]">{s.enrollments} inscritos</Badge>
                    <Badge variant="outline" className="text-[10px] text-emerald-400">{s.completion_rate}% completado</Badge>
                    <Badge variant="outline" className="text-[10px] text-blue-400">{s.delivery_rate}% entrega</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Campaigns Performance */}
      {(campaigns || []).length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Rendimiento de Campañas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Campaña</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Enviados</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Fallidos</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c, i) => (
                    <tr key={i} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="p-2 text-foreground font-medium">{c.name}</td>
                      <td className="p-2 text-emerald-400 font-bold">{c.sent}</td>
                      <td className="p-2 text-red-400">{c.failed}</td>
                      <td className="p-2"><Badge variant="outline" className={`text-[10px] ${c.status === "sent" ? "text-emerald-400" : ""}`}>{c.status === "sent" ? "Enviada" : c.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Buyers (only shown if purchase data exists) */}
      {(top_buyers || []).length > 0 && (
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Top Compradores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">#</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Cliente</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Compras</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Total Gastado</th>
                    <th className="text-left p-2 text-muted-foreground font-medium text-xs">Etapa</th>
                  </tr>
                </thead>
                <tbody>
                  {top_buyers.map((b, i) => (
                    <tr key={i} className="border-b border-border/30 hover:bg-muted/30" data-testid={`top-buyer-${i}`}>
                      <td className="p-2 text-muted-foreground">{i + 1}</td>
                      <td className="p-2 text-foreground font-medium">{b.name}</td>
                      <td className="p-2 text-muted-foreground">{b.purchases}</td>
                      <td className="p-2 text-primary font-bold">${b.total_spent}</td>
                      <td className="p-2"><Badge variant="outline" className="text-[10px]">{b.stage}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
