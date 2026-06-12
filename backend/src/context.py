import pandas as pd
import numpy as np


class contextSimulation:
    def __init__(self):
        self.context = self.get_default_context()

    @staticmethod
    def get_default_context():
        return {
            "Price": 50,
            "day_of_week": 3,
            "hour": 14,
            "is_weekend": 0,
            "month": 6,
            "quarter": 2,
            "has_discount": 0,
            "discount_level": 0,
            "DiscountApplied": 0,
            "category_encoded": 0,
            "store_encoded": 0,
            "payment_encoded": 1,
            "InflationMonth": 0.005,
            "InflationYear": 0.045,
            "customer_purchase_count": 3,
            "customer_avg_ticket": 150,
            "is_new_customer": 0,
            "days_since_last_purchase": 30,
            "price_deviation": 0,
            "price_vs_category": 1,
            "estimated_cost": 30,
            "category_avg_price": 50,
            "product_avg_price": 66,
        }

    @staticmethod
    def create_context_from_product(df: pd.DataFrame, product_id: str) -> dict:
        """
        Creates a context dictionary for a specific product based on its historical data in the dataframe.
        """
        # Get product data
        prod_data = (
            df[df["ProductID"] == product_id]
            if "ProductID" in df.columns
            else pd.DataFrame()
        )

        # If no data found, return default context
        if prod_data.empty:
            return contextSimulation.get_default_context()

        # Calculate context variables based on the product's recent or average data
        context = contextSimulation.get_default_context()

        # Update context with actual data
        # Taking the mean or mode of the available columns
        if "Price" in prod_data.columns and not prod_data["Price"].isnull().all():
            context["Price"] = float(prod_data["Price"].mean())
            context["product_avg_price"] = float(prod_data["Price"].mean())
            context["price_p5"] = float(prod_data["Price"].quantile(0.05))
            context["price_p95"] = float(prod_data["Price"].quantile(0.95))

        for col in ["day_of_week", "hour", "month", "quarter"]:
            if col in prod_data.columns and not prod_data[col].isnull().all():
                mode_val = prod_data[col].mode()
                context[col] = int(mode_val[0]) if not mode_val.empty else context[col]

        for col in ["is_weekend", "has_discount", "is_new_customer"]:
            if col in prod_data.columns and not prod_data[col].isnull().all():
                context[col] = 1 if float(prod_data[col].mean()) > 0.5 else 0

        for col in [
            "discount_level",
            "DiscountApplied",
            "category_encoded",
            "store_encoded",
            "payment_encoded",
            "InflationMonth",
            "InflationYear",
            "customer_purchase_count",
            "customer_avg_ticket",
            "days_since_last_purchase",
            "price_deviation",
            "price_vs_category",
            "estimated_cost",
            "category_avg_price",
        ]:
            if col in prod_data.columns and not prod_data[col].isnull().all():
                # Get the mean value and convert to native python types
                mean_val = float(prod_data[col].mean())
                # Handle cases where the mean might be NaN even after the check
                if not pd.isna(mean_val):
                    context[col] = mean_val

        # Ensure that no numpy variables or NaN leak into the context, keeping default if so
        for key, val in context.items():
            if pd.isna(val):
                context[key] = contextSimulation.get_default_context()[key]

        return context
