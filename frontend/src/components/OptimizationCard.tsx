interface OptimizationCardProps {
  optimization: {
    optimal_price: number;
    current_price: number;
    price_change_pct: number;
    predicted_demand: number;
    expected_revenue: number;
    expected_profit: number;
    margin_pct: number;
  };
  objective: "revenue" | "profit";
}

export default function OptimizationCard({
  optimization,
  objective,
}: OptimizationCardProps) {
  const isIncrease = optimization.price_change_pct > 0;
  const action = isIncrease ? "Subir" : "Bajar";
  const actionColor = isIncrease ? "text-red-600" : "text-green-600";
  const arrowIcon = isIncrease ? "📈" : "📉";

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-2xl font-bold text-gray-900">💡 Precio Óptimo</h2>
        <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
          Objetivo: {objective === "profit" ? "Profit" : "Revenue"}
        </span>
      </div>

      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="text-gray-600 text-sm mb-1">Precio Actual</p>
            <p className="text-3xl font-bold text-gray-900">
              ${optimization.current_price.toFixed(2)}
            </p>
          </div>
          <div className="text-4xl">{arrowIcon}</div>
          <div>
            <p className="text-gray-600 text-sm mb-1">Precio Sugerido</p>
            <p className="text-3xl font-bold text-purple-600">
              ${optimization.optimal_price.toFixed(2)}
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-purple-200">
          <p className="text-center">
            <span className="text-gray-700">Recomendación: </span>
            <span className={`font-bold ${actionColor}`}>
              {action} precio{" "}
              {Math.abs(optimization.price_change_pct).toFixed(1)}%
            </span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-gray-600 text-sm mb-1">Demanda Esperada</p>
          <p className="text-2xl font-bold text-gray-900">
            {optimization.predicted_demand.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">unidades</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-gray-600 text-sm mb-1">Margen</p>
          <p className="text-2xl font-bold text-gray-900">
            {optimization.margin_pct.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">profit margin</p>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-gray-600 text-sm mb-1">Revenue Esperado</p>
          <p className="text-2xl font-bold text-green-600">
            ${optimization.expected_revenue.toFixed(2)}
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-gray-600 text-sm mb-1">Profit Esperado</p>
          <p className="text-2xl font-bold text-purple-600">
            ${optimization.expected_profit.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          <span className="font-semibold">⚠️ Nota:</span> Esta es una sugerencia
          basada en el modelo. Considera factores externos como competencia,
          estacionalidad y estrategia de marca.
        </p>
      </div>
    </div>
  );
}
