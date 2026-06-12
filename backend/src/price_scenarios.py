import pandas as pd


def analyze_price_scenarios(
    demand_predictor, context, cost_per_unit=None, price_changes=None
):
    """
    Analiza diferentes escenarios de precio

    Returns DataFrame con: price, demand, revenue, profit, elasticity
    """

    current_price = context.get("Price", 50)

    if price_changes is None:
        # Usar percentiles históricos del producto como límites realistas
        price_p5 = context.get("price_p5", current_price * 0.7)
        price_p95 = context.get("price_p95", current_price * 1.3)
        min_pct = round((price_p5 - current_price) / current_price * 100)
        max_pct = round((price_p95 - current_price) / current_price * 100)
        # Generar ~9 puntos equiespaciados dentro del rango, siempre incluyendo 0
        import numpy as np

        raw = [int(x) for x in np.linspace(min_pct, max_pct, 9)]
        # Reemplazar el punto más cercano a 0 con 0 exacto
        closest = min(range(len(raw)), key=lambda i: abs(raw[i]))
        raw[closest] = 0
        price_changes = sorted(set(raw))

    if cost_per_unit is None:
        # Usar costo estimado del contexto
        cost_per_unit = context.get("estimated_cost", current_price * 0.6)

    scenarios = []

    for pct_change in price_changes:
        new_price = current_price * (1 + pct_change / 100)

        ctx = context.copy()
        ctx["Price"] = new_price

        cat_avg = context.get("category_avg_price", current_price)
        prod_avg = context.get("product_avg_price", current_price)
        ctx["price_vs_category"] = new_price / (cat_avg + 0.01)

        if "product_avg_price" in context:
            ctx["price_deviation"] = (new_price - prod_avg) / (prod_avg + 0.01)

        demand = demand_predictor.predict_demand(ctx)
        revenue = new_price * demand
        profit = (new_price - cost_per_unit) * demand
        margin = ((new_price - cost_per_unit) / new_price) * 100 if new_price > 0 else 0

        scenarios.append(
            {
                "price_change_pct": pct_change,
                "price": new_price,
                "demand": demand,
                "revenue": revenue,
                "profit": profit,
                "margin_pct": margin,
                "units_sold_change": demand - context.get("current_demand", demand),
            }
        )

    df_scenarios = pd.DataFrame(scenarios)

    # Marcar el mejor
    df_scenarios["best_revenue"] = (
        df_scenarios["revenue"] == df_scenarios["revenue"].max()
    )
    df_scenarios["best_profit"] = df_scenarios["profit"] == df_scenarios["profit"].max()

    return df_scenarios
