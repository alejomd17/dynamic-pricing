from scipy.optimize import minimize


def optimize_price(
    demand_predictor,
    context,
    cost_per_unit=None,
    objective="revenue",
    price_bounds=None,
    constraints=None,
):
    """
    Optimiza precio manteniendo la estructura original pero corrigiendo lógica de features.
    """
    current_price = context.get("Price", 50)

    if price_bounds is None:
        p5 = context.get("price_p5", current_price * 0.7)
        p95 = context.get("price_p95", current_price * 1.3)
        price_bounds = (p5, p95)

    if cost_per_unit is None:
        cost_per_unit = context.get("estimated_cost", current_price * 0.6)

    def objective_function(price):
        ctx = context.copy()
        ctx["Price"] = price[0]

        # Actualizar todas las variables que dependen del precio
        # Añadimos + 0.01 para evitar división por cero
        ctx["price_vs_category"] = price[0] / (
            context.get("category_avg_price", price[0]) + 0.01
        )

        if "product_avg_price" in context:
            ctx["price_deviation"] = (price[0] - context["product_avg_price"]) / (
                context["product_avg_price"] + 0.01
            )

        demand = demand_predictor.predict_demand(ctx)

        if objective == "revenue":
            return -demand * price[0]
        elif objective == "profit":
            return -(demand * (price[0] - cost_per_unit))
        elif objective == "demand":
            return -demand
        else:
            raise ValueError("objective debe ser 'revenue', 'profit', o 'demand'")

    cons = []
    if constraints and "min_demand" in constraints:

        def demand_constraint(price):
            ctx = context.copy()
            ctx["Price"] = price[0]
            ctx["price_vs_category"] = price[0] / (
                context.get("category_avg_price", price[0]) + 0.01
            )

            # Mantener consistencia en la restricción también
            if "product_avg_price" in context:
                ctx["price_deviation"] = (price[0] - context["product_avg_price"]) / (
                    context["product_avg_price"] + 0.01
                )

            demand = demand_predictor.predict_demand(ctx)
            return demand - constraints["min_demand"]

        cons.append({"type": "ineq", "fun": demand_constraint})

    # Grid search sobre 100 puntos para encontrar el óptimo global,
    # luego refinamos con SLSQP desde el mejor punto encontrado.
    import numpy as np

    grid = np.linspace(price_bounds[0], price_bounds[1], 100)
    best_x0 = min(grid, key=lambda p: objective_function([p]))

    result = minimize(
        objective_function,
        x0=[best_x0],
        method="SLSQP",
        bounds=[price_bounds],
        constraints=cons if cons else None,
    )

    optimal_price = result.x[0]

    # Recalcular métricas finales con el precio óptimo encontrado
    ctx_optimal = context.copy()
    ctx_optimal["Price"] = optimal_price
    ctx_optimal["price_vs_category"] = optimal_price / (
        context.get("category_avg_price", optimal_price) + 0.01
    )
    if "product_avg_price" in context:
        ctx_optimal["price_deviation"] = (
            optimal_price - context["product_avg_price"]
        ) / (context["product_avg_price"] + 0.01)

    optimal_demand = demand_predictor.predict_demand(ctx_optimal)
    optimal_revenue = optimal_demand * optimal_price
    optimal_profit = optimal_demand * (optimal_price - cost_per_unit)

    return {
        "optimal_price": optimal_price,
        "predicted_demand": optimal_demand,
        "expected_revenue": optimal_revenue,
        "expected_profit": optimal_profit,
        "cost_per_unit": cost_per_unit,
        "margin_pct": ((optimal_price - cost_per_unit) / (optimal_price + 0.01)) * 100
        if optimal_price > 0
        else 0,
        "price_change_pct": ((optimal_price - current_price) / (current_price + 0.01))
        * 100,
    }
