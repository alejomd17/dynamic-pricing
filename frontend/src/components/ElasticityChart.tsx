"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ElasticityChartProps {
  data: {
    prices: number[];
    demands: number[];
  };
  elasticity: number;
  currentPrice: number;
}

export default function ElasticityChart({
  data,
  elasticity,
  currentPrice,
}: ElasticityChartProps) {
  const chartData = data.prices.map((price, index) => ({
    price: price.toFixed(2),
    demand: data.demands[index].toFixed(2),
  }));

  const elasticityType = Math.abs(elasticity) > 1 ? "Elástica" : "Inelástica";
  const elasticityColor =
    Math.abs(elasticity) > 1 ? "text-orange-600" : "text-blue-600";

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          📈 Elasticidad Precio-Demanda
        </h2>
        <div className="flex items-center gap-4">
          <div>
            <span className="text-gray-600">Elasticidad: </span>
            <span className={`text-xl font-bold ${elasticityColor}`}>
              {elasticity.toFixed(3)}
            </span>
          </div>
          <div className="px-3 py-1 bg-gray-100 rounded-full">
            <span className="text-sm font-medium text-gray-700">
              Demanda {elasticityType}
            </span>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {Math.abs(elasticity) > 1
            ? "⚠️ Clientes MUY sensibles al precio - cuidado al subir precios"
            : "✅ Clientes poco sensibles - puedes aumentar precios sin perder mucha demanda"}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="price"
            label={{
              value: "Precio ($)",
              position: "insideBottom",
              offset: -5,
            }}
          />
          <YAxis
            label={{ value: "Demanda", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            formatter={(value: any) => [parseFloat(value).toFixed(2), ""]}
            labelFormatter={(label) => `Precio: $${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="demand"
            stroke="#3b82f6"
            strokeWidth={2}
            name="Demanda"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 text-center text-sm text-gray-600">
        Precio actual:{" "}
        <span className="font-bold">${currentPrice.toFixed(2)}</span>
      </div>
    </div>
  );
}
