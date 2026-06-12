# 🎯 Dynamic Pricing Backend

Backend FastAPI
---

## 📁 ESTRUCTURA

```
backend/
├── main.py                      # FastAPI app principal
├── pyproject.toml               # Dependencies (uv)
│
├── src/                         # TUS MÓDULOS (sin cambios)
│   ├── get_data.py             # GetData class
│   ├── demand_prediction.py    # DemandPredictor class
│   ├── price_elasticity.py     # calculate_price_elasticity()
│   ├── price_scenarios.py      # analyze_price_scenarios()
│   ├── optimize_price.py       # optimize_price()
│   ├── product_recommendations.py
│   ├── context.py              # contextSimulation
│   ├── download_data.py        # download_data()
│   └── ...
│
├── api/                         # FastAPI wrappers
│   ├── session_manager.py      # Manejo de sesiones
│   ├── routes/
│   │   ├── data.py             # /download, /load
│   │   ├── model.py            # /train
│   │   ├── analysis.py         # /elasticity, /scenarios, /optimize
│   │   └── recommendations.py  # /recommendations
│   └── models/
│       └── schemas.py          # Pydantic models
│
└── data/
    └── sessions/                # Sesiones de usuario
```

---

## 🚀 SETUP

### **Opción 1: Con UV (Recomendado)**

```bash
cd backend

# Instalar dependencias
uv sync

# O manualmente:
uv add fastapi uvicorn[standard] python-multipart
uv add pandas numpy scikit-learn scipy
uv add pydantic plotly python-dotenv
uv add google-cloud-storage
uv add pyarrow fastparquet

# Correr servidor
uv run uvicorn main:app --reload
```

### **Opción 2: Con pip tradicional**

```bash
cd backend

# Crear venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar
pip install fastapi uvicorn[standard] python-multipart
pip install pandas numpy scikit-learn scipy
pip install pydantic plotly python-dotenv google-cloud-storage pyarrow fastparquet

# Correr
python main.py
```

---

## 📡 ENDPOINTS

### **1. Data Loading**

```bash
# Descargar datos (requiere .env con GCP credentials)
POST /api/data/download
Body: {"datasets": ["transacciones", "inflacion"]}

# Cargar datos y crear sesión
POST /api/data/load
Response: {
  "session_id": "abc123",
  "rows": 2000,
  "products": 5,
  "features": [...]
}

# Info de sesión
GET /api/data/session/{session_id}
```

### **2. Model Training**

```bash
# Entrenar modelo
POST /api/model/train/{session_id}
Response: {
  "r2_test": 0.9716,
  "rmse_test": 0.42,
  "feature_importance": [...]
}
```

### **3. Analysis**

```bash
# Elasticidad
POST /api/analysis/elasticity/{session_id}
Body: {"product_id": "PROD_A"}

# Escenarios
POST /api/analysis/scenarios/{session_id}
Body: {"product_id": "PROD_A", "cost_per_unit": 30}

# Optimización
POST /api/analysis/optimize/{session_id}
Body: {
  "product_id": "PROD_A",
  "objective": "profit",
  "cost_per_unit": 30
}
```

### **4. Recommendations**

```bash
# Recomendaciones para todos los productos
GET /api/recommendations/{session_id}?limit=10
```

---

## CORRER LA API

### **1. Docs Automáticos**

Abre: http://localhost:8000/docs

Verás Swagger UI interactivo donde puedes probar todos los endpoints.

### **2. Flujo Completo (ejemplo con curl)**

```bash
# 1. Cargar datos
curl -X POST http://localhost:8000/api/data/load

# Response: {"session_id": "abc123", ...}

# 2. Entrenar modelo
curl -X POST http://localhost:8000/api/model/train/abc123

# 3. Calcular elasticidad
curl -X POST http://localhost:8000/api/analysis/elasticity/abc123 \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD_A"}'

# 4. Ver recomendaciones
curl http://localhost:8000/api/recommendations/abc123
```

---

##  FLUJO LOCAL vs API

### **LOCAL (Script):**

```python
# 1. Download
from src.download_data import download_data
download_data(['inflacion','transacciones'])

# 2. Load
from src.get_data import GetData
df, features = GetData().get_data()

# 3. Train
from src.demand_prediction import DemandPredictor
predictor = DemandPredictor(df)
predictor.train_demand_model()

# 4. Elasticity
from src.price_elasticity import calculate_price_elasticity
elasticity, prices, demands = calculate_price_elasticity(predictor, context)

# 5. Scenarios
from src.price_scenarios import analyze_price_scenarios
scenarios = analyze_price_scenarios(predictor, context, cost=30)

# 6. Optimize
from src.optimize_price import optimize_price
result = optimize_price(predictor, context, objective='profit')

# 7. Recommendations
from src.product_recommendations import generate_product_recommendations
recs = generate_product_recommendations(df, predictor)
```

### **API:**

```bash
# 1. Download
POST /api/data/download

# 2. Load
POST /api/data/load → session_id

# 3. Train
POST /api/model/train/{session_id}

# 4. Elasticity
POST /api/analysis/elasticity/{session_id}

# 5. Scenarios
POST /api/analysis/scenarios/{session_id}

# 6. Optimize
POST /api/analysis/optimize/{session_id}

# 7. Recommendations
GET /api/recommendations/{session_id}
```

---
## SESIONES

El backend guarda el estado en `data/sessions/{session_id}/`:

```
data/sessions/abc123/
├── df.parquet              # DataFrame
├── demand_predictor.pkl    # Modelo entrenado
├── features.pkl            # Lista de features
└── metadata.json           # Info de la sesión
```

Esto permite:
- ✅ Múltiples usuarios simultáneos
- ✅ No re-entrenar en cada request
- ✅ Persistencia temporal

---

## 🐛 TROUBLESHOOTING

### Error: "Session not found"
- Primero llama a `POST /api/data/load` para crear sesión
- Guarda el `session_id` que retorna

### Error: "Model not trained"
- Llama a `POST /api/model/train/{session_id}` antes de análisis

### Error: ModuleNotFoundError
- Asegúrate de estar en `backend/`
- Verifica que `src/` tenga `__init__.py`

---

## PRÓXIMO PASO

Una vez que el backend funcione:

```bash
cd backend
uv run uvicorn main:app --reload

# En otra terminal:
curl http://localhost:8000
# Deberías ver: {"message": "Dynamic Pricing API", ...}
```