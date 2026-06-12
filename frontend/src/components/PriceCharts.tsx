"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ComposedChart,
  ReferenceLine,
} from "recharts";
import type { ElasticityResponse, ScenariosResponse } from "@/lib/api";

interface PriceChartsProps {
  elasticityData: ElasticityResponse;
  scenariosData: ScenariosResponse;
}

const CHART_COLORS = {
  elasticity: "#0055b3",
  revenue: "#059669",
  profit: "#7c3aed",
  demand: "#d97706",
  revenueBar: "#10b981",
  profitBar: "#8b5cf6",
  demandLine: "#f59e0b",
};

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
      <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-4">
        {title}
      </h3>
      {children}
    </div>
  );
}

const formatCurrency = (v: number) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 1,
  }).format(v);

const formatNumber = (v: number) =>
  new Intl.NumberFormat("es-CO").format(Math.round(v));

export default function PriceCharts({
  elasticityData,
  scenariosData,
}: PriceChartsProps) {
  // Build elasticity chart data (price vs demand from elasticity endpoint)
  const elasticityChartData = elasticityData.prices.map((price, i) => ({
    price: price.toFixed(0),
    demanda: Math.round(elasticityData.demands[i]),
  }));

  // Build scenario chart data
  const scenarioChartData = scenariosData.scenarios.map((s) => ({
    cambio: `${s.price_change_pct > 0 ? "+" : ""}${s.price_change_pct}%`,
    precio: Number(s.price.toFixed(2)),
    demanda: Math.round(s.demand),
    revenue: Math.round(s.revenue),
    profit: Math.round(s.profit),
    margin: Number(s.margin_pct.toFixed(1)),
  }));

  // Normalized data for combined chart (0-100% of each metric's max)
  const maxRevenue = Math.max(...scenarioChartData.map((d) => d.revenue));
  const maxProfit = Math.max(
    ...scenarioChartData.map((d) => Math.max(d.profit, 0)),
  );
  const maxDemanda = Math.max(...scenarioChartData.map((d) => d.demanda));

  const combinedChartData = scenarioChartData.map((d) => ({
    cambio: d.cambio,
    "Ingreso (%)":
      maxRevenue > 0 ? Number(((d.revenue / maxRevenue) * 100).toFixed(1)) : 0,
    "Rentabilidad (%)":
      maxProfit > 0
        ? Number(((Math.max(d.profit, 0) / maxProfit) * 100).toFixed(1))
        : 0,
    "Demanda (%)":
      maxDemanda > 0 ? Number(((d.demanda / maxDemanda) * 100).toFixed(1)) : 0,
  }));

  const currentPriceLabel = scenariosData.scenarios.find(
    (s) => s.price_change_pct === 0,
  )
    ? "0%"
    : undefined;

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">
        Análisis de Precios
      </h2>

      {/* Row 1: Elasticidad + Ingreso */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Elasticidad Precio-Demanda">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={elasticityChartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="price"
                tick={{ fontSize: 11, fill: "#64748b" }}
                label={{
                  value: "Precio",
                  position: "insideBottomRight",
                  offset: -4,
                  fontSize: 11,
                  fill: "#94a3b8",
                }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={formatNumber}
                width={60}
              />
              <Tooltip
                formatter={(v: number) => [formatNumber(v), "Demanda"]}
                labelFormatter={(l) => `Precio: ${l}`}
                contentStyle={{ borderRadius: 8, fontSize: 12 }}
              />
              <Line
                type="monotone"
                dataKey="demanda"
                stroke={CHART_COLORS.elasticity}
                strokeWidth={2.5}
                dot={false}
                name="Demanda"
              />
              <ReferenceLine
                x={elasticityData.current_price.toFixed(0)}
                stroke="#94a3b8"
                strokeDasharray="4 2"
                label={{ value: "Actual", fontSize: 10, fill: "#94a3b8" }}
              />
            </LineChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-500 mt-1">
            Elasticidad:{" "}
            <span className="font-semibold text-slate-700">
              {elasticityData.elasticity.toFixed(3)}
            </span>{" "}
            (
            {elasticityData.elasticity_type === "elastic"
              ? "Elástica"
              : "Inelástica"}
            )
          </p>
        </ChartCard>

        <ChartCard title="Ingreso vs Precio">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={scenarioChartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="cambio"
                tick={{ fontSize: 11, fill: "#64748b" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
                width={52}
              />
              <Tooltip
                formatter={(v: number) => [formatCurrency(v), "Ingreso"]}
                contentStyle={{ borderRadius: 8, fontSize: 12 }}
              />
              {currentPriceLabel && (
                <ReferenceLine
                  x={currentPriceLabel}
                  stroke="#94a3b8"
                  strokeDasharray="4 2"
                />
              )}
              <Line
                type="monotone"
                dataKey="revenue"
                stroke={CHART_COLORS.revenue}
                strokeWidth={2.5}
                dot={{ r: 3, fill: CHART_COLORS.revenue }}
                name="Ingreso"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2: Rentabilidad + Demanda */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Rentabilidad vs Precio">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={scenarioChartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="cambio"
                tick={{ fontSize: 11, fill: "#64748b" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
                width={52}
              />
              <Tooltip
                formatter={(v: number) => [formatCurrency(v), "Rentabilidad"]}
                contentStyle={{ borderRadius: 8, fontSize: 12 }}
              />
              {currentPriceLabel && (
                <ReferenceLine
                  x={currentPriceLabel}
                  stroke="#94a3b8"
                  strokeDasharray="4 2"
                />
              )}
              <Line
                type="monotone"
                dataKey="profit"
                stroke={CHART_COLORS.profit}
                strokeWidth={2.5}
                dot={{ r: 3, fill: CHART_COLORS.profit }}
                name="Rentabilidad"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Demanda vs Precio">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={scenarioChartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="cambio"
                tick={{ fontSize: 11, fill: "#64748b" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={formatNumber}
                width={60}
              />
              <Tooltip
                formatter={(v: number) => [formatNumber(v), "Demanda"]}
                contentStyle={{ borderRadius: 8, fontSize: 12 }}
              />
              {currentPriceLabel && (
                <ReferenceLine
                  x={currentPriceLabel}
                  stroke="#94a3b8"
                  strokeDasharray="4 2"
                />
              )}
              <Line
                type="monotone"
                dataKey="demanda"
                stroke={CHART_COLORS.demand}
                strokeWidth={2.5}
                dot={{ r: 3, fill: CHART_COLORS.demand }}
                name="Demanda"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 3: Combined stacked/grouped chart */}
      <ChartCard title="Ingreso, Rentabilidad y Demanda vs Precio (% del máximo)">
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart
            data={combinedChartData}
            margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="cambio" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(v) => `${v}%`}
              domain={[0, 100]}
              width={48}
            />
            <Tooltip
              formatter={(v: number, name: string) => [
                `${v.toFixed(1)}%`,
                name,
              ]}
              contentStyle={{ borderRadius: 8, fontSize: 12 }}
            />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
            {currentPriceLabel && (
              <ReferenceLine
                x={currentPriceLabel}
                stroke="#94a3b8"
                strokeDasharray="4 2"
                label={{ value: "Actual", fontSize: 10, fill: "#94a3b8" }}
              />
            )}
            <Bar
              dataKey="Ingreso (%)"
              fill={CHART_COLORS.revenueBar}
              radius={[3, 3, 0, 0]}
              maxBarSize={32}
            />
            <Bar
              dataKey="Rentabilidad (%)"
              fill={CHART_COLORS.profitBar}
              radius={[3, 3, 0, 0]}
              maxBarSize={32}
            />
            <Line
              type="monotone"
              dataKey="Demanda (%)"
              stroke={CHART_COLORS.demandLine}
              strokeWidth={2.5}
              dot={{ r: 3, fill: CHART_COLORS.demandLine }}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="text-xs text-slate-400 mt-1">
          Valores normalizados como porcentaje del máximo de cada métrica.
        </p>
      </ChartCard>
    </div>
  );
}
