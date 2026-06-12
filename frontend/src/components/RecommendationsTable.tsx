"use client";

import type { RecommendationItem, OptimizeObjective } from "@/lib/api";

interface RecommendationsTableProps {
  recommendations: RecommendationItem[];
  objective: OptimizeObjective;
}

const formatCurrency = (v: number) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 1,
  }).format(v);

export default function RecommendationsTable({
  recommendations,
  objective,
}: RecommendationsTableProps) {
  const getSuggestedPrice = (rec: RecommendationItem): number => {
    if (objective === "revenue") return rec.precio_max_revenue;
    if (objective === "profit") return rec.precio_max_profit;
    return (
      rec.precio_max_demand ??
      Math.min(rec.precio_max_revenue, rec.precio_max_profit)
    );
  };

  const getPriceVariation = (rec: RecommendationItem): number => {
    const suggested = getSuggestedPrice(rec);
    return ((suggested - rec.precio_actual) / rec.precio_actual) * 100;
  };

  const getAction = (
    rec: RecommendationItem,
  ): { label: string; color: string } => {
    const variation = getPriceVariation(rec);
    if (Math.abs(variation) < 1) return { label: "Mantener", color: "#64748b" };
    return variation > 0
      ? { label: "Subir precio", color: "#059669" }
      : { label: "Bajar precio", color: "#dc2626" };
  };

  const objectiveLabel: Record<OptimizeObjective, string> = {
    revenue: "Ingreso",
    profit: "Rentabilidad",
    demand: "Demanda",
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 mb-8">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-lg font-semibold text-slate-800">
          Recomendaciones por Producto
        </h2>
        <span className="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded">
          Precio sugerido optimizado por:{" "}
          <strong className="text-slate-600">
            {objectiveLabel[objective]}
          </strong>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Producto
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Precio Actual
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Variación
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Precio Sugerido ({objectiveLabel[objective]})
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Elasticidad
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                LTV Promedio
              </th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Acción
              </th>
            </tr>
          </thead>
          <tbody>
            {recommendations.map((rec) => {
              const suggested = getSuggestedPrice(rec);
              const variation = getPriceVariation(rec);
              const action = getAction(rec);
              const isElastic = Math.abs(rec.elasticidad) > 1;
              const ltvColor: Record<string, string> = {
                Alto: "#059669",
                Medio: "#d97706",
                Bajo: "#dc2626",
              };
              const ltvBg: Record<string, string> = {
                Alto: "#d1fae5",
                Medio: "#fef3c7",
                Bajo: "#fee2e2",
              };

              return (
                <tr
                  key={rec.ProductID}
                  className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                >
                  <td className="py-2 px-3">
                    <span className="font-medium text-slate-800">
                      {rec.ProductID}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-slate-600">
                    {formatCurrency(rec.precio_actual)}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span
                      className="font-medium text-xs px-2 py-0.5 rounded-full"
                      style={{
                        color:
                          variation > 0
                            ? "#059669"
                            : variation < 0
                              ? "#dc2626"
                              : "#64748b",
                        backgroundColor:
                          variation > 0
                            ? "#d1fae5"
                            : variation < 0
                              ? "#fee2e2"
                              : "#f1f5f9",
                      }}
                    >
                      {variation > 0 ? "+" : ""}
                      {variation.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-semibold text-slate-800">
                    {formatCurrency(suggested)}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{
                        color: isElastic ? "#d97706" : "#0055b3",
                        backgroundColor: isElastic ? "#fef3c7" : "#dbeafe",
                      }}
                    >
                      {rec.elasticidad.toFixed(2)}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    {rec.avg_ltv != null && rec.ltv_segment ? (
                      <div className="flex flex-col items-end gap-0.5">
                        <span className="text-slate-700 text-xs">
                          {formatCurrency(rec.avg_ltv)}
                        </span>
                        <span
                          className="text-xs font-semibold px-2 py-0.5 rounded-full"
                          style={{
                            color: ltvColor[rec.ltv_segment] ?? "#64748b",
                            backgroundColor:
                              ltvBg[rec.ltv_segment] ?? "#f1f5f9",
                          }}
                        >
                          {rec.ltv_segment}
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-300 text-xs">—</span>
                    )}
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className="text-xs font-semibold"
                      style={{ color: action.color }}
                    >
                      {action.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Elasticidad &gt; 1: demanda sensible al precio. Elasticidad &lt; 1:
        demanda insensible al precio.
      </p>
    </div>
  );
}
