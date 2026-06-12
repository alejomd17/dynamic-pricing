# Dynamic Pricing

Dashboard de precios dinámicos — FastAPI + Next.js empaquetados en un solo contenedor Docker.

## Estructura

```
dynamic-pricing/
├── backend/              # FastAPI (Python 3.11 + uv)
│   ├── data/             # CSVs de entrada y caché procesada
│   ├── src/              # Módulos de análisis (elasticidad, escenarios, optimización)
│   ├── api/              # Rutas FastAPI
│   └── scripts/          # create_session.py
├── frontend/             # Next.js 16 + Tailwind + Recharts
├── Dockerfile            # Build monolítico (backend + frontend + nginx)
├── docker-compose.yml    # Local y producción
├── nginx.conf            # Proxy: / → frontend, /api → backend
└── entrypoint.sh         # Arranca los tres procesos
```

---

## Correr localmente

### 1. Generar la sesión de datos (una sola vez)

Requiere `uv` instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`):

```bash
cd backend
uv sync
uv run python scripts/create_session.py
```

Imprime al final:
```
SESSION_ID = a1b2c3d4
```

### 2. Levantar Docker

```bash
SESSION_ID=a1b2c3d4 docker compose up --build
```

Abre: **http://localhost:8080**

El primer build tarda ~5 min. Los siguientes son instantáneos.

---

## Desplegar en pricing.aleossa.com

En el servidor, después de clonar el repo y tener los CSVs en `backend/data/`:

```bash
# Generar sesión inicial (igual que en local)
cd backend && uv sync && uv run python scripts/create_session.py

# Levantar en producción
SESSION_ID=<id> CORS_ORIGINS=https://pricing.aleossa.com docker compose up --build -d
```

Luego apunta `pricing.aleossa.com` → `localhost:8080` con el Nginx/Caddy del servidor.

---

## Endpoints

| Endpoint | Descripción |
|---|---|
| `GET /api/docs` | Swagger UI interactivo |
| `GET /api/data/default-session` | Sesión activa |
| `POST /api/model/train/{id}` | Entrenar modelos de demanda |
| `POST /api/analysis/elasticity/{id}` | Elasticidad de precio |
| `POST /api/analysis/scenarios/{id}` | Escenarios de precio |
| `POST /api/analysis/optimize/{id}` | Precio óptimo |
| `GET /api/recommendations/{id}` | Recomendaciones por producto |
