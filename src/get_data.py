"""
Dynamic Pricing Model
===================================================
Modelo de Dynamic Pricing utilizando datos reales de transacciones minoristas.
Se incluyen features adicionales como inflación, temperatura y precios de competencia
cuando estén disponibles.
"""

import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings('ignore')


class GetData:
    """
    Modelo de Dynamic Pricing 
    """
    
    def __init__(self, cost_per_unit_default=None):
        self.demand_model = None
        # self.scaler = StandardScaler()
        self.cost_per_unit_default = cost_per_unit_default
        self.feature_names = None
        self.product_costs = {}  # Costos por producto
        self.available_features = set()  # Features disponibles
        self.df = pd.DataFrame()  # Datos agrupados de todas las fuentes
        self.df_transacciones = pd.DataFrame()  # Datos detallados de transacciones
        self.df_inflation = pd.DataFrame()  # Datos detallados de transacciones
        self.df_temperature = pd.DataFrame()  # Datos detallados de transacciones
        self.df_competidors = pd.DataFrame()  # Datos detallados de transacciones
        
    def sellin_input(self):
        """
        Parameters:
        -----------
        transactions_df: DataFrame with columns:
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
        """
        transactions_df = pd.read_csv('../data/Retail_Transaction_Dataset.csv')
        transactions_df = transactions_df.rename(columns={'DiscountApplied(%)': 'DiscountApplied'}      )
        print(f"=== Sellin input ===")
        df = transactions_df.copy()

        # Convertir fecha
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
        df['Date'] = df['TransactionDate'].dt.date
        
        # Extraer features temporales
        df['year'] = df['TransactionDate'].dt.year
        df['month'] = df['TransactionDate'].dt.month
        df['year_month'] = df['year'].astype(str) + df['month'].astype(str).str.zfill(2)
        df['day_of_week'] = df['TransactionDate'].dt.dayofweek
        df['day_of_month'] = df['TransactionDate'].dt.day
        df['hour'] = df['TransactionDate'].dt.hour
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['quarter'] = df['TransactionDate'].dt.quarter

        # Location
        df['Direction'] = df['StoreLocation'].str.split('\n', expand=True)[0]
        df['City'] = df['StoreLocation'].str.split('\n', expand=True)[1].str.split(', ', expand=True)[0]
        df['State'] = df['StoreLocation'].str.split('\n', expand=True)[1].str.split(', ', expand=True)[1].str.split(' ', expand=True)[0]
        df['ZipCode'] = df['StoreLocation'].str.split('\n', expand=True)[1].str.split(', ', expand=True)[1].str.split(' ', expand=True)[1]
        
        # Categorizar método de pago
        df['payment_encoded'] = pd.Categorical(df['PaymentMethod']).codes

        # Encodear categorías de producto
        df['category_encoded'] = pd.Categorical(df['ProductCategory']).codes
        
        # Features de descuento
        df['has_discount'] = (df['DiscountApplied'] > 0).astype(int)
        df['discount_level'] = pd.cut(
                                        df['DiscountApplied'], 
                                        bins=[-0.1, 0, 10, 20, 100],
                                        labels=[0, 1, 2, 3]
                                    ).astype(int)
        
        # Encodear ubicación de tienda
        df['store_encoded'] = pd.Categorical(df['StoreLocation']).codes
        
        # Features derivadas
        df['discount_amount'] = df['TotalAmount'] * (df['DiscountApplied'] / 100)
        
        # Costos estimados como % del Price
        df['estimated_cost'] = df.apply(
                                        lambda row: row['Price'] * 0.6,
                                        axis=1
                                    )
        # # Costos estimados como ajuste histórico por producto
        # discount_factor = df.groupby('ProductID')['DiscountApplied'].mean() / 200
        # df['discount_factor'] = df['ProductID'].map(discount_factor)
        # df['estimated_cost'] = df['estimated_cost'] * (1 + df['discount_factor'].fillna(0))
        
        # Columna para costos reales
        # df['actual_cost'] = df['estimated_cost'].copy()
        
        df['estimated_margin_pct'] = ((df['Price'] - df['estimated_cost']) / df['Price']) * 100

        # Eliminar las columnas originales que ya no se necesitan
        df = df.drop(columns=['StoreLocation', 'TransactionDate'])

        
        # Frecuencia de compra del cliente
        df['customer_purchase_count'] = df.groupby('CustomerID').cumcount() + 1
        
        # Ticket promedio del cliente (histórico)
        customer_avg = df.groupby('CustomerID')['TotalAmount'].expanding().mean().reset_index(level=0, drop=True)
        df['customer_avg_ticket'] = customer_avg
        
        # Cliente nuevo
        df['is_new_customer'] = (df['customer_purchase_count'] == 1).astype(int)
        
        # Días desde última compra (solo para clientes recurrentes)
        df = df.sort_values(['CustomerID', 'Date'])
        df['days_since_last_purchase'] = df.groupby('CustomerID')['Date'].diff().dt.days
        df['days_since_last_purchase'] = df['days_since_last_purchase'].fillna(0)
        
        # Lifetime value del cliente hasta la fecha
        df['customer_ltv'] = df.groupby('CustomerID')['TotalAmount'].cumsum()
        
          # Ticket promedio por producto
        df['product_avg_ticket'] = df.groupby('ProductID')['TotalAmount'].transform('mean')
        
        # Desviación del ticket normal del producto
        df['ticket_deviation'] = (df['TotalAmount'] - df['product_avg_ticket']) / (df['product_avg_ticket'] + 1)
        
        # Precio vs promedio de categoría
        df['category_avg_price'] = df.groupby('category_encoded')['Price'].transform('mean')
        df['price_vs_category'] = df['Price'] / (df['category_avg_price'] + 1)
        
        # Revenue y profit calculados
        df['revenue'] = df['Price'] * df['demand']
        df['estimated_profit'] = (df['Price'] - df['estimated_cost']) * df['demand']
        
        df.rename(columns={'Quantity': 'demand'}, inplace=True)

        # Registrar features básicas disponibles
        self.available_features = {
            'Price', 'day_of_week', 'hour', 'is_weekend', 'month', 
            'quarter', 'has_discount', 'discount_level', 'DiscountApplied', 'category_encoded',
            'store_encoded', 'payment_encoded', 'customer_purchase_count',
            'customer_avg_ticket', 'is_new_customer', 'days_since_last_purchase',
            'customer_ltv', 'product_avg_ticket', 'ticket_deviation', 'price_vs_category',
        }
        
        print(f"Transacciones cargadas: {len(df):,}")
        print(f"Periodo: {df['Date'].min()} a {df['Date'].max()}")
        
        self.df_transacciones = df.copy() 
        self.df = df.copy()

        return self.df_transacciones
    
    def inflation_input(self):
        """ 
        inflation_df: DataFrame con columnas [Date, InflationRate] (opcional)
        """
        try:
            inflation_df = pd.read_csv('../data/CPIAUCSL.csv')
            print(f"=== Inflation input ===")
            inflation_df['Date'] = pd.to_datetime(inflation_df['observation_date'])
            inflation_df['year_month'] = inflation_df['Date'].dt.year.astype(str) + inflation_df['Date'].dt.month.astype(str).str.zfill(2) 
            inflation_df['InflationAcum'] = inflation_df['CPIAUCSL'].ffill()
            inflation_df['InflationAcum'] = np.where(inflation_df['CPIAUCSL'].isna(), inflation_df['InflationAcum']+0.0001, inflation_df['InflationAcum'])
            inflation_df['InflationMonth'] = inflation_df['InflationAcum'] / inflation_df['InflationAcum'].shift(1) - 1
            inflation_df['InflationYear'] = inflation_df['InflationAcum'] / inflation_df['InflationAcum'].shift(12) - 1
            self.df_inflation = inflation_df.copy()
            
            if len(self.df) > 0:
                self.df = self.df.merge(
                    inflation_df[['year_month', 'InflationMonth', 'InflationYear']], 
                    on='year_month', 
                    how='left'
                )
                self.available_features.add('inflation_month')
                self.available_features.add('inflation_year')
                print(f"Inflación agregada")
            else:
                print("No se ha cargado el DataFrame principal aún.")
                        
        except FileNotFoundError:
            print("Inflación NO disponible")

        return self.df_inflation
        
    def temperature_input(self):
        """ 
        temperature_df: DataFrame con columnas [Date, Temperature] (opcional)
        """
        try:
            temperature_df = pd.read_csv('../data/temperature.csv')
            self.df_temperature = temperature_df.copy()

            if len(self.df) > 0:
                self.df = self.df.merge(
                    temperature_df[['Date', 'Temperature']], 
                    on='Date', 
                    how='left'
                )
                self.available_features.add('temperature')
                print(f"Temperatura agregada")
            else:
                print("No se ha cargado el DataFrame principal aún.")

            
        except FileNotFoundError:
            print("Temperatura NO disponible")

        return self.df_temperature
    
    def competitors_input(self):
        """ 
        competitor_prices_df: DataFrame con [Date, ProductID, CompetitorPrice] (opcional)
        """
        try:
            competitor_prices_df = pd.read_csv('../data/competitor_prices.csv')
            self.df_competidors = competitor_prices_df.copy()
            
            self.df = self.df.merge(
                competitor_prices_df[['Date', 'ProductID', 'CompetitorPrice']], 
                on=['Date', 'ProductID'], 
                how='left'
            )
            self.available_features.add('competitor_price')
            
            print(f"Precios de competencia agregados")
        except FileNotFoundError:
            print("Precios de competencia NO disponibles")
        
        return self.df_competidors
    
    def get_data(self):
        """
        Función principal para obtener datos procesados listos para modelar.
        """
        self.sellin_input()
        self.inflation_input()
        self.temperature_input()
        self.competitors_input()

        return self.df, self.available_features
