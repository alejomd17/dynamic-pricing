"""
Dynamic Pricing Model
===================================================
Modelo de Dynamic Pricing utilizando datos reales de transacciones minoristas.
Se incluyen features adicionales como inflación, temperatura y precios de competencia
cuando estén disponibles.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')


class DynamicPricingModelReal:
    """
    Modelo de Dynamic Pricing 
    """
    
    def __init__(self, cost_per_unit_default=None):
        self.demand_model = None
        self.scaler = StandardScaler()
        self.cost_per_unit_default = cost_per_unit_default
        self.feature_names = None
        self.product_costs = {}  # Costos por producto
        self.available_features = set()  # Features disponibles
        
    def load_and_prepare_data(self, 
                              transactions_df, 
                              inflation_df=None, 
                              temperature_df=None,
                              competitor_prices_df=None):
        """
        Carga y prepara tus datos reales
        
        Parameters:
        -----------
        transactions_df: DataFrame con columnas:
            - CustomerID
            - ProductID
            - Quantity
            - Price
            - TransactionDate
            - PaymentMethod
            - StoreLocation
            - ProductCategory
            - DiscountApplied(%)
            - TotalAmount
            
        inflation_df: DataFrame con columnas [Date, InflationRate] (opcional)
        temperature_df: DataFrame con columnas [Date, Temperature] (opcional)
        competitor_prices_df: DataFrame con [Date, ProductID, CompetitorPrice] (opcional)
        """
        
        print("="*70)
        print("PREPARANDO DATOS")
        print("="*70)
        
        # 1. Copiar y limpiar transacciones
        df = transactions_df.copy()
        
        # 2. Convertir fecha
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
        df['Date'] = df['TransactionDate'].dt.date
        
        # 3. Extraer features temporales
        df['year'] = df['TransactionDate'].dt.year
        df['month'] = df['TransactionDate'].dt.month
        df['day_of_week'] = df['TransactionDate'].dt.dayofweek
        df['day_of_month'] = df['TransactionDate'].dt.day
        df['hour'] = df['TransactionDate'].dt.hour
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['quarter'] = df['TransactionDate'].dt.quarter
        
        # 4. Categorizar método de pago
        df['payment_cash'] = (df['PaymentMethod'] == 'Cash').astype(int)
        df['payment_card'] = (df['PaymentMethod'].isin(['Credit Card', 'Debit Card'])).astype(int)
        
        # 5. Encodear categorías de producto
        df['category_encoded'] = pd.Categorical(df['ProductCategory']).codes
        
        # 6. Features de descuento
        df['has_discount'] = (df['DiscountApplied(%)'] > 0).astype(int)
        df['discount_level'] = pd.cut(
            df['DiscountApplied(%)'], 
            bins=[-0.1, 0, 10, 20, 100],
            labels=[0, 1, 2, 3]
        ).astype(int)
        
        # 7. Encodear ubicación de tienda
        df['store_encoded'] = pd.Categorical(df['StoreLocation']).codes
        
        # 8. Features derivadas
        df['price_per_unit'] = df['Price'] / df['Quantity']
        df['discount_amount'] = df['TotalAmount'] * (df['DiscountApplied(%)'] / 100)
        
        # Registrar features básicas disponibles
        self.available_features = {
            'price', 'day_of_week', 'hour', 'is_weekend', 'month', 
            'quarter', 'has_discount', 'discount_level', 'category_encoded',
            'store_encoded', 'payment_cash', 'payment_card'
        }
        
        print(f"✓ Transacciones cargadas: {len(df):,}")
        print(f"✓ Periodo: {df['Date'].min()} a {df['Date'].max()}")
        print(f"✓ Productos únicos: {df['ProductID'].nunique()}")
        print(f"✓ Categorías: {df['ProductCategory'].nunique()}")
        
        # 9. MERGE CON INFLACIÓN (si está disponible)
        if inflation_df is not None:
            inflation_df = inflation_df.copy()
            inflation_df['Date'] = pd.to_datetime(inflation_df['Date']).dt.date
            
            df = df.merge(
                inflation_df[['Date', 'InflationRate']], 
                on='Date', 
                how='left'
            )
            
            # Rellenar valores faltantes con la media o forward fill
            df['InflationRate'] = df['InflationRate'].fillna(method='ffill').fillna(0)
            
            self.available_features.add('inflation_rate')
            print(f"✓ Inflación agregada: {inflation_df['InflationRate'].min():.2%} - {inflation_df['InflationRate'].max():.2%}")
        else:
            print("⚠ Inflación NO disponible (se agregará cuando la tengas)")
        
        # 10. MERGE CON TEMPERATURA (si está disponible)
        if temperature_df is not None:
            temperature_df = temperature_df.copy()
            temperature_df['Date'] = pd.to_datetime(temperature_df['Date']).dt.date
            
            df = df.merge(
                temperature_df[['Date', 'Temperature']], 
                on='Date', 
                how='left'
            )
            
            df['Temperature'] = df['Temperature'].fillna(df['Temperature'].mean())
            
            self.available_features.add('temperature')
            print(f"✓ Temperatura agregada: {df['Temperature'].min():.1f}°C - {df['Temperature'].max():.1f}°C")
        else:
            print("⚠ Temperatura NO disponible (se agregará cuando la tengas)")
        
        # 11. MERGE CON PRECIOS DE COMPETENCIA (si están disponibles)
        if competitor_prices_df is not None:
            competitor_prices_df = competitor_prices_df.copy()
            competitor_prices_df['Date'] = pd.to_datetime(competitor_prices_df['Date']).dt.date
            
            df = df.merge(
                competitor_prices_df[['Date', 'ProductID', 'CompetitorPrice']], 
                on=['Date', 'ProductID'], 
                how='left'
            )
            
            # Rellenar con precio propio si no hay competidor
            df['CompetitorPrice'] = df['CompetitorPrice'].fillna(df['Price'])
            df['price_vs_competitor'] = df['Price'] / df['CompetitorPrice']
            
            self.available_features.add('competitor_price')
            self.available_features.add('price_vs_competitor')
            print(f"✓ Precios de competencia agregados")
        else:
            print("⚠ Precios de competencia NO disponibles (se agregarán cuando los consigas)")
        
        # 12. Calcular DEMANDA (agregada por día/producto/precio)
        # La demanda es la suma de Quantity vendida a cada nivel de precio
        df_aggregated = df.groupby(['Date', 'ProductID', 'Price', 'ProductCategory']).agg({
            'Quantity': 'sum',  # DEMANDA
            'CustomerID': 'count',  # Número de transacciones
            'TotalAmount': 'sum',
            'day_of_week': 'first',
            'hour': 'mean',
            'is_weekend': 'first',
            'month': 'first',
            'quarter': 'first',
            'has_discount': 'max',
            'discount_level': 'max',
            'DiscountApplied(%)': 'mean',
            'category_encoded': 'first',
            'store_encoded': 'first',  # Changed from mode to first
            'payment_cash': 'mean',
            'payment_card': 'mean'
        }).reset_index()
        
        # Renombrar para claridad
        df_aggregated.rename(columns={'Quantity': 'demand'}, inplace=True)
        
        # Agregar inflación y temperatura si existen
        if inflation_df is not None:
            df_aggregated = df_aggregated.merge(
                df[['Date', 'InflationRate']].drop_duplicates(),
                on='Date',
                how='left'
            )
        
        if temperature_df is not None:
            df_aggregated = df_aggregated.merge(
                df[['Date', 'Temperature']].drop_duplicates(),
                on='Date',
                how='left'
            )
        
        if competitor_prices_df is not None:
            df_aggregated = df_aggregated.merge(
                df[['Date', 'ProductID', 'CompetitorPrice', 'price_vs_competitor']].drop_duplicates(),
                on=['Date', 'ProductID'],
                how='left'
            )
        
        print(f"\n✓ Datos agregados: {len(df_aggregated):,} observaciones precio-demanda")
        print(f"✓ Features disponibles: {len(self.available_features)}")
        print(f"  {sorted(self.available_features)}")
        
        print("="*70 + "\n")
        
        return df_aggregated, df  # Retorna agregado y detallado
    
    def prepare_features(self, df):
        """
        Prepara features dinámicamente según lo que esté disponible
        """
        feature_cols = ['Price']
        
        # Agregar features según disponibilidad
        always_available = [
            'day_of_week', 'hour', 'is_weekend', 'month', 'quarter',
            'has_discount', 'discount_level', 'category_encoded',
            'store_encoded', 'payment_cash', 'payment_card'
        ]
        
        for feat in always_available:
            if feat in df.columns:
                feature_cols.append(feat)
        
        # Features opcionales
        if 'InflationRate' in df.columns:
            feature_cols.append('InflationRate')
        
        if 'Temperature' in df.columns:
            feature_cols.append('Temperature')
        
        if 'CompetitorPrice' in df.columns:
            feature_cols.append('CompetitorPrice')
            feature_cols.append('price_vs_competitor')
        
        return df[feature_cols]
    
    def train_demand_model(self, df_aggregated):
        """
        Entrena el modelo de predicción de demanda
        """
        X = self.prepare_features(df_aggregated)
        y = df_aggregated['demand']
        
        self.feature_names = X.columns.tolist()
        
        print("="*70)
        print("ENTRENAMIENTO DEL MODELO")
        print("="*70)
        print(f"Features utilizadas ({len(self.feature_names)}):")
        for i, feat in enumerate(self.feature_names, 1):
            print(f"  {i}. {feat}")
        print()
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        # Escalar
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entrenar
        self.demand_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            random_state=42
        )
        
        self.demand_model.fit(X_train_scaled, y_train)
        
        # Evaluar
        y_pred_train = self.demand_model.predict(X_train_scaled)
        y_pred_test = self.demand_model.predict(X_test_scaled)
        
        print("RESULTADOS:")
        print("-" * 70)
        print(f"R² Train: {r2_score(y_train, y_pred_train):.4f}")
        print(f"R² Test:  {r2_score(y_test, y_pred_test):.4f}")
        print(f"RMSE Train: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.2f}")
        print(f"RMSE Test:  {np.sqrt(mean_squared_error(y_test, y_pred_test)):.2f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.demand_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nIMPORTANCIA DE FEATURES:")
        print("-" * 70)
        for _, row in feature_importance.iterrows():
            bar_length = int(row['importance'] * 50)
            bar = '█' * bar_length
            print(f"{row['feature']:25s} {bar} {row['importance']:.4f}")
        
        print("="*70 + "\n")
        
        return X_test, y_test, y_pred_test, feature_importance
    
    def predict_demand(self, features_dict):
        """
        Predice demanda dado un contexto
        """
        # Crear DataFrame con solo las features que el modelo espera
        feature_values = {}
        for feat in self.feature_names:
            if feat in features_dict:
                feature_values[feat] = features_dict[feat]
            else:
                # Valor por defecto si no está en el contexto
                feature_values[feat] = 0
        
        df = pd.DataFrame([feature_values])
        X_scaled = self.scaler.transform(df)
        
        return max(0, self.demand_model.predict(X_scaled)[0])
    
    def optimize_price(self, context, cost_per_unit=None, 
                      objective='profit', price_bounds=None):
        """
        Optimiza precio dado un contexto
        """
        if cost_per_unit is None:
            cost_per_unit = self.cost_per_unit_default
            
        if cost_per_unit is None:
            raise ValueError("Debes especificar cost_per_unit")
        
        # Auto-determinar bounds si no se especifican
        if price_bounds is None:
            current_price = context.get('Price', 50)
            price_bounds = (current_price * 0.5, current_price * 2.0)
        
        def objective_function(price):
            ctx = context.copy()
            ctx['Price'] = price[0]
            
            # Actualizar price_vs_competitor si existe
            if 'CompetitorPrice' in ctx:
                ctx['price_vs_competitor'] = price[0] / ctx['CompetitorPrice']
            
            demand = self.predict_demand(ctx)
            
            if objective == 'revenue':
                return -demand * price[0]
            elif objective == 'profit':
                return -(demand * price[0] - demand * cost_per_unit)
            else:
                raise ValueError("objective debe ser 'revenue' o 'profit'")
        
        result = minimize(
            objective_function,
            x0=[(price_bounds[0] + price_bounds[1]) / 2],
            method='SLSQP',
            bounds=[price_bounds]
        )
        
        optimal_price = result.x[0]
        
        # Calcular métricas con precio óptimo
        ctx_optimal = context.copy()
        ctx_optimal['Price'] = optimal_price
        if 'CompetitorPrice' in ctx_optimal:
            ctx_optimal['price_vs_competitor'] = optimal_price / ctx_optimal['CompetitorPrice']
        
        optimal_demand = self.predict_demand(ctx_optimal)
        optimal_revenue = optimal_demand * optimal_price
        optimal_profit = optimal_demand * (optimal_price - cost_per_unit)
        
        return {
            'optimal_price': optimal_price,
            'predicted_demand': optimal_demand,
            'expected_revenue': optimal_revenue,
            'expected_profit': optimal_profit,
            'unit_cost': cost_per_unit,
            'margin_pct': ((optimal_price - cost_per_unit) / optimal_price) * 100 if optimal_price > 0 else 0
        }
    
    def calculate_price_elasticity(self, context, price_range=None):
        """
        Calcula elasticidad precio-demanda
        """
        current_price = context.get('Price', 50)
        
        if price_range is None:
            price_range = (current_price * 0.7, current_price * 1.3)
        
        prices = np.linspace(price_range[0], price_range[1], 50)
        demands = []
        
        for price in prices:
            ctx = context.copy()
            ctx['Price'] = price
            if 'CompetitorPrice' in ctx:
                ctx['price_vs_competitor'] = price / ctx['CompetitorPrice']
            
            demand = self.predict_demand(ctx)
            demands.append(demand)
        
        # Elasticidad en punto medio
        mid_idx = len(prices) // 2
        if mid_idx > 0 and mid_idx < len(prices) - 1:
            price_change = (prices[mid_idx + 1] - prices[mid_idx - 1]) / prices[mid_idx]
            demand_change = (demands[mid_idx + 1] - demands[mid_idx - 1]) / max(demands[mid_idx], 0.01)
            
            elasticity = demand_change / price_change if price_change != 0 else 0
        else:
            elasticity = 0
        
        return elasticity, prices, demands
    
    def add_new_feature(self, df, feature_name, feature_data):
        """
        Permite agregar nuevas features dinámicamente
        
        Ejemplo:
        --------
        # Agregar marketing spend
        df = model.add_new_feature(df, 'marketing_spend', marketing_data)
        
        # Re-entrenar
        model.train_demand_model(df)
        """
        df[feature_name] = feature_data
        self.available_features.add(feature_name)
        
        print(f"✓ Feature '{feature_name}' agregada")
        print(f"  Total features: {len(self.available_features)}")
        
        return df


# ============================================================================
# EJEMPLO DE USO CON DATOS REALES
# ============================================================================

def ejemplo_con_datos_reales():
    """
    Ejemplo de cómo usar el modelo con tus datos
    """
    
    print("\n" + "="*70)
    print(" "*15 + "DYNAMIC PRICING - MODELO CON TUS DATOS")
    print("="*70 + "\n")
    
    # ========================================================================
    # 1. SIMULAR TUS DATOS (Reemplaza esto con pd.read_csv('tus_datos.csv'))
    # ========================================================================
    
    # Aquí simulo tus datos - TÚ REEMPLAZARÁS ESTO CON:
    # transactions_df = pd.read_csv('transacciones.csv')
    # inflation_df = pd.read_csv('inflacion.csv')
    # temperature_df = pd.read_csv('temperatura.csv')
    
    print("Generando datos de ejemplo (TÚ CARGARÁS TUS CSVs AQUÍ)...\n")
    
    # Simular transacciones
    np.random.seed(42)
    n_transactions = 1000
    
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='H')
    sample_dates = np.random.choice(dates, n_transactions)
    
    transactions_df = pd.DataFrame({
        'CustomerID': np.random.randint(1000, 9999, n_transactions),
        'ProductID': np.random.choice(['A', 'B', 'C', 'D'], n_transactions),
        'Quantity': np.random.randint(1, 10, n_transactions),
        'Price': np.random.uniform(20, 100, n_transactions),
        'TransactionDate': sample_dates,
        'PaymentMethod': np.random.choice(['Cash', 'Credit Card', 'Debit Card'], n_transactions),
        'StoreLocation': np.random.choice(['Store1', 'Store2', 'Store3'], n_transactions),
        'ProductCategory': np.random.choice(['Electronics', 'Books', 'Home Decor', 'Clothing'], n_transactions),
        'DiscountApplied(%)': np.random.choice([0, 5, 10, 15, 20], n_transactions, p=[0.5, 0.2, 0.15, 0.1, 0.05]),
        'TotalAmount': 0  # Se calculará
    })
    
    transactions_df['TotalAmount'] = (transactions_df['Price'] * transactions_df['Quantity'] * 
                                       (1 - transactions_df['DiscountApplied(%)'] / 100))
    
    # Simular inflación
    inflation_dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    inflation_df = pd.DataFrame({
        'Date': inflation_dates,
        'InflationRate': np.random.uniform(0.02, 0.08, len(inflation_dates))
    })
    
    # Simular temperatura
    temperature_df = pd.DataFrame({
        'Date': inflation_dates,
        'Temperature': 20 + 10 * np.sin(np.arange(len(inflation_dates)) * 2 * np.pi / 365) + np.random.normal(0, 3, len(inflation_dates))
    })
    
    # ========================================================================
    # 2. INICIALIZAR MODELO
    # ========================================================================
    
    model = DynamicPricingModelReal(cost_per_unit_default=30)
    
    # ========================================================================
    # 3. CARGAR Y PREPARAR DATOS
    # ========================================================================
    
    df_aggregated, df_detailed = model.load_and_prepare_data(
        transactions_df=transactions_df,
        inflation_df=inflation_df,
        temperature_df=temperature_df,
        competitor_prices_df=None  # Aún no tienes esto
    )
    
    # ========================================================================
    # 4. ENTRENAR MODELO
    # ========================================================================
    
    X_test, y_test, y_pred, feature_importance = model.train_demand_model(df_aggregated)
    
    # ========================================================================
    # 5. OPTIMIZAR PRECIOS
    # ========================================================================
    
    print("\n" + "="*70)
    print("OPTIMIZACIÓN DE PRECIOS")
    print("="*70 + "\n")
    
    # Contexto para optimización (ejemplo: Producto A, fin de semana, verano)
    context = {
        'Price': 50,  # Precio actual (se optimizará)
        'day_of_week': 6,  # Domingo
        'hour': 14,
        'is_weekend': 1,
        'month': 7,  # Julio
        'quarter': 3,
        'has_discount': 0,
        'discount_level': 0,
        'category_encoded': 0,  # Electronics
        'store_encoded': 0,
        'payment_cash': 0.3,
        'payment_card': 0.7,
        'InflationRate': 0.045,  # 4.5%
        'Temperature': 28  # 28°C
    }
    
    # Optimizar
    result = model.optimize_price(
        context,
        cost_per_unit=30,
        objective='profit',
        price_bounds=(30, 100)
    )
    
    print("Contexto:")
    print(f"  Día: Domingo (fin de semana)")
    print(f"  Hora: 14:00")
    print(f"  Mes: Julio (verano)")
    print(f"  Inflación: {context['InflationRate']:.1%}")
    print(f"  Temperatura: {context['Temperature']:.1f}°C")
    print()
    print("Resultados:")
    print(f"  Precio óptimo: ${result['optimal_price']:.2f}")
    print(f"  Demanda esperada: {result['predicted_demand']:.0f} unidades")
    print(f"  Revenue esperado: ${result['expected_revenue']:,.2f}")
    print(f"  Profit esperado: ${result['expected_profit']:,.2f}")
    print(f"  Margen: {result['margin_pct']:.1f}%")
    
    # ========================================================================
    # 6. ELASTICIDAD
    # ========================================================================
    
    print("\n" + "="*70)
    print("ELASTICIDAD PRECIO-DEMANDA")
    print("="*70)
    
    elasticity, prices, demands = model.calculate_price_elasticity(context)
    
    print(f"\nElasticidad: {elasticity:.3f}")
    
    if abs(elasticity) > 1:
        print("→ Demanda ELÁSTICA: Los clientes son sensibles al precio")
        print("  Estrategia: Competir en precio para aumentar volumen")
    else:
        print("→ Demanda INELÁSTICA: Los clientes son menos sensibles al precio")
        print("  Estrategia: Mantener márgenes altos, enfocarse en valor")
    
    print("\n" + "="*70 + "\n")
    
    return model, df_aggregated, result


if __name__ == "__main__":
    model, df, result = ejemplo_con_datos_reales()
