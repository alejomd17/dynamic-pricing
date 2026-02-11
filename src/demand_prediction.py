import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

import warnings
warnings.filterwarnings('ignore')

class DemandPredictor:
    def __init__(self, df):
        self.demand_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.df = df.copy()

    def prepare_features(self):
        """
        Prepara features para el modelo
        """
        feature_cols = [
            'Price',
            'day_of_week', 'hour', 'is_weekend', 'month', 'quarter',
            'has_discount', 'discount_level', 'DiscountApplied',
            'category_encoded', 'store_encoded', 'payment_encoded',
            'InflationMonth', 'InflationYear',
            'customer_purchase_count', 'customer_avg_ticket', 'is_new_customer',
            'days_since_last_purchase', 
            'ticket_deviation', 'price_vs_category'
        ]
        
        # Filtrar solo las que existen
        feature_cols = [f for f in feature_cols if f in self.df.columns]
        
        return self.df[feature_cols]
    
    def train_demand_model(self):
        """
        Entrena el modelo de predicción de demanda
        """
        X = self.prepare_features()
        y = self.df['demand']
        
        self.feature_names = X.columns.tolist()
        
        print("="*80)
        print("ENTRENAMIENTO DEL MODELO DE DEMANDA")
        print("="*80)
        print(f"\nFeatures utilizadas ({len(self.feature_names)}):")
        for i, feat in enumerate(self.feature_names, 1):
            print(f"  {i:2d}. {feat}")
        print()
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        
        print(f"Training set: {len(X_train):,} observaciones")
        print(f"Test set: {len(X_test):,} observaciones\n")
        
        # Escalar
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entrenar
        self.demand_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            verbose=0
        )
        
        print("Entrenando modelo...")
        self.demand_model.fit(X_train_scaled, y_train)
        print("✓ Modelo entrenado\n")
        
        # Evaluar
        y_pred_train = self.demand_model.predict(X_train_scaled)
        y_pred_test = self.demand_model.predict(X_test_scaled)
        
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        print("MÉTRICAS DE EVALUACIÓN:")
        print("-" * 80)
        print(f"R² Train:  {r2_train:.4f}")
        print(f"R² Test:   {r2_test:.4f}")
        print(f"RMSE Train: {rmse_train:.2f} unidades")
        print(f"RMSE Test:  {rmse_test:.2f} unidades")
        
        if r2_test < 0.3:
            print("\n⚠️  R² bajo - Considera:")
            print("   1. Más datos históricos")
            print("   2. Verificar calidad de datos")
            print("   3. Agregar más features relevantes")
        elif r2_test < 0.6:
            print("\n✓ R² aceptable - El modelo captura algunas tendencias")
        else:
            print("\n✓✓ R² bueno - El modelo predice bien la demanda")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.demand_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nIMPORTANCIA DE FEATURES:")
        print("-" * 80)
        for _, row in feature_importance.head(10).iterrows():
            bar_length = int(row['importance'] * 50)
            bar = '█' * bar_length
            print(f"{row['feature']:30s} {bar} {row['importance']:.4f}")
        
        print("="*80 + "\n")
        
        return X_test, y_test, y_pred_test, feature_importance
    
    def predict_demand(self, features_dict):
        """
        Predice demanda dado un contexto
        """
        feature_values = {}
        for feat in self.feature_names:
            feature_values[feat] = features_dict.get(feat, 0)
        
        df = pd.DataFrame([feature_values])
        X_scaled = self.scaler.transform(df)
        
        return max(0, self.demand_model.predict(X_scaled)[0])
    