import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

const client = axios.create({
  baseURL: API_URL,
});

export type OptimizeObjective = "revenue" | "profit" | "demand";

export interface LoadDataResponse {
  session_id: string;
  rows: number;
  products: number;
  customers: number;
  date_range: {
    start: string;
    end: string;
  };
  features: string[];
}

export interface ElasticityResponse {
  product_id: string;
  elasticity: number;
  elasticity_type: string;
  current_price: number;
  prices: number[];
  demands: number[];
}

export interface ScenarioItem {
  price_change_pct: number;
  price: number;
  demand: number;
  revenue: number;
  profit: number;
  margin_pct: number;
}

export interface ScenariosResponse {
  product_id: string;
  scenarios: ScenarioItem[];
}

export interface OptimizeResponse {
  product_id: string;
  optimal_price: number;
  current_price: number;
  price_change_pct: number;
  predicted_demand: number;
  expected_revenue: number;
  expected_profit: number;
  margin_pct: number;
}

export interface RecommendationItem {
  ProductID: string;
  precio_actual: number;
  precio_max_revenue: number;
  precio_max_profit: number;
  precio_max_demand: number | null;
  elasticidad: number;
  recomendacion: string;
  avg_ltv: number | null;
  ltv_segment: string | null;
}

export interface RecommendationsResponse {
  session_id: string;
  count: number;
  recommendations: RecommendationItem[];
}

export interface ModelStatusResponse {
  session_id: string;
  total_products: number;
  trained_models: number;
  missing_models: number;
  trained_products: string[];
  missing_products: string[];
  is_complete: boolean;
}

const api = {
  data: {
    getDefaultSession: async () => {
      const { data } = await client.get("/data/default-session");
      return data;
    },
    getSession: async (sessionId: string) => {
      const { data } = await client.get(`/data/session/${sessionId}`);
      return data;
    },
    getProductStats: async (sessionId: string, productId: string) => {
      const { data } = await client.get(`/data/product-stats/${sessionId}`, {
        params: { product_id: productId },
      });
      return data;
    },
  },
  model: {
    train: async (sessionId: string) => {
      const { data } = await client.post(`/model/train/${sessionId}`);
      return data;
    },
    status: async (sessionId: string): Promise<ModelStatusResponse> => {
      const { data } = await client.get(`/model/status/${sessionId}`);
      return data;
    },
  },
  analysis: {
    elasticity: async (
      sessionId: string,
      productId: string,
    ): Promise<ElasticityResponse> => {
      const { data } = await client.post(`/analysis/elasticity/${sessionId}`, {
        product_id: productId,
      });
      return data;
    },
    scenarios: async (
      sessionId: string,
      productId: string,
      costPerUnit?: number,
      basePrice?: number,
    ): Promise<ScenariosResponse> => {
      const { data } = await client.post(`/analysis/scenarios/${sessionId}`, {
        product_id: productId,
        cost_per_unit: costPerUnit,
        base_price: basePrice,
      });
      return data;
    },
    optimize: async (
      sessionId: string,
      productId: string,
      objective: OptimizeObjective,
      costPerUnit?: number,
      basePrice?: number,
    ): Promise<OptimizeResponse> => {
      const { data } = await client.post(`/analysis/optimize/${sessionId}`, {
        product_id: productId,
        objective,
        cost_per_unit: costPerUnit,
        base_price: basePrice,
      });
      return data;
    },
    plotElasticity: async (
      sessionId: string,
      productId: string,
      costPerUnit?: number,
      basePrice?: number,
    ): Promise<string> => {
      const { data } = await client.post(
        `/analysis/plot-elasticity/${sessionId}`,
        {
          product_id: productId,
          cost_per_unit: costPerUnit,
          base_price: basePrice,
        },
        { responseType: "blob" },
      );
      return URL.createObjectURL(data);
    },
  },
  recommendations: {
    getAll: async (
      sessionId: string,
      limit: number = 10,
    ): Promise<RecommendationsResponse> => {
      const { data } = await client.get(`/recommendations/${sessionId}`, {
        params: { limit },
      });
      return data;
    },
  },
};

export default api;
