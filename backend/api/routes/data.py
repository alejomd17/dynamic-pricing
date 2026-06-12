"""
Data Routes - Endpoints para manejo de datos
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import LoadDataResponse
from api.session_manager import SessionManager
from src.get_data import GetData

router = APIRouter()
session_manager = SessionManager()

# =============================================================================
# LOAD DATA
# =============================================================================


@router.post("/load", response_model=LoadDataResponse)
async def load_data():
    """
    Carga datos y crea una nueva sesión

    **Proceso:**
    1. Ejecuta GetData().get_data()
    2. Crea session_id
    3. Guarda df y features
    4. Retorna stats

    **Response:**
    ```json
    {
      "session_id": "abc123",
      "rows": 2000,
      "products": 5,
      "customers": 1568,
      "date_range": {"start": "2023-01-01", "end": "2024-12-31"},
      "features": ["Price", "demand", ...]
    }
    ```
    """
    try:
        # Cargar datos usando tu clase
        session_id = session_manager.create_session()
        print(f"Creando nueva sesión: {session_id}")

        data_loader = GetData(session_id=session_id)
        df, features = data_loader.get_data()

        # Crear sesión

        # Guardar datos en la sesión
        session_manager.save_dataframe(session_id, df, "df")
        session_manager.save_object(session_id, list(features), "features")

        # Calcular stats
        metadata = {
            "session_id": session_id,
            "rows": len(df),
            "products": df["ProductID"].nunique(),
            "customers": df["CustomerID"].nunique(),
            "date_range": {
                "start": str(df["Date"].min()),
                "end": str(df["Date"].max()),
            },
            "features": list(features),
        }

        session_manager.save_metadata(session_id, metadata)

        return LoadDataResponse(**metadata)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando datos: {str(e)}")


# =============================================================================
# GET SESSION INFO
# =============================================================================


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Obtiene información de una sesión existente
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    metadata = session_manager.load_metadata(session_id)
    return metadata


@router.get("/product-stats/{session_id}")
async def get_product_stats(session_id: str, product_id: str):
    """
    Retorna transacciones y clientes únicos para un producto específico
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    df = session_manager.load_dataframe(session_id, "df")
    df_product = df[df["ProductID"] == product_id]

    if df_product.empty:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    transactions = len(df_product)
    customers = (
        int(df_product["CustomerID"].nunique())
        if "CustomerID" in df_product.columns
        else 0
    )

    return {
        "product_id": product_id,
        "transactions": transactions,
        "customers": customers,
    }


@router.get("/default-session")
async def get_default_session():
    """
    Retorna la sesión activa: primero busca la definida en la variable de entorno
    SESSION_ID, si no existe toma la más reciente disponible en disco.
    Nunca tiene un ID hardcodeado.
    """
    import os
    from datetime import datetime

    # 1. Intentar usar el ID configurado por variable de entorno
    env_session_id = os.environ.get("SESSION_ID")
    if env_session_id and session_manager.session_exists(env_session_id):
        session_id = env_session_id
    else:
        # 2. Tomar la sesión más reciente disponible en disco
        session_id = session_manager.get_latest_session()

    if session_id is None:
        raise HTTPException(
            status_code=404,
            detail="No hay sesiones disponibles. Ejecuta POST /api/data/load para crear una.",
        )

    df = session_manager.load_dataframe(session_id, "df")
    metadata = session_manager.load_metadata(session_id)

    productos = df["ProductID"].unique()
    modelos_entrenados = sum(
        1
        for p in productos
        if (
            session_manager.get_session_path(session_id) / f"demand_predictor_{p}.pkl"
        ).exists()
    )

    metadata_path = session_manager.get_session_path(session_id) / "metadata.json"
    created_at = None
    if metadata_path.exists():
        mtime = os.path.getmtime(str(metadata_path))
        created_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "session_id": session_id,
        "exists": True,
        "models_trained": modelos_entrenados,
        "total_products": len(productos),
        "metadata": metadata,
        "created_at": created_at,
    }
