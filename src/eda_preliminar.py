
"""
PLANTILLA PARA USAR TUS DATOS REALES
====================================
Copia este código y reemplaza con tus archivos CSV
"""
import pandas as pd
from dynamic_pricing_real_data import DynamicPricingModelReal

# ============================================================================
# PASO 1: CARGAR TUS DATOS DESDE CSV
# ============================================================================

print("Cargando datos desde CSV...")

# 1.1 TRANSACCIONES (OBLIGATORIO)
# --------------------------------
# Tu archivo debe tener estas columnas:
# - CustomerID
# - ProductID  
# - Quantity
# - Price
# - TransactionDate (formato: MM/DD/YYYY HH:MM o similar)
# - PaymentMethod
# - StoreLocation
# - ProductCategory
# - DiscountApplied(%)
# - TotalAmount


# 1.2 INFLACIÓN (OPCIONAL pero recomendado)
# ------------------------------------------
# Tu archivo debe tener:
# - Date (mismo formato que TransactionDate)
# - InflationRate (como decimal, ej: 0.045 para 4.5%)

try:
    inflation_df = pd.read_csv('inflacion.csv')  # 👈 REEMPLAZA CON TU ARCHIVO
    print(f"\n✓ Inflación cargada: {len(inflation_df):,} filas")
    print(f"  Rango: {inflation_df['InflationRate'].min():.2%} - {inflation_df['InflationRate'].max():.2%}")
except FileNotFoundError:
    print("\n⚠ Archivo de inflación no encontrado - continuando sin inflación")
    inflation_df = None


# 1.3 TEMPERATURA (OPCIONAL)
# ---------------------------
# Tu archivo debe tener:
# - Date
# - Temperature (en Celsius o Fahrenheit, tú decides)

try:
    temperature_df = pd.read_csv('temperatura.csv')  # 👈 REEMPLAZA CON TU ARCHIVO
    print(f"\n✓ Temperatura cargada: {len(temperature_df):,} filas")
    print(f"  Rango: {temperature_df['Temperature'].min():.1f}° - {temperature_df['Temperature'].max():.1f}°")
except FileNotFoundError:
    print("\n⚠ Archivo de temperatura no encontrado - continuando sin temperatura")
    temperature_df = None


# 1.4 PRECIOS DE COMPETENCIA (OPCIONAL - para cuando los consigas)
# ------------------------------------------------------------------
# Tu archivo debe tener:
# - Date
# - ProductID (debe coincidir con ProductID en transacciones)
# - CompetitorPrice

try:
    competitor_prices_df = pd.read_csv('precios_competencia.csv')  # 👈 AGREGA CUANDO LOS TENGAS
    print(f"\n✓ Precios competencia cargados: {len(competitor_prices_df):,} filas")
except FileNotFoundError:
    print("\n⚠ Precios de competencia no disponibles - continuando sin ellos")
    competitor_prices_df = None

# ============================================================================
# PASO 2: INICIALIZAR MODELO
# ============================================================================

print("\n" + "="*70)
print("INICIALIZANDO MODELO")
print("="*70 + "\n")

# Especifica el costo unitario promedio de tus productos
# Si tienes diferentes costos por producto, los puedes especificar después
model = DynamicPricingModelReal(cost_per_unit_default=30)  # 👈 AJUSTA TU COSTO


# ============================================================================
# PASO 3: PREPARAR DATOS
# ============================================================================

df_aggregated, df_detailed = model.load_and_prepare_data(
    transactions_df=transactions_df,
    inflation_df=inflation_df,
    temperature_df=temperature_df,
    competitor_prices_df=competitor_prices_df
)

# Guardar datos procesados (opcional)
df_aggregated.to_csv('datos_procesados_agregados.csv', index=False)
df_detailed.to_csv('datos_procesados_detallados.csv', index=False)

print("\n✓ Datos procesados guardados")


# ============================================================================
# PASO 4: ENTRENAR MODELO
# ============================================================================

X_test, y_test, y_pred, feature_importance = model.train_demand_model(df_aggregated)

# Guardar feature importance
feature_importance.to_csv('feature_importance.csv', index=False)


# ============================================================================
# PASO 5: ANÁLISIS POR PRODUCTO
# ============================================================================

print("\n" + "="*70)
print("ANÁLISIS POR PRODUCTO")
print("="*70 + "\n")

# Obtener productos únicos de tus datos
productos = df_aggregated['ProductID'].unique()

resultados_por_producto = []

for producto in productos[:5]:  # Primeros 5 productos como ejemplo
    
    # Filtrar datos del producto
    df_producto = df_aggregated[df_aggregated['ProductID'] == producto]
    
    # Precio y demanda promedio actual
    precio_actual = df_producto['Price'].mean()
    demanda_actual = df_producto['demand'].mean()
    
    # Contexto típico para este producto
    context = {
        'Price': precio_actual,
        'day_of_week': 3,  # Miércoles promedio
        'hour': 14,
        'is_weekend': 0,
        'month': 6,
        'quarter': 2,
        'has_discount': 0,
        'discount_level': 0,
        'category_encoded': df_producto['category_encoded'].mode()[0],
        'store_encoded': df_producto['store_encoded'].mode()[0],
        'payment_cash': df_producto['payment_cash'].mean(),
        'payment_card': df_producto['payment_card'].mean(),
    }
    
    # Agregar inflación y temperatura si existen
    if inflation_df is not None:
        context['InflationRate'] = df_producto['InflationRate'].mean()
    
    if temperature_df is not None:
        context['Temperature'] = df_producto['Temperature'].mean()
    
    if competitor_prices_df is not None:
        context['CompetitorPrice'] = df_producto['CompetitorPrice'].mean()
        context['price_vs_competitor'] = precio_actual / context['CompetitorPrice']
    
    # Optimizar precio
    try:
        resultado = model.optimize_price(
            context,
            cost_per_unit=30,  # 👈 Puedes especificar costo por producto aquí
            objective='profit',
            price_bounds=(precio_actual * 0.7, precio_actual * 1.5)
        )
        
        # Calcular elasticidad
        elasticity, _, _ = model.calculate_price_elasticity(context)
        
        resultados_por_producto.append({
            'ProductID': producto,
            'precio_actual': precio_actual,
            'demanda_actual': demanda_actual,
            'precio_optimo': resultado['optimal_price'],
            'demanda_optima': resultado['predicted_demand'],
            'profit_actual': demanda_actual * (precio_actual - 30),
            'profit_optimo': resultado['expected_profit'],
            'mejora_profit': resultado['expected_profit'] - demanda_actual * (precio_actual - 30),
            'mejora_profit_pct': ((resultado['expected_profit'] - demanda_actual * (precio_actual - 30)) / 
                                 max(demanda_actual * (precio_actual - 30), 1)) * 100,
            'elasticidad': elasticity
        })
        
        print(f"\nProducto: {producto}")
        print(f"  Precio actual: ${precio_actual:.2f}")
        print(f"  Precio óptimo: ${resultado['optimal_price']:.2f}")
        print(f"  Cambio sugerido: {((resultado['optimal_price'] - precio_actual) / precio_actual * 100):+.1f}%")
        print(f"  Mejora en profit: ${resultado['expected_profit'] - demanda_actual * (precio_actual - 30):+,.2f}")
        print(f"  Elasticidad: {elasticity:.3f}")
        
    except Exception as e:
        print(f"\nProducto: {producto}")
        print(f"  ⚠ Error al optimizar: {e}")

# Guardar resultados
df_resultados = pd.DataFrame(resultados_por_producto)
df_resultados.to_csv('optimizacion_por_producto.csv', index=False)

print("\n✓ Resultados guardados en 'optimizacion_por_producto.csv'")


# ============================================================================
# PASO 6: ANÁLISIS POR CATEGORÍA
# ============================================================================

print("\n" + "="*70)
print("ANÁLISIS POR CATEGORÍA")
print("="*70 + "\n")

categorias_performance = df_aggregated.groupby('ProductCategory').agg({
    'demand': 'sum',
    'Price': 'mean',
    'TotalAmount': 'sum',
    'has_discount': 'mean',
    'DiscountApplied(%)': 'mean'
}).round(2)

print(categorias_performance)

categorias_performance.to_csv('performance_por_categoria.csv')


# ============================================================================
# PASO 7: SIMULACIÓN DE ESCENARIOS
# ============================================================================

print("\n" + "="*70)
print("SIMULACIÓN DE ESCENARIOS")
print("="*70 + "\n")

# Escenario base (condiciones promedio)
escenario_base = {
    'Price': 50,
    'day_of_week': 3,
    'hour': 14,
    'is_weekend': 0,
    'month': 6,
    'quarter': 2,
    'has_discount': 0,
    'discount_level': 0,
    'category_encoded': 0,
    'store_encoded': 0,
    'payment_cash': 0.3,
    'payment_card': 0.7,
}

if inflation_df is not None:
    escenario_base['InflationRate'] = inflation_df['InflationRate'].mean()

if temperature_df is not None:
    escenario_base['Temperature'] = temperature_df['Temperature'].mean()

escenarios = {
    'Condiciones Normales': escenario_base.copy(),
    'Fin de Semana': {**escenario_base, 'is_weekend': 1, 'day_of_week': 6},
    'Con Descuento 10%': {**escenario_base, 'has_discount': 1, 'discount_level': 1},
    'Alta Inflación': {**escenario_base, 'InflationRate': 0.08} if inflation_df is not None else None,
    'Verano Caluroso': {**escenario_base, 'Temperature': 35, 'month': 7} if temperature_df is not None else None
}

# Filtrar escenarios None
escenarios = {k: v for k, v in escenarios.items() if v is not None}

print("Comparación de escenarios:\n")

for nombre, escenario in escenarios.items():
    resultado = model.optimize_price(escenario, cost_per_unit=30, objective='profit')
    print(f"{nombre:25s} → Precio: ${resultado['optimal_price']:6.2f}  |  Profit: ${resultado['expected_profit']:8,.2f}")


# ============================================================================
# PASO 8: AGREGAR NUEVAS VARIABLES CUANDO LAS CONSIGAS
# ============================================================================

print("\n" + "="*70)
print("CÓMO AGREGAR NUEVAS VARIABLES EN EL FUTURO")
print("="*70 + "\n")

print("""
Cuando consigas nuevas variables (ej: precios de competencia, gastos de marketing):

1. Cargar nueva variable:
   nueva_variable = pd.read_csv('nueva_data.csv')

2. Agregar al modelo:
   df_aggregated = model.add_new_feature(
       df_aggregated, 
       'nombre_variable', 
       nueva_variable
   )

3. Re-entrenar:
   model.train_demand_model(df_aggregated)

4. Las optimizaciones ahora incluirán la nueva variable automáticamente!

Ejemplos de variables que puedes agregar:
- Precios de competencia
- Gastos de marketing
- Stock/inventario
- Eventos especiales
- Tráfico de la tienda
- Indicadores económicos adicionales
""")

print("\n" + "="*70)
print("✅ ANÁLISIS COMPLETO TERMINADO")
print("="*70 + "\n")

print("Archivos generados:")
print("  1. datos_procesados_agregados.csv")
print("  2. datos_procesados_detallados.csv")
print("  3. feature_importance.csv")
print("  4. optimizacion_por_producto.csv")
print("  5. performance_por_categoria.csv")
