"use client";

import type { OptimizeResponse, OptimizeObjective } from "@/lib/api";

interface OptimalPriceCardProps {
  optimization: OptimizeResponse;
  objective: OptimizeObjective;
  onObjectiveChange: (obj: OptimizeObjective) => void;
  loading?: boolean;
}

const formatCurrency = (v: number) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 1,
  }).format(v);

const formatNumber = (v: number) =>
  new Intl.NumberFormat("es-CO", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(v);

const OBJECTIVES: { value: OptimizeObjective; label: string }[] = [
  { value: "revenue", label: "Ingreso" },
  { value: "profit", label: "Rentabilidad" },
  { value: "demand", label: "Demanda" },
];

const OBJECTIVE_COLORS: Record<OptimizeObjective, string> = {
  revenue: "#059669",
  profit: "#7c3aed",
  demand: "#d97706",
};

export default function OptimalPriceCard({
  optimization,
  objective,
  onObjectiveChange,
  loading,
}: OptimalPriceCardProps) {
  if (!optimization && !loading) return null;

  const priceIncreased = optimization
    ? optimization.optimal_price > optimization.current_price
    : false;
  const priceChanged = optimization
    ? Math.abs(optimization.price_change_pct) > 0.1
    : false;
  const direction = priceIncreased ? "Subir" : "Bajar";
  const accentColor = OBJECTIVE_COLORS[objective];

  const kpis = optimization
    ? [
        {
          label: "Objetivo",
          value:
            OBJECTIVES.find((o) => o.value === objective)?.label ?? objective,
          highlight: true,
        },
        {
          label: "Precio Actual",
          value: formatCurrency(optimization.current_price),
        },
        {
          label: "Precio Sugerido",
          value: formatCurrency(optimization.optimal_price),
          badge: priceChanged
            ? `${optimization.price_change_pct > 0 ? "+" : ""}${optimization.price_change_pct.toFixed(1)}%`
            : null,
          badgeColor: priceIncreased ? "#059669" : "#dc2626",
        },
        {
          label: "Recomendación",
          value: priceChanged ? `${direction} precio` : "Mantener precio",
        },
        {
          label: "Demanda Esperada",
          value: formatNumber(optimization.predicted_demand),
        },
        {
          label: "Rentabilidad Esperada",
          value: formatCurrency(optimization.expected_profit),
        },
        {
          label: "Ingreso Esperado",
          value: formatCurrency(optimization.expected_revenue),
        },
      ]
    : [];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 mb-8">
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <h2 className="text-lg font-semibold text-slate-800">Precio Óptimo</h2>
        <div
          className="flex gap-1 rounded-lg p-1"
          style={{ backgroundColor: "#f1f5f9" }}
        >
          {OBJECTIVES.map((obj) => (
            <button
              key={obj.value}
              onClick={() => onObjectiveChange(obj.value)}
              className="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
              style={
                objective === obj.value
                  ? {
                      backgroundColor: OBJECTIVE_COLORS[obj.value],
                      color: "white",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
                    }
                  : { color: "#64748b" }
              }
            >
              {obj.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div
            className="animate-spin rounded-full h-8 w-8 border-b-2"
            style={{ borderColor: accentColor }}
          />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {kpis.map((kpi, i) => (
            <div
              key={i}
              className="rounded-xl p-4"
              style={{
                backgroundColor: kpi.highlight ? `${accentColor}15` : "#f8fafc",
                border: kpi.highlight
                  ? `1px solid ${accentColor}40`
                  : "1px solid #e2e8f0",
              }}
            >
              <p
                className="text-xs font-semibold uppercase tracking-wide mb-1"
                style={{ color: "#94a3b8" }}
              >
                {kpi.label}
              </p>
              <p
                className="text-sm font-bold leading-snug"
                style={{ color: kpi.highlight ? accentColor : "#1e293b" }}
              >
                {kpi.value}
              </p>
              {kpi.badge && (
                <span
                  className="inline-block mt-1 text-xs font-semibold px-1.5 py-0.5 rounded"
                  style={{
                    backgroundColor: `${kpi.badgeColor}20`,
                    color: kpi.badgeColor,
                  }}
                >
                  {kpi.badge}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
