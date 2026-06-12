"""
Business Dashboard & EDA - Dynamic Pricing
==========================================================
Dashboard ejecutivo para análisis de performance de retail.
Enfoque en KPIs de negocio, elasticidad de precios y comportamiento del consumidor.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")

# Configuración de estilo corporativo
COLOR_PALETTE = px.colors.qualitative.Prism
TEMPLATE = "plotly_white"


def generar_dashboard_negocio(df):
    """
    Ejecuta el pipeline completo de visualización para negocio.
    """
    print("\n" + "=" * 80)
    print("🚀 GENERANDO DASHBOARD EJECUTIVO DE RETAIL")
    print("=" * 80 + "\n")

    # 1. KPIs Principales (Big Numbers)
    mostrar_kpis_principales(df)

    # 2. Análisis de Elasticidad (El corazón del Dynamic Pricing)
    analisis_elasticidad_precio(df)

    # 3. Evolución Temporal y Estacionalidad
    analisis_temporal_negocio(df)

    # 4. Performance de Productos (Pareto)
    analisis_pareto_productos(df)

    # 5. Rentabilidad y Márgenes
    analisis_rentabilidad_categoria(df)

    print("\n✅ Dashboard generado exitosamente.")


# ============================================================================
# 1. KPIs PRINCIPALES (BIG NUMBERS)
# ============================================================================
def mostrar_kpis_principales(df):
    print("📊 Generando KPIs Principales...")

    # Cálculos
    total_revenue = df["revenue"].sum()
    total_profit = df["estimated_profit"].sum()
    margin_pct = (total_profit / total_revenue) * 100
    aov = (
        df["revenue"].sum() / df["demand"].sum()
    )  # Average Order Value (aprox por unidad)
    avg_ticket = (
        df.groupby("CustomerID")["revenue"].sum().mean()
    )  # Valor real del cliente

    fig = go.Figure()

    kpis = [
        {
            "label": "Ingresos Totales",
            "value": f"${total_revenue:,.0f}",
            "color": "green",
        },
        {
            "label": "Beneficio (Profit)",
            "value": f"${total_profit:,.0f}",
            "color": "blue",
        },
        {"label": "Margen Global", "value": f"{margin_pct:.1f}%", "color": "orange"},
        {
            "label": "Ticket Promedio (AOV)",
            "value": f"${avg_ticket:.2f}",
            "color": "purple",
        },
    ]

    # Crear tarjetas de indicadores
    for i, kpi in enumerate(kpis):
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=0,  # Dummy value, usamos title y number formatting abajo
                number={"prefix": "", "font": {"size": 50, "color": kpi["color"]}},
                title={
                    "text": f"{kpi['label']}<br><span style='font-size:0.8em;color:gray'>{kpi['value']}</span>"
                },
                domain={"row": 0, "column": i},
            )
        )

    fig.update_layout(
        grid={"rows": 1, "columns": 4, "pattern": "independent"},
        height=250,
        title_text="<b>KPIs Estratégicos del Negocio</b>",
        template=TEMPLATE,
    )
    fig.show()


# ============================================================================
# 2. ANÁLISIS DE ELASTICIDAD (CORE DEL NEGOCIO)
# ============================================================================
def analisis_elasticidad_precio(df):
    print("📉 Analizando Elasticidad de Precios...")

    # Muestreo para que el gráfico no sea pesado si hay muchos datos
    df_sample = df.sample(n=min(5000, len(df)), random_state=42)

    # Scatter plot con líneas de tendencia por categoría
    # Esto demuestra visualmente que a mayor precio, menor demanda (la curva)
    fig = px.scatter(
        df_sample,
        x="Price",
        y="demand",
        color="ProductCategory",
        trendline="lowess",  # Línea de tendencia suave no lineal
        title="<b>Curvas de Demanda: Sensibilidad al Precio por Categoría</b><br><i>(Muestra cómo cae la venta al subir el precio)</i>",
        labels={
            "Price": "Precio Unitario ($)",
            "demand": "Unidades Vendidas (Demanda)",
            "ProductCategory": "Categoría",
        },
        opacity=0.4,
        color_discrete_sequence=COLOR_PALETTE,
    )

    fig.update_layout(height=600, template=TEMPLATE)
    fig.show()


# ============================================================================
# 3. ANÁLISIS TEMPORAL (HEATMAPS)
# ============================================================================
def analisis_temporal_negocio(df):
    print("📅 Analizando Patrones Temporales...")

    # Agregación para Heatmap: Día de la Semana vs Hora
    # Mapeo de días
    dias_map = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo",
    }
    df["dia_nombre"] = df["day_of_week"].map(dias_map)

    heatmap_data = df.groupby(["dia_nombre", "hour"])["revenue"].sum().reset_index()

    # Ordenar días correctamente para el gráfico
    orden_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data["revenue"],
            x=heatmap_data["hour"],
            y=heatmap_data["dia_nombre"],
            colorscale="Viridis",
            colorbar=dict(title="Ingresos ($)"),
        )
    )

    fig.update_yaxes(categoryorder="array", categoryarray=orden_dias)
    fig.update_layout(
        title="<b>Mapa de Calor de Ventas: ¿Cuándo vendemos más?</b><br><i>(Intensidad de Ingresos por Día y Hora)</i>",
        xaxis_title="Hora del Día",
        yaxis_title="Día de la Semana",
        height=500,
        template=TEMPLATE,
    )
    fig.show()

    # Serie temporal diaria (Ingresos vs Profit)
    daily_metrics = (
        df.groupby("Date")
        .agg({"revenue": "sum", "estimated_profit": "sum"})
        .reset_index()
    )

    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=daily_metrics["Date"],
            y=daily_metrics["revenue"],
            mode="lines",
            name="Ingresos",
            line=dict(color="blue"),
        )
    )
    fig2.add_trace(
        go.Scatter(
            x=daily_metrics["Date"],
            y=daily_metrics["estimated_profit"],
            mode="lines",
            name="Beneficio",
            line=dict(color="green", dash="dot"),
        )
    )

    fig2.update_layout(
        title="<b>Evolución Financiera Diaria</b>",
        yaxis_title="Monto ($)",
        height=400,
        template=TEMPLATE,
        hovermode="x unified",
    )
    fig2.show()


# ============================================================================
# 4. PARETO DE PRODUCTOS (80/20)
# ============================================================================
def analisis_pareto_productos(df):
    print("📦 Analizando Performance de Productos (Pareto)...")

    # Agrupar por producto
    prod_perf = (
        df.groupby("ProductID")
        .agg({"revenue": "sum"})
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

    # Calcular acumulados
    prod_perf["revenue_acum"] = prod_perf["revenue"].cumsum()
    prod_perf["pct_acum"] = (
        prod_perf["revenue_acum"] / prod_perf["revenue"].sum()
    ) * 100
    prod_perf["pct_productos"] = ((prod_perf.index + 1) / len(prod_perf)) * 100

    # Solo mostramos el top 50 para que el gráfico sea legible
    top_50 = prod_perf.head(50)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Barras: Ingreso por producto
    fig.add_trace(
        go.Bar(
            x=top_50["ProductID"],
            y=top_50["revenue"],
            name="Ingresos ($)",
            marker_color="rgb(55, 83, 109)",
        ),
        secondary_y=False,
    )

    # Línea: % Acumulado
    fig.add_trace(
        go.Scatter(
            x=top_50["ProductID"],
            y=top_50["pct_acum"],
            name="% Acumulado",
            mode="lines+markers",
            marker_color="rgb(26, 118, 255)",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="<b>Análisis de Pareto (Top 50 Productos)</b><br><i>Identificando los productos estrella que generan el 80% del ingreso</i>",
        template=TEMPLATE,
        height=600,
        showlegend=True,
    )
    fig.update_yaxes(title_text="Ingresos ($)", secondary_y=False)
    fig.update_yaxes(
        title_text="% Acumulado del Total", range=[0, 110], secondary_y=True
    )

    fig.show()


# ============================================================================
# 5. RENTABILIDAD POR CATEGORÍA
# ============================================================================
def analisis_rentabilidad_categoria(df):
    print("💰 Analizando Rentabilidad por Categoría...")

    cat_metrics = (
        df.groupby("ProductCategory")
        .agg(
            {
                "revenue": "sum",
                "estimated_profit": "sum",
                "estimated_margin_pct": "mean",
                "demand": "sum",
            }
        )
        .reset_index()
    )

    # Bubble Chart: X=Ingresos, Y=Margen %, Tamaño=Demanda
    fig = px.scatter(
        cat_metrics,
        x="revenue",
        y="estimated_margin_pct",
        size="demand",
        color="ProductCategory",
        hover_name="ProductCategory",
        size_max=60,
        title="<b>Matriz de Rentabilidad por Categoría</b><br><i>(Eje X: Cuánto vende | Eje Y: Qué tan rentable es | Tamaño: Volumen de unidades)</i>",
        labels={
            "revenue": "Ingresos Totales ($)",
            "estimated_margin_pct": "Margen Promedio (%)",
        },
        color_discrete_sequence=COLOR_PALETTE,
    )

    # Líneas promedio para cuadrantes
    avg_rev = cat_metrics["revenue"].mean()
    avg_mar = cat_metrics["estimated_margin_pct"].mean()

    fig.add_hline(
        y=avg_mar,
        line_dash="dot",
        annotation_text="Margen Promedio",
        annotation_position="bottom right",
    )
    fig.add_vline(
        x=avg_rev,
        line_dash="dot",
        annotation_text="Ingreso Promedio",
        annotation_position="top left",
    )

    fig.update_layout(height=600, template=TEMPLATE)
    fig.show()


# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    # Asumimos que ya tienes la clase GetData importada o definida arriba
    from src.dynamic_pricing_model import GetData

    print("🔄 Cargando datos simulados...")
    # Instanciamos tu clase (asegúrate de que GetData esté disponible)
    data_loader = GetData()
    df_final, _ = data_loader.get_data()

    # Ejecutamos el Dashboard
    generar_dashboard_negocio(df_final)
