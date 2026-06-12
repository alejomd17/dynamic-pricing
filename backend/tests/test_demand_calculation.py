import pandas as pd
import pytest
from src.demand_calculation import calculate_demand


def test_calculate_demand_basic():
    # 1. Crear datos de ejemplo (mock data)
    data = {
        "Date": ["2023-01-01", "2023-01-01", "2023-01-01"],
        "ProductID": [1, 1, 2],
        "Price": [10.0, 10.0, 20.0],
        "category_encoded": [0, 0, 1],
        "Quantity": [2, 3, 1],
        "CustomerID": [101, 102, 103],
        "TotalAmount": [20.0, 30.0, 20.0],
        "day_of_week": [6, 6, 6],
        "hour": [10, 11, 12],
        "is_weekend": [True, True, True],
        "month": [1, 1, 1],
        "quarter": [1, 1, 1],
        "has_discount": [0, 0, 0],
        "discount_level": [0, 0, 0],
        "DiscountApplied": [0.0, 0.0, 0.0],
        "store_encoded": [1, 1, 1],
        "payment_encoded": [1, 1, 1],
        "InflationMonth": [0.05, 0.05, 0.05],
        "InflationYear": [0.5, 0.5, 0.5],
    }
    df = pd.DataFrame(data)

    # 2. Ejecutar la función
    result = calculate_demand(df)

    # 3. Verificaciones (Assertions)
    # Debería haber 2 filas (una para Product 1 y otra para Product 2)
    assert len(result) == 2

    # La demanda del Producto 1 debería ser 5 (2 + 3)
    demand_p1 = result[result["ProductID"] == 1]["demand"].iloc[0]
    assert demand_p1 == 5

    # La demanda del Producto 2 debería ser 1
    demand_p2 = result[result["ProductID"] == 2]["demand"].iloc[0]
    assert demand_p2 == 1

    # Verificar que las columnas clave existan
    assert "demand" in result.columns
    assert "ProductID" in result.columns
