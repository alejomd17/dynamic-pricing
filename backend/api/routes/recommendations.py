"""
Recommendations Routes - Recomendaciones de pricing por producto
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import RecommendationsResponse, RecommendationItem
from api.session_manager import SessionManager
from src.product_recommendations import generate_product_recommendations
import pandas as pd

router = APIRouter()
session_manager = SessionManager()

# =============================================================================
# RECOMMENDATIONS
# =============================================================================


@router.get("/{session_id}", response_model=RecommendationsResponse)
async def get_recommendations(session_id: str, limit: int = 10):
    """
    Genera recomendaciones de precio para todos los productos

    **Parameters:**
    - session_id: ID de sesión
    - limit: Número máximo de productos (default: 10)

    **Response:**
    Lista de recomendaciones con precio actual, sugerido, elasticidad, etc.
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar datos
        df = session_manager.load_dataframe(session_id, "df")

        # Obtener productos únicos
        productos_unicos = df["ProductID"].unique()

        # Identificar productos que tienen modelos entrenados
        productos_con_modelo = []
        for product_id in productos_unicos:
            try:
                # Intentar cargar el modelo para este producto
                demand_predictor = session_manager.load_object(
                    session_id, f"demand_predictor_{product_id}"
                )
                productos_con_modelo.append((product_id, demand_predictor))
            except Exception:
                # Si no hay modelo, lo saltamos
                continue

        # Verificar si hay productos con modelo
        if not productos_con_modelo:
            raise HTTPException(
                status_code=400,
                detail="No trained models found. Call POST /train/{session_id} for each product first",
            )

        # Generar recomendaciones para cada producto con su modelo específico
        todas_recomendaciones = []
        for product_id, demand_predictor in productos_con_modelo[
            :limit
        ]:  # Limitar a 'limit' productos
            try:
                # Llamar a la función con product_id específico
                recommendations_df = generate_product_recommendations(
                    df, demand_predictor, product_id=product_id
                )

                if not recommendations_df.empty:
                    todas_recomendaciones.append(recommendations_df)

            except Exception as e:
                # Si falla un producto, continuamos con los demás
                print(f"Error generando recomendaciones para {product_id}: {str(e)}")
                continue

        # Verificar si se generaron recomendaciones
        if not todas_recomendaciones:
            return RecommendationsResponse(
                session_id=session_id, count=0, recommendations=[]
            )

        # Combinar todas las recomendaciones
        combined_df = pd.concat(todas_recomendaciones, ignore_index=True)

        # Ordenar por elasticidad (más elásticos primero) y limitar
        if "elasticidad" in combined_df.columns:
            combined_df = combined_df.sort_values("elasticidad", ascending=False)

        combined_df = combined_df.head(limit)

        # Convertir a lista de RecommendationItem
        recommendations_list = []
        for _, row in combined_df.iterrows():
            recommendations_list.append(
                RecommendationItem(
                    ProductID=str(row["ProductID"]),
                    precio_actual=float(row["precio_actual"]),
                    precio_max_revenue=float(row["precio_max_revenue"]),
                    precio_max_profit=float(row["precio_max_profit"]),
                    precio_max_demand=float(row["precio_max_demand"])
                    if "precio_max_demand" in row
                    else None,
                    elasticidad=float(row["elasticidad"]),
                    recomendacion=str(row["recomendacion"]),
                    avg_ltv=float(row["avg_ltv"])
                    if "avg_ltv" in row and row["avg_ltv"] is not None
                    else None,
                    ltv_segment=str(row["ltv_segment"])
                    if "ltv_segment" in row and row["ltv_segment"] is not None
                    else None,
                )
            )

        return RecommendationsResponse(
            session_id=session_id,
            count=len(recommendations_list),
            recommendations=recommendations_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}"
        )
