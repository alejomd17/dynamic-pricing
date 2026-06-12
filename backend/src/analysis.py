"""
Analysis Routes - Elasticidad, Escenarios, Optimización
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.models.schemas import (
    ElasticityRequest,
    ElasticityResponse,
    ScenariosRequest,
    ScenariosResponse,
    ScenarioItem,
    OptimizeRequest,
    OptimizeResponse,
)
from api.session_manager import SessionManager
from src.price_elasticity import calculate_price_elasticity
from src.price_scenarios import analyze_price_scenarios
from src.optimize_price import optimize_price
from src.plot_elasticity_price import plot_elasticity_analysis
from src.context import contextSimulation
import io
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend

router = APIRouter()
session_manager = SessionManager()

# =============================================================================
# ELASTICITY
# =============================================================================


@router.post("/elasticity/{session_id}", response_model=ElasticityResponse)
async def get_elasticity(session_id: str, request: ElasticityRequest):
    """
    Calcula elasticidad precio-demanda para un producto

    **Body:**
    ```json
    {
      "product_id": "PROD_A"
    }
    ```

    **Response:**
    Elasticidad + arrays para gráfico
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar modelo y datos
        demand_predictor = session_manager.load_object(session_id, "demand_predictor")
        df = session_manager.load_dataframe(session_id, "df")

        # Crear contexto para el producto
        context = contextSimulation.create_context_from_product(df, request.product_id)

        # Calcular elasticidad
        elasticity, prices, demands = calculate_price_elasticity(
            demand_predictor, context
        )

        response = {
            "product_id": request.product_id,
            "elasticity": float(elasticity),
            "elasticity_type": "elastic" if abs(elasticity) > 1 else "inelastic",
            "current_price": float(context["Price"]),
            "prices": [float(p) for p in prices],
            "demands": [float(d) for d in demands],
        }

        return ElasticityResponse(**response)

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Call POST /train/{session_id} first",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating elasticity: {str(e)}"
        )


# =============================================================================
# SCENARIOS
# =============================================================================


@router.post("/scenarios/{session_id}", response_model=ScenariosResponse)
async def get_scenarios(session_id: str, request: ScenariosRequest):
    """
    Genera escenarios de precio para un producto

    **Body:**
    ```json
    {
      "product_id": "PROD_A",
      "cost_per_unit": 30  // opcional
    }
    ```

    **Response:**
    Lista de escenarios con precio, demanda, revenue, profit
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar modelo y datos
        demand_predictor = session_manager.load_object(session_id, "demand_predictor")
        df = session_manager.load_dataframe(session_id, "df")

        # Crear contexto
        context = contextSimulation.create_context_from_product(df, request.product_id)

        # Calcular escenarios
        scenarios_df = analyze_price_scenarios(
            demand_predictor, context, cost_per_unit=request.cost_per_unit
        )

        # Convertir a lista de ScenarioItem
        scenarios_list = []
        for _, row in scenarios_df.iterrows():
            scenarios_list.append(
                ScenarioItem(
                    price_change_pct=int(row["price_change_pct"]),
                    price=float(row["price"]),
                    demand=float(row["demand"]),
                    revenue=float(row["revenue"]),
                    profit=float(row["profit"]),
                    margin_pct=float(row["margin_pct"]),
                )
            )

        return ScenariosResponse(
            product_id=request.product_id, scenarios=scenarios_list
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Call POST /train/{session_id} first",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating scenarios: {str(e)}"
        )


# =============================================================================
# OPTIMIZATION
# =============================================================================


@router.post("/optimize/{session_id}", response_model=OptimizeResponse)
async def optimize_product_price(session_id: str, request: OptimizeRequest):
    """
    Optimiza el precio de un producto

    **Body:**
    ```json
    {
      "product_id": "PROD_A",
      "objective": "profit",  // o "revenue"
      "cost_per_unit": 30     // opcional
    }
    ```

    **Response:**
    Precio óptimo + métricas esperadas
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar modelo y datos
        demand_predictor = session_manager.load_object(session_id, "demand_predictor")
        df = session_manager.load_dataframe(session_id, "df")

        # Crear contexto
        context = contextSimulation.create_context_from_product(df, request.product_id)

        # Optimizar
        result = optimize_price(
            demand_predictor,
            context,
            cost_per_unit=request.cost_per_unit,
            objective=request.objective,
        )

        response = {
            "product_id": request.product_id,
            "optimal_price": float(result["optimal_price"]),
            "current_price": float(context["Price"]),
            "price_change_pct": float(result["price_change_pct"]),
            "predicted_demand": float(result["predicted_demand"]),
            "expected_revenue": float(result["expected_revenue"]),
            "expected_profit": float(result["expected_profit"]),
            "margin_pct": float(result["margin_pct"]),
        }

        return OptimizeResponse(**response)

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Call POST /train/{session_id} first",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing price: {str(e)}")


# =============================================================================
# ELASTICITY PLOT (NEW)
# =============================================================================


@router.post("/plot-elasticity/{session_id}")
async def plot_elasticity(session_id: str, request: ElasticityRequest):
    """
    Genera un gráfico completo de análisis de elasticidad

    **Body:**
    ```json
    {
      "product_id": "PROD_A",
      "cost_per_unit": 30  // opcional
    }
    ```

    **Response:**
    Imagen PNG con 4 subplots:
    - Demanda vs Precio
    - Revenue vs Precio
    - Profit vs Precio
    - Escenarios comparativos
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar modelo y datos
        demand_predictor = session_manager.load_object(session_id, "demand_predictor")
        df = session_manager.load_dataframe(session_id, "df")

        # Crear contexto para el producto
        context = contextSimulation().create_context_from_product(
            df, request.product_id
        )

        # Determinar costo
        cost_per_unit = getattr(request, "cost_per_unit", None) or 30

        # Generar figura
        fig = plot_elasticity_analysis(
            demand_predictor, context, cost_per_unit=cost_per_unit, save_path=None
        )

        # Convertir a bytes
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)

        # Cerrar figura para liberar memoria
        import matplotlib.pyplot as plt

        plt.close(fig)

        return StreamingResponse(buf, media_type="image/png")

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Model not trained. Call POST /train/{session_id} first",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")
