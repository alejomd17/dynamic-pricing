import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime
import pandas as pd
import numpy as np

# Importamos tu clase de datos (asegúrate de que el archivo se llame get_data.py o ajusta el import)
from get_data import GetData

# Configuración de Estilo
COLOR_PALETTE = px.colors.qualitative.Prism
TEMPLATE = "plotly_white"


class DashboardGenerator:
    def __init__(self, title="Reporte Estratégico de Pricing"):
        self.title = title
        self.sections = []
        self.html_head = """
        <head>
            <meta charset="utf-8">
            <title>Dashboard Ejecutivo</title>
            <style>
                body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header h1 { margin: 0; font-size: 2.5em; }
                .header p { margin: 10px 0 0; opacity: 0.8; }
                .card { background: white; border-radius: 8px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                .card h2 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
                .kpi-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }
                .kpi-card { flex: 1; background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-top: 4px solid #1e3c72; }
                .kpi-value { font-size: 2.5em; font-weight: bold; color: #1e3c72; margin: 10px 0; }
                .kpi-label { color: #7f8c8d; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
                .footer { text-align: center; color: #95a5a6; margin-top: 50px; font-size: 0.8em; }
            </style>
        </head>
        """

    def add_header(self):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        html = f"""
        <div class="header">
            <h1>{self.title}</h1>
            <p>Estado del Proyecto | Generado: {timestamp}</p>
        </div>
        """
        self.sections.append(html)

    def add_kpis(self, df):
        """Genera el bloque HTML de KPIs"""
        total_rev = df["revenue"].sum()
        total_profit = df["estimated_profit"].sum()
        margin = (total_profit / total_rev) * 100
        avg_ticket = df["revenue"].sum() / df["demand"].sum()

        kpi_html = f"""
        <div class="kpi-container">
            <div class="kpi-card" style="border-top-color: #2ecc71;">
                <div class="kpi-label">Ingresos Totales</div>
                <div class="kpi-value">${total_rev:,.0f}</div>
            </div>
            <div class="kpi-card" style="border-top-color: #3498db;">
                <div class="kpi-label">Beneficio (Profit)</div>
                <div class="kpi-value">${total_profit:,.0f}</div>
            </div>
            <div class="kpi-card" style="border-top-color: #f1c40f;">
                <div class="kpi-label">Margen Global</div>
                <div class="kpi-value">{margin:.1f}%</div>
            </div>
            <div class="kpi-card" style="border-top-color: #9b59b6;">
                <div class="kpi-label">Ticket Promedio</div>
                <div class="kpi-value">${avg_ticket:.2f}</div>
            </div>
        </div>
        """
        self.sections.append(kpi_html)

    def add_title(self, text, anchor_id):
        self.sections.append(
            f'<a id="{anchor_id}" class="anchor"></a><h2 class="section-title">{text}</h2>'
        )

    def add_plot(self, fig, title, description=""):
        """Convierte una figura Plotly a HTML y la añade al reporte"""
        # Convertir figura a HTML div (sin el full html wrapper)
        plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

        section_html = f"""
        <div class="card">
            <h2>{title}</h2>
            <p style="color: #666; margin-bottom: 20px;">{description}</p>
            {plot_html}
        </div>
        """
        self.sections.append(section_html)

    def add_tech_table(self, df):
        """Genera una tabla de calidad de datos (EDA Técnico)"""
        tech_data = []
        for col in df.columns:
            tech_data.append(
                {
                    "Columna": col,
                    "Tipo": str(df[col].dtype),
                    "Nulos": df[col].isnull().sum(),
                    "Únicos": df[col].nunique(),
                    "Ejemplo": str(df[col].iloc[0])[:30],
                }
            )

        df_tech = pd.DataFrame(tech_data)
        table_html = df_tech.to_html(classes="tech_table", index=False, border=0)
        # Inyectamos la clase tech-table
        table_html = table_html.replace(
            'class="dataframe tech_table"', 'class="tech-table"'
        )

        self.sections.append(
            f'<div class="card"><h3>Análisis de Calidad de Datos</h3>{table_html}</div>'
        )

    def save(self, filename="Dashboard_Pricing_Final.html"):
        body_content = "\n".join(self.sections)
        full_html = f"""<!DOCTYPE html><html>{self.html_head}<body>
            <div class="sidebar">
                <h2 style="color:white; margin-bottom:30px;">Pricing v2.0</h2>
                <a href="#negocio" class="nav-link">📈 Vista de Negocio</a>
                <a href="#elasticidad" class="nav-link">📉 Elasticidad Detalle</a>
                <a href="#tecnico" class="nav-link">⚙️ Vista Técnica (EDA)</a>
            </div>
            <div class="main-content">{body_content}</div>
        </body></html>"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"✅ Reporte guardado: {filename}")


# ============================================================================
# LÓGICA DE GRÁFICOS
# ============================================================================


def generar_reporte_completo(df, report):
    report.add_header()
    report.add_kpis(df)

    # --- SECCIÓN 1: NEGOCIO ---
    report.add_title("Vista de Negocio & Estrategia", "negocio")

    # 1. Serie Temporal
    daily_sales = df.groupby("Date").agg({"revenue": "sum"}).reset_index()
    fig_time = px.line(
        daily_sales,
        x="Date",
        y="revenue",
        title="Evolución Diaria de Ingresos",
        line_shape="spline",
    )
    report.add_plot(
        fig_time,
        "Tendencia Temporal",
        "Visualización de la facturación a lo largo del tiempo para detectar estacionalidad.",
    )

    # 2. Heatmap Temporal
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
    orden_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=heatmap_data["revenue"],
            x=heatmap_data["hour"],
            y=heatmap_data["dia_nombre"],
            colorscale="Viridis",
        )
    )
    fig_heat.update_yaxes(categoryorder="array", categoryarray=orden_dias)
    report.add_plot(
        fig_heat,
        "Mapa de Calor de Ventas",
        "Identifica los momentos de mayor facturación (Día vs Hora).",
    )

    # 3. Pareto
    prod_perf = (
        df.groupby("ProductID")
        .agg({"revenue": "sum"})
        .sort_values("revenue", ascending=False)
        .reset_index()
    )
    prod_perf["pct_acum"] = (
        prod_perf["revenue"].cumsum() / prod_perf["revenue"].sum() * 100
    )
    top_50 = prod_perf.head(50)
    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
    fig_pareto.add_trace(
        go.Bar(
            x=top_50["ProductID"],
            y=top_50["revenue"],
            name="Ingresos",
            marker_color="#1e3c72",
        ),
        secondary_y=False,
    )
    fig_pareto.add_trace(
        go.Scatter(
            x=top_50["ProductID"],
            y=top_50["pct_acum"],
            name="% Acumulado",
            marker_color="#e74c3c",
        ),
        secondary_y=True,
    )
    report.add_plot(
        fig_pareto,
        "Análisis de Pareto (Top 50 Productos)",
        "Muestra qué productos generan el 80% de los ingresos.",
    )

    # 4. Rentabilidad
    cat_metrics = (
        df.groupby("ProductCategory")
        .agg({"revenue": "sum", "estimated_margin_pct": "mean", "demand": "sum"})
        .reset_index()
    )
    fig_bubble = px.scatter(
        cat_metrics,
        x="revenue",
        y="estimated_margin_pct",
        size="demand",
        color="ProductCategory",
        size_max=60,
    )
    report.add_plot(
        fig_bubble,
        "Matriz de Rentabilidad",
        "Relación entre volumen de facturación y margen por categoría.",
    )

    # --- SECCIÓN 2: ELASTICIDAD ---
    report.add_title("Estudio de Elasticidad Detallado", "elasticidad")

    # 5. Scatter Elasticidad
    df_sample = df.sample(n=min(2000, len(df)), random_state=42)
    fig_elast_scatter = px.scatter(
        df_sample,
        x="Price",
        y="demand",
        color="ProductCategory",
        trendline="lowess",
        opacity=0.5,
    )
    report.add_plot(
        fig_elast_scatter,
        "Sensibilidad al Precio (Visual)",
        "Curvas de demanda por categoría. Pendientes más pronunciadas indican mayor sensibilidad.",
    )

    # 6. Coeficientes de Elasticidad (NUEVO)
    results = []
    for cat in df["ProductCategory"].unique():
        sub = df[df["ProductCategory"] == cat]
        if len(sub) > 10:
            coef = np.polyfit(np.log(sub["Price"] + 1), np.log(sub["demand"] + 1), 1)[0]
            results.append({"Categoría": cat, "Elasticidad": round(coef, 2)})
    df_coef = pd.DataFrame(results).sort_values("Elasticidad")
    fig_coef = px.bar(
        df_coef,
        x="Categoría",
        y="Elasticidad",
        color="Elasticidad",
        color_continuous_scale="RdYlGn",
    )
    report.add_plot(
        fig_coef,
        "Coeficientes Numéricos de Elasticidad",
        "Valores negativos indican que al subir el precio baja la demanda. -2.5 es más sensible que -0.5.",
    )

    # --- SECCIÓN 3: TÉCNICO ---
    report.add_title("Vista Técnica & EDA Tradicional", "tecnico")

    report.add_tech_table(df)

    # 7. Distribución de Filas por Categoría (NUEVO)
    cat_counts = df["ProductCategory"].value_counts().reset_index()
    fig_pie = px.pie(
        cat_counts,
        names="ProductCategory",
        values="count",
        hole=0.4,
        title="Distribución de Datos por Categoría",
    )
    report.add_plot(
        fig_pie,
        "Balance del Dataset",
        "Cantidad de registros disponibles por cada categoría de producto.",
    )

    # 8. Distribución de Demanda (NUEVO)
    fig_hist = px.histogram(
        df,
        x="demand",
        nbins=20,
        title="Distribución de Cantidades Vendidas",
        color_discrete_sequence=["#2a5298"],
    )
    report.add_plot(
        fig_hist,
        "Histograma de Demanda",
        "Frecuencia de las cantidades solicitadas en las transacciones.",
    )


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    loader = GetData()
    df_final, _ = loader.get_data()

    reporte = DashboardGenerator("Dashboard Estratégico: Pricing & Demand")
    generar_reporte_completo(df_final, reporte)
    reporte.save("Dashboard_Pricing_Final.html")
