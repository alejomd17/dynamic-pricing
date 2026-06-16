"""
Dynamic Pricing API
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import data, model, analysis, recommendations
from api.session_manager import SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("INICIANDO DYNAMIC PRICING API")
    print("=" * 60)

    session_manager = SessionManager()
    session_id = os.environ.get("SESSION_ID") or session_manager.get_latest_session()

    if session_id and session_manager.session_exists(session_id):
        print(f"Sesion activa: {session_id}")
        try:
            df = session_manager.load_dataframe(session_id, "df")
            productos = df["ProductID"].unique()
            modelos_entrenados = sum(
                1
                for p in productos
                if (
                    session_manager.get_session_path(session_id)
                    / f"demand_predictor_{p}.pkl"
                ).exists()
            )
            print(f"Productos: {len(productos)} | Modelos: {modelos_entrenados}/{len(productos)}")
        except Exception as e:
            print(f"Error al leer sesion: {e}")
    else:
        print("No hay sesiones. Ejecuta: uv run python scripts/create_session.py")

    print("=" * 60 + "\n")
    yield
    print("\nAPAGANDO DYNAMIC PRICING API\n")


app = FastAPI(
    title="Dynamic Pricing API",
    description="API para análisis de precios dinámicos",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    root_path="/dynamic_pricing",
)

_cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://aleossa.com,https://www.aleossa.com")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}


app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])


@app.get("/api")
async def root():
    return {
        "message": "Dynamic Pricing API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
