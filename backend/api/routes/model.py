"""
Model Routes - Endpoints para entrenamiento
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import TrainResponse
from api.session_manager import SessionManager
from src.demand_prediction import DemandPredictor
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

router = APIRouter()
session_manager = SessionManager()

# =============================================================================
# TRAIN MODEL
# =============================================================================


@router.post("/train/{session_id}", response_model=TrainResponse)
async def train_model(session_id: str):
    """
    Entrena el modelo de predicción de demanda

    **Path Parameter:**
    - session_id: ID de la sesión (del endpoint /load)

    **Proceso:**
    1. Carga df de la sesión
    2. Crea DemandPredictor(df)
    3. Llama a train_demand_model()
    4. Guarda el modelo en la sesión
    5. Retorna métricas

    **Response:**
    ```json
    {
      "session_id": "abc123",
      "product": "PROD_A",
      "r2_train": 0.9966,
      "r2_test": 0.9716,
      "rmse_train": 0.13,
      "rmse_test": 0.42,
      "features_used": ["Price", "day_of_week", ...],
      "feature_importance": [
        {"feature": "ticket_deviation", "importance": 0.5850},
        ...
      ]
    }
    ```
    """
    try:
        # Verificar sesión
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Cargar datos
        df = session_manager.load_dataframe(session_id, "df")

        # Verificar que el DataFrame no esté vacío
        if df.empty:
            raise HTTPException(
                status_code=400, detail="DataFrame is empty. Please load data first."
            )

        # Obtener productos únicos
        # Asegurarse de que la columna se llame 'ProductID' (como en tu código)
        if "ProductID" not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Column 'ProductID' not found in data. Please check your data format.",
            )

        productos = df["ProductID"].unique()

        if len(productos) == 0:
            raise HTTPException(status_code=400, detail="No products found in data")

        print(f"\n{'=' * 80}")
        print(f"ENTRENANDO MODELOS PARA {len(productos)} PRODUCTOS")
        print(f"{'=' * 80}\n")

        # Contadores para estadísticas
        modelos_entrenados = 0
        modelos_fallidos = 0

        # Almacenar métricas del último producto para respuesta
        ultimo_response = None

        # Entrenar modelo para cada producto
        for idx, producto in enumerate(productos, 1):
            print(
                f"\n[{idx}/{len(productos)}] Entrenando modelo para producto: {producto}"
            )
            print("-" * 50)

            # Filtrar datos para este producto
            df_product = df[df["ProductID"] == producto].copy()

            # Verificar datos suficientes
            min_registros = 10
            if len(df_product) < min_registros:
                print(
                    f"  ⚠️  Datos insuficientes ({len(df_product)} registros). Mínimo requerido: {min_registros}"
                )
                modelos_fallidos += 1
                continue

            # Verificar columna 'demand'
            if "demand" not in df_product.columns:
                print(f"  ⚠️  Columna 'demand' no encontrada en los datos")
                modelos_fallidos += 1
                continue

            try:
                # Crear predictor para este producto
                demand_predictor = DemandPredictor(df_product)

                # Entrenar modelo
                X_test, y_test, y_pred_test, feature_importance = (
                    demand_predictor.train_demand_model()
                )

                # Calcular métricas en train
                X = demand_predictor.prepare_features()
                y = df_product["demand"]
                X_scaled = demand_predictor.scaler.transform(X)
                y_pred_train = demand_predictor.demand_model.predict(X_scaled)

                r2_train = r2_score(y, y_pred_train)
                r2_test = r2_score(y_test, y_pred_test)
                rmse_train = np.sqrt(mean_squared_error(y, y_pred_train))
                rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))

                # Guardar modelo en sesión con nombre específico por producto
                session_manager.save_object(
                    session_id, demand_predictor, f"demand_predictor_{producto}"
                )

                # Convertir feature_importance a lista de diccionarios
                feature_imp_list = []
                if feature_importance is not None and not feature_importance.empty:
                    for _, row in feature_importance.iterrows():
                        feature_imp_list.append(
                            {
                                "feature": row["feature"],
                                "importance": float(row["importance"]),
                            }
                        )

                # Crear respuesta para este producto
                response_data = {
                    "session_id": session_id,
                    "product": producto,
                    "r2_train": float(r2_train),
                    "r2_test": float(r2_test),
                    "rmse_train": float(rmse_train),
                    "rmse_test": float(rmse_test),
                    "features_used": demand_predictor.feature_names,
                    "feature_importance": feature_imp_list,
                }

                # Guardar para posible respuesta
                ultimo_response = response_data
                modelos_entrenados += 1

                print(f"  ✅ Modelo guardado como 'demand_predictor_{producto}'")
                print(f"  📊 R² train: {r2_train:.4f} | R² test: {r2_test:.4f}")
                print(f"  📊 RMSE train: {rmse_train:.4f} | RMSE test: {rmse_test:.4f}")
                print(
                    f"  📈 Features utilizadas: {len(demand_predictor.feature_names)}"
                )

            except Exception as e:
                print(f"  ❌ Error entrenando producto {producto}: {str(e)}")
                modelos_fallidos += 1
                continue

        # Resumen final
        print(f"\n{'=' * 80}")
        print(f"RESUMEN DE ENTRENAMIENTO")
        print(f"{'=' * 80}")
        print(f"✅ Modelos entrenados exitosamente: {modelos_entrenados}")
        print(f"❌ Modelos fallidos: {modelos_fallidos}")
        print(f"📊 Total productos procesados: {len(productos)}")
        print(f"{'=' * 80}\n")

        # Verificar si se entrenó al menos un modelo
        if ultimo_response is None:
            raise HTTPException(
                status_code=400,
                detail=f"No models could be trained. Check data quality and requirements. Failed: {modelos_fallidos}/{len(productos)} products",
            )

        # Retornar respuesta con métricas del último producto entrenado
        return TrainResponse(**ultimo_response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training models: {str(e)}")


@router.get("/status/{session_id}")
async def get_model_status(session_id: str):
    """
    Verifica qué productos tienen modelos entrenados
    """
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        df = session_manager.load_dataframe(session_id, "df")
        productos = df["ProductID"].unique()

        modelos_entrenados = []
        modelos_faltantes = []

        for producto in productos:
            try:
                session_manager.load_object(session_id, f"demand_predictor_{producto}")
                modelos_entrenados.append(producto)
            except:
                modelos_faltantes.append(producto)

        return {
            "session_id": session_id,
            "total_products": len(productos),
            "trained_models": len(modelos_entrenados),
            "missing_models": len(modelos_faltantes),
            "trained_products": modelos_entrenados,
            "missing_products": modelos_faltantes,
            "is_complete": len(modelos_entrenados) == len(productos),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking model status: {str(e)}"
        )
