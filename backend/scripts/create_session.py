"""
Script to transform product data with realistic names and prices,
then create a new session and train demand models.

Run from backend/ directory:
    uv run python scripts/create_session.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from api.session_manager import SessionManager
from src.demand_prediction import DemandPredictor

# ============================================================
# PRODUCT MAPPING: (ProductCategory, ProductID) -> (new_name, min_price, max_price)
# ============================================================
PRODUCT_MAP = {
    ("Books", "A"): ("Books_Harry_Potter", 12, 22),
    ("Books", "B"): ("Books_Frankenstein", 8, 16),
    ("Books", "C"): ("Books_1984", 9, 18),
    ("Books", "D"): ("Books_The_Great_Gatsby", 7, 14),
    ("Electronics", "A"): ("Electronics_AirPods_Pro", 200, 280),
    ("Electronics", "B"): ("Electronics_MacBook_Air", 999, 1499),
    ("Electronics", "C"): ("Electronics_iPhone_15", 699, 1099),
    ("Electronics", "D"): ("Electronics_iPad_Mini", 449, 649),
    ("Home Decor", "A"): ("HomeDecor_Ceramic_Vase", 25, 85),
    ("Home Decor", "B"): ("HomeDecor_LED_Floor_Lamp", 60, 150),
    ("Home Decor", "C"): ("HomeDecor_Throw_Pillow_Set", 20, 55),
    ("Home Decor", "D"): ("HomeDecor_Wood_Frame", 15, 40),
    ("Clothing", "A"): ("Clothing_Slim_Fit_Jeans", 45, 95),
    ("Clothing", "B"): ("Clothing_Merino_Sweater", 70, 160),
    ("Clothing", "C"): ("Clothing_Running_Sneakers", 80, 180),
    ("Clothing", "D"): ("Clothing_Waterproof_Jacket", 90, 220),
}

ELASTICIDADES = {
    "Clothing": -2.5,
    "Electronics": -1.8,
    "Home Decor": -1.5,
    "Books": -0.8,
    "Food": -0.5,
    "Other": -1.0,
}

FEATURES = {
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


def rescale_prices(series, new_min, new_max):
    old_min, old_max = series.min(), series.max()
    if old_max == old_min:
        return pd.Series([new_min] * len(series), index=series.index, dtype=float)
    return (
        new_min + (series - old_min) / (old_max - old_min) * (new_max - new_min)
    ).round(2)


def transform_data(csv_path):
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"DiscountApplied(%)": "DiscountApplied"})

    print(f"  Categories: {sorted(df['ProductCategory'].unique())}")
    print(f"  IDs:        {sorted(df['ProductID'].unique())}")

    orig_id = df["ProductID"].copy()

    # Rename ProductID to real product name
    def get_name(row):
        key = (row["ProductCategory"], row["ProductID"])
        return PRODUCT_MAP.get(
            key, (f"{row['ProductCategory']}_{row['ProductID']}", None, None)
        )[0]

    df["ProductID"] = df.apply(get_name, axis=1)

    # Rescale prices per product
    new_prices = df["Price"].copy().astype(float)
    for (cat, oid), (name, pmin, pmax) in PRODUCT_MAP.items():
        mask = (df["ProductCategory"] == cat) & (orig_id == oid)
        if mask.any():
            new_prices[mask] = rescale_prices(df.loc[mask, "Price"], pmin, pmax)
    df["Price"] = new_prices

    # Recalculate TotalAmount
    df["TotalAmount"] = (
        df["Price"] * df["Quantity"] * (1 - df["DiscountApplied"] / 100)
    ).round(2)

    print("\nPrice ranges after transformation:")
    for prod, grp in df.groupby("ProductID"):
        print(f"  {prod:<25} ${grp['Price'].min():.2f} – ${grp['Price'].max():.2f}")

    return df


def process_data(df):
    """Apply same feature engineering as get_data.py (but reads locally)."""
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
    df["is_weekend"] = (df["TransactionDate"].dt.dayofweek >= 5).astype(int)

    # Reference price per product
    df["p_ref"] = df.groupby("ProductID")["Price"].transform("mean")
    df["elast_val"] = df["ProductCategory"].map(ELASTICIDADES).fillna(-1.0)

    # Demand simulation (fixed seed for reproducibility)
    np.random.seed(42)
    ratio_precio = df["Price"] / (df["p_ref"] + 0.01)
    efecto_precio = ratio_precio ** df["elast_val"]
    efecto_finde = np.where(df["is_weekend"] == 1, 1.3, 1.0)
    ruido = np.random.normal(1, 0.2, size=len(df))
    df["demand"] = (3 * efecto_precio * efecto_finde * ruido).round().astype(int)
    df["demand"] = np.maximum(df["demand"], 1)

    # Date features
    df["Date"] = pd.to_datetime(df["TransactionDate"].dt.date)
    df["month"] = df["TransactionDate"].dt.month
    df["quarter"] = df["TransactionDate"].dt.quarter
    df["day_of_week"] = df["TransactionDate"].dt.dayofweek
    df["hour"] = df["TransactionDate"].dt.hour
    df["year_month"] = df["TransactionDate"].dt.strftime("%Y%m")

    # Parse city from address
    df["City"] = (
        df["StoreLocation"]
        .str.split("\n", expand=True)[1]
        .str.split(", ", expand=True)[0]
    )

    # Encodings
    df["category_encoded"] = pd.Categorical(df["ProductCategory"]).codes
    df["store_encoded"] = pd.Categorical(df["StoreLocation"]).codes
    df["payment_encoded"] = pd.Categorical(df["PaymentMethod"]).codes

    # Discounts
    df["has_discount"] = (df["DiscountApplied"] > 0).astype(int)
    df["discount_level"] = pd.cut(
        df["DiscountApplied"], bins=[-0.1, 0, 10, 20, 100], labels=[0, 1, 2, 3]
    ).astype(int)

    # Customer metrics (no leakage — cumulative history)
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

    # Price metrics
    df["category_avg_price"] = df.groupby("category_encoded")["Price"].transform("mean")
    df["price_vs_category"] = df["Price"] / (df["category_avg_price"] + 1)
    df["price_deviation"] = df.groupby("ProductID")["Price"].transform(
        lambda x: (x - x.mean()) / (x.mean() + 0.01)
    )

    # Financial metrics
    df["estimated_cost"] = df["Price"] * 0.6
    df["revenue"] = df["Price"] * df["demand"]
    df["estimated_profit"] = (df["Price"] - df["estimated_cost"]) * df["demand"]
    df["estimated_margin_pct"] = (
        (df["Price"] - df["estimated_cost"]) / df["Price"]
    ) * 100

    # Drop heavy columns
    df = df.drop(
        columns=["StoreLocation", "TransactionDate", "p_ref", "elast_val", "Quantity"],
        errors="ignore",
    )
    return df


def create_and_train_session(df):
    session_manager = SessionManager()
    session_id = session_manager.create_session()
    print(f"\nCreated session: {session_id}")

    session_manager.save_dataframe(session_id, df, "df")
    session_manager.save_object(session_id, list(FEATURES), "features")

    metadata = {
        "session_id": session_id,
        "rows": len(df),
        "products": df["ProductID"].nunique(),
        "customers": int(df["CustomerID"].nunique()),
        "date_range": {
            "start": str(df["Date"].min()),
            "end": str(df["Date"].max()),
        },
        "features": list(FEATURES),
    }
    session_manager.save_metadata(session_id, metadata)
    print(
        f"Saved: {len(df)} rows, {df['ProductID'].nunique()} products, {metadata['customers']} customers"
    )

    # Train one model per product
    productos = df["ProductID"].unique()
    print(f"\nTraining {len(productos)} models...")
    trained, failed = 0, 0
    for producto in sorted(productos):
        df_product = df[df["ProductID"] == producto].copy()
        try:
            predictor = DemandPredictor(df_product)
            X_test, y_test, y_pred, _ = predictor.train_demand_model()
            r2 = r2_score(y_test, y_pred)
            session_manager.save_object(
                session_id, predictor, f"demand_predictor_{producto}"
            )
            print(f"  ✅ {producto:<25} R²={r2:.4f}  ({len(df_product)} rows)")
            trained += 1
        except Exception as e:
            print(f"  ❌ {producto}: {e}")
            failed += 1

    print(f"\nResult: {trained} trained, {failed} failed")
    return session_id


def main():
    # Run from backend/ directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "Retail_Transaction_Dataset.csv")

    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el CSV en {csv_path}")
        print("Coloca 'Retail_Transaction_Dataset.csv' en backend/data/ y vuelve a ejecutar.")
        sys.exit(1)

    df_raw = transform_data(csv_path)
    print("\nApplying feature engineering...")
    df_proc = process_data(df_raw)

    session_id = create_and_train_session(df_proc)

    print(f"\n{'=' * 50}")
    print(f"  SESSION_ID = {session_id}")
    print(f"{'=' * 50}")
    print("\nNext steps:")
    print(f"  1. En backend/.env agrega/actualiza:  SESSION_ID={session_id}")
    print(f"  2. Reconstruye Docker:  docker compose build && docker compose up -d")


if __name__ == "__main__":
    main()
