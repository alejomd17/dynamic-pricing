import pandas as pd
from src.optimize_price import optimize_price
from src.price_elasticity import calculate_price_elasticity
from src.context import contextSimulation


def generate_product_recommendations(df, demand_predictor, product_id=None):
    """
    Genera recomendaciones de precio por producto

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame con datos de todos los productos
    demand_predictor : DemandPredictor
        Modelo entrenado (debe corresponder a product_id si se especifica)
    product_id : str, optional
        ID específico del producto. Si es None, genera para todos los productos

    Returns:
    --------
    pd.DataFrame
        DataFrame con las recomendaciones generadas
    """
    print("\n" + "=" * 80)
    print("RECOMENDACIONES DE PRECIO POR PRODUCTO")
    print("=" * 80 + "\n")

    # Determinar qué productos procesar
    if product_id is not None:
        # Procesar solo un producto específico
        if product_id not in df["ProductID"].values:
            print(f"Producto {product_id} no encontrado en los datos")
            return pd.DataFrame()
        productos = [product_id]
    else:
        # Procesar top 10 productos
        productos = df["ProductID"].unique()[:10]

    recommendations = []

    for producto in productos:
        df_prod = df[df["ProductID"] == producto]

        # Validar datos suficientes
        if len(df_prod) < 5:
            print(
                f"\n{producto}: Saltado - datos insuficientes ({len(df_prod)} registros)"
            )
            continue

        try:
            # Contexto promedio del producto
            context = contextSimulation.create_context_from_product(df, producto)

            # Agregar demanda actual si existe
            if "demand" in df_prod.columns and not df_prod["demand"].isnull().all():
                context["current_demand"] = float(df_prod["demand"].mean())
            else:
                context["current_demand"] = 100.0  # valor por defecto

            context["ticket_deviation"] = 0

            # Optimizar para revenue
            revenue_opt = optimize_price(demand_predictor, context, objective="revenue")

            # Optimizar para profit (con costo por unidad)
            estimated_cost = context.get("estimated_cost", 0)
            profit_opt = optimize_price(
                demand_predictor,
                context,
                cost_per_unit=estimated_cost,
                objective="profit",
            )

            # Optimizar para demanda
            demand_opt = optimize_price(demand_predictor, context, objective="demand")

            # Calcular elasticidad
            elasticity, _, _ = calculate_price_elasticity(demand_predictor, context)

            # Determinar recomendación
            recomendacion = (
                "Subir precio"
                if profit_opt["optimal_price"] > context["Price"]
                else "Bajar precio"
            )

            # LTV del segmento de clientes que compra este producto
            avg_ltv = None
            ltv_segment = None
            if "customer_ltv" in df_prod.columns:
                avg_ltv = float(df_prod["customer_ltv"].mean())
                p33 = df_prod["customer_ltv"].quantile(0.33)
                p66 = df_prod["customer_ltv"].quantile(0.66)
                if avg_ltv >= p66:
                    ltv_segment = "Alto"
                elif avg_ltv >= p33:
                    ltv_segment = "Medio"
                else:
                    ltv_segment = "Bajo"

            # Agregar a resultados
            recommendations.append(
                {
                    "ProductID": producto,
                    "precio_actual": context["Price"],
                    "demanda_actual": context["current_demand"],
                    "precio_max_revenue": revenue_opt["optimal_price"],
                    "precio_max_profit": profit_opt["optimal_price"],
                    "precio_max_demand": demand_opt["optimal_price"],
                    "revenue_actual": context["Price"] * context["current_demand"],
                    "revenue_optimizado": revenue_opt["expected_revenue"],
                    "profit_actual": (context["Price"] - estimated_cost)
                    * context["current_demand"],
                    "profit_optimizado": profit_opt["expected_profit"],
                    "elasticidad": elasticity,
                    "recomendacion": recomendacion,
                    "avg_ltv": avg_ltv,
                    "ltv_segment": ltv_segment,
                }
            )

            # Imprimir resultados en consola
            print(f"\n{producto}:")
            print(f"  Precio actual: ${context['Price']:.2f}")
            print(
                f"  Recomendado (revenue): ${revenue_opt['optimal_price']:.2f} ({revenue_opt['price_change_pct']:+.1f}%)"
            )
            print(
                f"  Recomendado (profit):  ${profit_opt['optimal_price']:.2f} ({profit_opt['price_change_pct']:+.1f}%)"
            )
            print(f"  Elasticidad: {elasticity:.3f}")
            print(f"  → {recomendacion}")

        except Exception as e:
            print(f"\n{producto}: Error - {str(e)}")
            continue

    df_recommendations = pd.DataFrame(recommendations)

    print("\n" + "=" * 80)
    print(f"✓ Recomendaciones generadas para {len(recommendations)} productos")
    print("=" * 80 + "\n")

    return df_recommendations
