import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Heart, BarChart3, Repeat, TrendingUp, DollarSign, Users, ShieldCheck } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const CHART_COLORS = ["#A3E635", "#3B82F6", "#F59E0B", "#8B5CF6", "#10B981", "#EF4444", "#64748B"];

function MetricsDashboard({ metrics }) {
  const { summary, product_revenue, product_repeat, top_buyers } = metrics;

  const retentionData = [
    { name: "Activos", value: summary.active_clients, color: "#10B981" },
    { name: "Perdidos", value: summary.lost_clients, color: "#64748B" },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6" data-testid="metrics-dashboard">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: "Clientes", value: summary.total_clients, icon: Users, color: "text-blue-400" },
          { label: "Recompra", value: `${summary.repeat_rate}%`, icon: Repeat, color: "text-lime-400" },
          { label: "Retención", value: `${summary.retention_rate}%`, icon: ShieldCheck, color: "text-emerald-400" },
          { label: "Revenue Total", value: `$${summary.total_revenue}`, icon: DollarSign, color: "text-amber-400" },
          { label: "Ticket Promedio", value: `$${summary.avg_order_value}`, icon: TrendingUp, color: "text-purple-400" },
          { label: "Compras/Cliente", value: summary.avg_purchases_per_client, icon: BarChart3, color: "text-pink-400" },
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Revenue por Producto</CardTitle>
          </CardHeader>
          <CardContent>
            {product_revenue.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={product_revenue} layout="vertical">
                  <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="product" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 9 }} width={120} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--foreground))", fontSize: 12 }} formatter={(v) => [`$${v}`, "Revenue"]} />
                  <Bar dataKey="revenue" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-muted-foreground text-center py-8">Sin datos de ventas</p>}
          </CardContent>
        </Card>

        <Card className="bg-card border-border rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-foreground">Retención de Clientes</CardTitle>
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
                  <p className="text-xs text-muted-foreground mt-2">Tasa de retención: <span className="text-primary font-bold">{summary.retention_rate}%</span></p>
                </div>
              </div>
            ) : <p className="text-sm text-muted-foreground text-center py-8">Sin datos de clientes</p>}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border-border rounded-2xl">
        <CardHeader className="pb-2">
          <CardTitle className="text-base text-foreground">Tasa de Recompra por Producto</CardTitle>
        </CardHeader>
        <CardContent>
          {product_repeat.length > 0 ? (
            <div className="space-y-3">
              {product_repeat.map((p, i) => (
                <div key={i} className="flex items-center gap-3" data-testid={`product-repeat-${i}`}>
                  <span className="text-xs text-muted-foreground w-32 truncate">{p.product}</span>
                  <div className="flex-1 h-6 bg-muted rounded-lg overflow-hidden relative">
                    <div className="h-full rounded-lg transition-all duration-500" style={{ width: `${Math.max(p.repeat_rate, 2)}%`, backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-foreground">{p.repeat_rate}%</span>
                  </div>
                  <span className="text-xs text-muted-foreground w-20">{p.repeat_buyers}/{p.total_buyers} rep.</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted-foreground text-center py-8">Sin datos de recompra</p>}
        </CardContent>
      </Card>

      {top_buyers.length > 0 && (
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

  return (
    <div data-testid="loyalty-page" className="space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-3xl font-bold text-foreground font-heading">Fidelización</h1>
        <p className="text-sm text-muted-foreground">Métricas de generación de leads mediante el Bot de WhatsApp</p>
      </div>

      {metrics ? <MetricsDashboard metrics={metrics} /> : (
        <div className="text-center py-12 text-muted-foreground">Sin métricas disponibles</div>
      )}
    </div>
  );
}
