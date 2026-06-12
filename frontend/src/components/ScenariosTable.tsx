"use client";

import type { ScenarioItem } from "@/lib/api";

interface ScenariosTableProps {
  scenarios: ScenarioItem[];
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

export default function ScenariosTable({ scenarios }: ScenariosTableProps) {
  const maxRevenue = Math.max(...scenarios.map((s) => s.revenue));
  const maxProfit = Math.max(...scenarios.map((s) => s.profit));
  const maxDemand = Math.max(...scenarios.map((s) => s.demand));

  const bestRevenueIdx = scenarios.findIndex((s) => s.revenue === maxRevenue);
  const bestProfitIdx = scenarios.findIndex((s) => s.profit === maxProfit);
  const bestDemandIdx = scenarios.findIndex((s) => s.demand === maxDemand);

  const isCurrentPrice = (s: ScenarioItem) => s.price_change_pct === 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 mb-8">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-lg font-semibold text-slate-800">
          Escenarios de Precio
        </h2>
        <div className="flex gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-sm bg-emerald-100" />
            Mejor Ingreso
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-sm bg-violet-100" />
            Mejor Rentabilidad
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-sm bg-amber-100" />
            Mejor Demanda
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Cambio
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Precio
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Demanda
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Ingreso
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Rentabilidad
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Margen
              </th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Num. Ventas
              </th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s, i) => {
              const isBestRevenue = i === bestRevenueIdx;
              const isBestProfit = i === bestProfitIdx;
              const isBestDemand = i === bestDemandIdx;
              const isCurrent = isCurrentPrice(s);

              let rowBg = "";
              if (isBestRevenue) rowBg = "bg-emerald-50";
              else if (isBestProfit) rowBg = "bg-violet-50";
              else if (isBestDemand) rowBg = "bg-amber-50";

              const changeColor =
                s.price_change_pct > 0
                  ? "text-emerald-600"
                  : s.price_change_pct < 0
                    ? "text-red-500"
                    : "text-slate-600";

              return (
                <tr
                  key={i}
                  className={`border-b border-slate-50 ${rowBg} ${isCurrent ? "font-semibold" : ""}`}
                >
                  <td className="py-2 px-3">
                    <span className={`font-medium ${changeColor}`}>
                      {s.price_change_pct > 0 ? "+" : ""}
                      {s.price_change_pct}%
                    </span>
                    {isCurrent && (
                      <span className="ml-2 text-xs text-slate-400 font-normal">
                        (actual)
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-700">
                    {formatCurrency(s.price)}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-700">
                    {formatNumber(s.demand)}
                    {isBestDemand && (
                      <span className="ml-1 text-amber-500 text-xs">
                        &#9650;
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-700">
                    {formatCurrency(s.revenue)}
                    {isBestRevenue && (
                      <span className="ml-1 text-emerald-500 text-xs">
                        &#9650;
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-700">
                    {formatCurrency(s.profit)}
                    {isBestProfit && (
                      <span className="ml-1 text-violet-500 text-xs">
                        &#9650;
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-500">
                    {s.margin_pct.toFixed(1)}%
                  </td>
                  <td className="py-2 px-3 text-right text-slate-700">
                    {formatNumber(s.demand)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
