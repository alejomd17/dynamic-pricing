"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface ElasticityPlotProps {
  sessionId: string;
  productId: string;
  costPerUnit?: number;
}

export default function ElasticityPlot({
  sessionId,
  productId,
  costPerUnit,
}: ElasticityPlotProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPlot();
  }, [sessionId, productId, costPerUnit]);

  const loadPlot = async () => {
    try {
      setLoading(true);
      setError(null);

      const url = await api.analysis.plotElasticity(
        sessionId,
        productId,
        costPerUnit,
      );
      setImageUrl(url);
    } catch (err: any) {
      console.error("❌ Error cargando gráfico:", err);
      setError(err.response?.data?.detail || "Error al generar gráfico");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generando gráfico de análisis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-red-500 text-xl mr-2">⚠️</span>
            <div>
              <p className="text-red-800 font-semibold">Error</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          📊 Análisis Completo de Elasticidad
        </h2>
        <p className="text-gray-600">
          Visualización generada con matplotlib mostrando demanda, revenue,
          profit y escenarios
        </p>
      </div>

      {imageUrl && (
        <div className="w-full overflow-hidden rounded-lg border border-gray-200">
          <img
            src={imageUrl}
            alt="Análisis de Elasticidad"
            className="w-full h-auto"
          />
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <button
          onClick={loadPlot}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          🔄 Regenerar gráfico
        </button>
      </div>
    </div>
  );
}
