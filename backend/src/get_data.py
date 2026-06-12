"""
Dynamic Pricing Model
===================================================
Carga datos locales del CSV de transacciones y aplica feature engineering.
"""

from pathlib import Path
import numpy as np
import pandas as pd

import warnings

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BACKEND_DIR / "data" / "Retail_Transaction_Dataset.csv"
CACHE_DIR = BACKEND_DIR / "data" / "processed"


class GetData:
    def __init__(self, cost_per_unit_default=None, session_id=None):
        self.available_features = set()
        self.df = pd.DataFrame()
        self.session_id = session_id

    def sellin_input(self):
        # Intentar cargar caché local procesado
        cache_path = CACHE_DIR / f"simulacion_retail_{self.session_id}.parquet"
        if cache_path.exists():
            print(f"Cargando datos procesados desde caché: {cache_path}")
            self.df = pd.read_parquet(cache_path)
            self._set_available_features()
            return self.df

        if not CSV_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el CSV en {CSV_PATH}. "
                "Coloca el archivo 'Retail_Transaction_Dataset.csv' en backend/data/"
            )

        print(f"Leyendo CSV local: {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)

        df = df.rename(columns={"DiscountApplied(%)": "DiscountApplied"}).copy()
        df["ProductID"] = df["ProductCategory"] + "_" + df["ProductID"]

        elasticidades = {
            "Clothing": -2.5,
            "Electronics": -1.8,
            "Home": -1.5,
            "Books": -0.8,
            "Food": -0.5,
            "Other": -1.0,
        }

        df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
        df["is_weekend"] = (df["TransactionDate"].dt.dayofweek >= 5).astype(int)

        df["p_ref"] = df.groupby(["ProductCategory", "ProductID"])["Price"].transform("mean")
        df["elast_val"] = df["ProductCategory"].map(elasticidades).fillna(-1.0)

        ratio_precio = df["Price"] / (df["p_ref"] + 0.01)
        efecto_precio = ratio_precio ** df["elast_val"]
        efecto_finde = np.where(df["is_weekend"] == 1, 1.3, 1.0)
        ruido = np.random.normal(1, 0.2, size=len(df))

        df["demand"] = (3 * efecto_precio * efecto_finde * ruido).round().astype(int)
        df["demand"] = np.maximum(df["demand"], 1)

        df["Date"] = pd.to_datetime(df["TransactionDate"].dt.date)
        df["month"] = df["TransactionDate"].dt.month
        df["day_of_week"] = df["TransactionDate"].dt.dayofweek
        df["hour"] = df["TransactionDate"].dt.hour
        df["year_month"] = df["TransactionDate"].dt.strftime("%Y%m")

        df["City"] = (
            df["StoreLocation"]
            .str.split("\n", expand=True)[1]
            .str.split(", ", expand=True)[0]
        )

        df["category_encoded"] = pd.Categorical(df["ProductCategory"]).codes
        df["store_encoded"] = pd.Categorical(df["StoreLocation"]).codes
        df["payment_encoded"] = pd.Categorical(df["PaymentMethod"]).codes

        df["has_discount"] = (df["DiscountApplied"] > 0).astype(int)
        df["discount_level"] = pd.cut(
            df["DiscountApplied"], bins=[-0.1, 0, 10, 20, 100], labels=[0, 1, 2, 3]
        ).astype(int)

        df = df.sort_values(["CustomerID", "Date"]).reset_index(drop=True)
        df["customer_purchase_count"] = df.groupby("CustomerID").cumcount() + 1
        df["customer_ltv"] = (
            df.groupby("CustomerID")["TotalAmount"]
            .apply(lambda x: x.shift(1).cumsum())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df["customer_avg_ticket"] = (
            df.groupby("CustomerID")["TotalAmount"]
            .apply(lambda x: x.shift(1).expanding().mean())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df["days_since_last_purchase"] = (
            df.groupby("CustomerID")["Date"].diff().dt.days.fillna(-1)
        )
        df["is_new_customer"] = (df["customer_purchase_count"] == 1).astype(int)

        df["category_avg_price"] = df.groupby("category_encoded")["Price"].transform("mean")
        df["price_vs_category"] = df["Price"] / (df["category_avg_price"] + 1)

        df["estimated_cost"] = df["Price"] * 0.6
        df["revenue"] = df["Price"] * df["demand"]
        df["estimated_profit"] = (df["Price"] - df["estimated_cost"]) * df["demand"]
        df["estimated_margin_pct"] = (
            (df["Price"] - df["estimated_cost"]) / df["Price"]
        ) * 100

        df = df.drop(
            columns=["StoreLocation", "TransactionDate", "p_ref", "elast_val", "Quantity"],
            errors="ignore",
        )

        # Guardar caché local
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False, engine="pyarrow")
        print(f"Caché guardado en: {cache_path}")

        self.df = df.copy()
        self._set_available_features()
        return self.df

    def _set_available_features(self):
        self.available_features = {
            "Price",
            "day_of_week",
            "hour",
            "is_weekend",
            "month",
            "has_discount",
            "discount_level",
            "DiscountApplied",
            "category_encoded",
            "store_encoded",
            "payment_encoded",
            "customer_purchase_count",
            "customer_avg_ticket",
            "is_new_customer",
            "days_since_last_purchase",
            "customer_ltv",
            "price_vs_category",
        }

    def get_data(self):
        self.sellin_input()
        return self.df, self.available_features
