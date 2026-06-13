"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import api from "@/lib/api";
import type {
  LoadDataResponse,
  ElasticityResponse,
  ScenariosResponse,
  OptimizeResponse,
  RecommendationsResponse,
  OptimizeObjective,
} from "@/lib/api";

import KPIFiltersBar from "@/components/KPIFiltersBar";
import PriceCharts from "@/components/PriceCharts";
import ScenariosTable from "@/components/ScenariosTable";
import OptimalPriceCard from "@/components/OptimalPriceCard";
import RecommendationsTable from "@/components/RecommendationsTable";

function DashboardContent() {
  const searchParams = useSearchParams();
  const sessionIdFromUrl = searchParams.get("session");

  const [sessionId, setSessionId] = useState<string>(sessionIdFromUrl || "");
  const [sessionMeta, setSessionMeta] = useState<LoadDataResponse | null>(null);

  const [products, setProducts] = useState<string[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [price, setPrice] = useState<number>(50);
  const [cost, setCost] = useState<number>(30);
  const [objective, setObjective] = useState<OptimizeObjective>("revenue");
  const [productStats, setProductStats] = useState<{
    transactions: number;
    customers: number;
  }>({
    transactions: 0,
    customers: 0,
  });

  const [elasticityData, setElasticityData] =
    useState<ElasticityResponse | null>(null);
  const [scenariosData, setScenariosData] = useState<ScenariosResponse | null>(
    null,
  );
  const [optimizationData, setOptimizationData] =
    useState<OptimizeResponse | null>(null);
  const [recommendationsData, setRecommendationsData] =
    useState<RecommendationsResponse | null>(null);

  const [initialLoading, setInitialLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [optimizeLoading, setOptimizeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const priceRef = useRef(price);
  const costRef = useRef(cost);
  const objectiveRef = useRef(objective);
  const selectedProductRef = useRef(selectedProduct);
  const sessionIdRef = useRef(sessionId);

  priceRef.current = price;
  costRef.current = cost;
  objectiveRef.current = objective;
  selectedProductRef.current = selectedProduct;
  sessionIdRef.current = sessionId;

  const scheduleRecalc = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      const sid = sessionIdRef.current;
      const productId = selectedProductRef.current;
      const newPrice = priceRef.current;
      const newCost = costRef.current;
      const obj = objectiveRef.current;
      if (!productId) return;

      const basePriceArg = newPrice > 0 ? newPrice : undefined;

      try {
        setAnalysisLoading(true);
        const scenarios = await api.analysis.scenarios(
          sid,
          productId,
          newCost,
          basePriceArg,
        );
        setScenariosData(scenarios);
      } catch (e) {
        console.error(e);
      } finally {
        setAnalysisLoading(false);
      }
      try {
        setOptimizeLoading(true);
        const opt = await api.analysis.optimize(
          sid,
          productId,
          obj,
          newCost,
          basePriceArg,
        );
        setOptimizationData(opt);
      } catch (e) {
        console.error(e);
      } finally {
        setOptimizeLoading(false);
      }
    }, 600);
  }, []);

  const loadProductAnalysis = useCallback(
    async (
      sid: string,
      productId: string,
      costValue: number,
      obj: OptimizeObjective,
    ) => {
      if (!sid || !productId) return;

      api.data
        .getProductStats(sid, productId)
        .then((s) =>
          setProductStats({
            transactions: s.transactions,
            customers: s.customers,
          }),
        )
        .catch(console.error);

      try {
        setAnalysisLoading(true);
        const [elasticity, scenarios] = await Promise.all([
          api.analysis.elasticity(sid, productId),
          api.analysis.scenarios(sid, productId, costValue),
        ]);
        setElasticityData(elasticity);
        setScenariosData(scenarios);
        const actualPrice = Number(elasticity.current_price.toFixed(2));
        setPrice(actualPrice);
        priceRef.current = actualPrice;
      } catch (err: any) {
        console.error("Error loading product analysis:", err);
      } finally {
        setAnalysisLoading(false);
      }

      try {
        setOptimizeLoading(true);
        const opt = await api.analysis.optimize(sid, productId, obj, costValue);
        setOptimizationData(opt);
      } catch (err: any) {
        console.error("Error loading optimization:", err);
      } finally {
        setOptimizeLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const init = async () => {
      try {
        setInitialLoading(true);
        setError(null);

        let resolvedSessionId = sessionIdFromUrl || "";

        if (!sessionIdFromUrl) {
          try {
            const defaultSession = await api.data.getDefaultSession();
            resolvedSessionId = defaultSession.session_id;
            setSessionMeta(defaultSession.metadata);
          } catch {
            // Fall back to hardcoded default
          }
        }

        setSessionId(resolvedSessionId);
        sessionIdRef.current = resolvedSessionId;

        if (!resolvedSessionId) {
          throw new Error(
            "No se pudo encontrar una sesión activa. Por favor, carga datos primero.",
          );
        }

        if (!sessionMeta) {
          const meta = await api.data.getSession(resolvedSessionId);
          setSessionMeta(meta);
        }

        const modelStatus = await api.model.status(resolvedSessionId);
        if (!modelStatus.is_complete) {
          await api.model.train(resolvedSessionId);
        }

        const recs = await api.recommendations.getAll(resolvedSessionId, 20);
        setRecommendationsData(recs);

        const productList = recs.recommendations.map((r) => r.ProductID);
        setProducts(productList);

        if (productList.length > 0) {
          const firstProduct = productList[0];
          setSelectedProduct(firstProduct);
          selectedProductRef.current = firstProduct;
          await loadProductAnalysis(
            resolvedSessionId,
            firstProduct,
            costRef.current,
            objectiveRef.current,
          );
        }
      } catch (err: any) {
        console.error("Error initializing dashboard:", err);
        setError(err?.response?.data?.detail || "Error al cargar el dashboard");
      } finally {
        setInitialLoading(false);
      }
    };

    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleProductChange = useCallback(
    (productId: string) => {
      setSelectedProduct(productId);
      selectedProductRef.current = productId;
      setElasticityData(null);
      setScenariosData(null);
      setOptimizationData(null);
      loadProductAnalysis(
        sessionIdRef.current,
        productId,
        costRef.current,
        objectiveRef.current,
      );
    },
    [loadProductAnalysis],
  );

  const handleObjectiveChange = useCallback((obj: OptimizeObjective) => {
    setObjective(obj);
    objectiveRef.current = obj;
    const productId = selectedProductRef.current;
    if (!productId) return;
    setOptimizeLoading(true);
    const basePriceArg = priceRef.current > 0 ? priceRef.current : undefined;
    api.analysis
      .optimize(
        sessionIdRef.current,
        productId,
        obj,
        costRef.current,
        basePriceArg,
      )
      .then(setOptimizationData)
      .catch(console.error)
      .finally(() => setOptimizeLoading(false));
  }, []);

  const handleCostChange = useCallback(
    (newCost: number) => {
      setCost(newCost);
      costRef.current = newCost;
      scheduleRecalc();
    },
    [scheduleRecalc],
  );

  const handlePriceChange = useCallback(
    (newPrice: number) => {
      setPrice(newPrice);
      priceRef.current = newPrice;
      scheduleRecalc();
    },
    [scheduleRecalc],
  );

  if (initialLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-14 w-14 border-b-2 mx-auto mb-5"
            style={{ borderColor: "#00285d" }}
          />
          <h2 className="text-xl font-semibold text-slate-700 mb-1">
            Cargando Aplicación
          </h2>
          <p className="text-slate-400 text-sm">Preparando análisis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white p-8">
        <div className="bg-white rounded-2xl shadow-lg border border-red-100 p-8 max-w-md text-center">
          <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-6 h-6 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-slate-800 mb-2">
            Error al cargar
          </h2>
          <p className="text-slate-500 text-sm mb-5">{error}</p>
          <a
            href="/"
            className="inline-block px-5 py-2 rounded-lg text-white text-sm font-medium"
            style={{ backgroundColor: "#00285d" }}
          >
            Volver al inicio
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-100 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <h1 className="text-2xl font-bold" style={{ color: "#00285d" }}>
                Optimización Inteligente de Precios
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Optimización de precios y análisis de elasticidad en tiempo real
              </p>
            </div>
            {sessionMeta?.date_range && (
              <div className="text-right text-xs text-slate-400 self-center">
                <span className="font-medium text-slate-500">Período de datos: </span>
                {sessionMeta.date_range.start.slice(0, 10)} — {sessionMeta.date_range.end.slice(0, 10)}
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <KPIFiltersBar
          products={products}
          selectedProduct={selectedProduct}
          onProductChange={handleProductChange}
          price={price}
          onPriceChange={handlePriceChange}
          cost={cost}
          onCostChange={handleCostChange}
          transactions={productStats.transactions}
          customers={productStats.customers}
        />

        {analysisLoading && (
          <div className="flex items-center gap-3 text-slate-400 text-sm mb-6">
            <div
              className="animate-spin rounded-full h-4 w-4 border-b-2"
              style={{ borderColor: "#00285d" }}
            />
            Actualizando análisis...
          </div>
        )}

        {elasticityData && scenariosData && !analysisLoading && (
          <PriceCharts
            elasticityData={elasticityData}
            scenariosData={scenariosData}
          />
        )}

        {scenariosData && !analysisLoading && (
          <ScenariosTable scenarios={scenariosData.scenarios} />
        )}

        {(optimizationData || optimizeLoading) && (
          <OptimalPriceCard
            optimization={optimizationData!}
            objective={objective}
            onObjectiveChange={handleObjectiveChange}
            loading={optimizeLoading || !optimizationData}
          />
        )}

        {recommendationsData &&
          recommendationsData.recommendations.length > 0 && (
            <RecommendationsTable
              recommendations={recommendationsData.recommendations}
              objective={objective}
            />
          )}
      </main>

      <footer className="border-t border-slate-100 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 text-center text-xs text-slate-400">
          Optimización Inteligente de Precios · FastAPI + Next.js + Machine
          Learning
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-white">
          <div className="text-center">
            <div
              className="animate-spin rounded-full h-14 w-14 border-b-2 mx-auto mb-5"
              style={{ borderColor: "#00285d" }}
            />
            <p className="text-slate-400 text-sm">Cargando...</p>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
