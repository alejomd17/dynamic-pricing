"""
API Schemas - Pydantic models para validación
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# =============================================================================
# DATA LOADING
# =============================================================================


class DownloadRequest(BaseModel):
    """Request para descargar datos"""

    datasets: List[str] = Field(
        ..., description="Lista de datasets: 'inflacion', 'transacciones'"
    )


class LoadDataResponse(BaseModel):
    """Response al cargar datos"""

    session_id: str
    rows: int
    products: int
    customers: int
    date_range: Dict[str, str]
    features: List[str]


# =============================================================================
# MODEL TRAINING
# =============================================================================


class TrainResponse(BaseModel):
    """Response al entrenar modelo"""

    session_id: str
    product: Optional[str] = None
    r2_train: float
    r2_test: float
    rmse_train: float
    rmse_test: float
    features_used: List[str]
    feature_importance: List[Dict[str, Any]]


# =============================================================================
# ELASTICITY ANALYSIS
# =============================================================================


class ElasticityRequest(BaseModel):
    """Request para análisis de elasticidad"""

    product_id: str = Field(..., description="ID del producto")


class ElasticityResponse(BaseModel):
    """Response de elasticidad"""

    product_id: str
    elasticity: float
    elasticity_type: str  # "elastic" o "inelastic"
    current_price: float
    prices: List[float]
    demands: List[float]


# =============================================================================
# SCENARIOS
# =============================================================================


class ScenariosRequest(BaseModel):
    """Request para escenarios"""

    product_id: str
    cost_per_unit: Optional[float] = None
    base_price: Optional[float] = None


class ScenarioItem(BaseModel):
    """Item de escenario"""

    price_change_pct: int
    price: float
    demand: float
    revenue: float
    profit: float
    margin_pct: float


class ScenariosResponse(BaseModel):
    """Response de escenarios"""

    product_id: str
    scenarios: List[ScenarioItem]


# =============================================================================
# OPTIMIZATION
# =============================================================================


class OptimizeRequest(BaseModel):
    """Request para optimización"""

    product_id: str
    objective: str = Field("profit", description="'revenue', 'profit' o 'demand'")
    cost_per_unit: Optional[float] = None
    base_price: Optional[float] = None


class OptimizeResponse(BaseModel):
    """Response de optimización"""

    product_id: str
    optimal_price: float
    current_price: float
    price_change_pct: float
    predicted_demand: float
    expected_revenue: float
    expected_profit: float
    margin_pct: float


# =============================================================================
# RECOMMENDATIONS
# =============================================================================


class RecommendationItem(BaseModel):
    """Item de recomendación"""

    ProductID: str
    precio_actual: float
    precio_max_revenue: float
    precio_max_profit: float
    precio_max_demand: Optional[float] = None
    elasticidad: float
    recomendacion: str
    avg_ltv: Optional[float] = None
    ltv_segment: Optional[str] = None


class RecommendationsResponse(BaseModel):
    """Response de recomendaciones"""

    session_id: str
    count: int
    recommendations: List[RecommendationItem]


# =============================================================================
# EDA
# =============================================================================


class EDAResponse(BaseModel):
    """Response de EDA"""

    session_id: str
    charts: List[Dict[str, Any]]  # Lista de gráficos Plotly en JSON
    summary: Dict[str, Any]
