import pandas as pd
from demand_prediction import DemandPredictor

def generate_product_recommendations(self, df):
    """
    Genera recomendaciones de precio por producto
    """
    print("\n" + "="*80)
    print("RECOMENDACIONES DE PRECIO POR PRODUCTO")
    print("="*80 + "\n")
    
    productos = df['ProductID'].unique()
    recommendations = []
    
    for producto in productos[:10]:  # Top 10 productos
        df_prod = df[df['ProductID'] == producto]
        
        if len(df_prod) < 5:
            continue
        
        # Contexto promedio del producto
        context = {
            'Price': df_prod['Price'].mean(),
            'day_of_week': 3,
            'hour': 14,
            'is_weekend': 0,
            'month': 6,
            'quarter': 2,
            'has_discount': 0,
            'discount_level': 0,
            'DiscountApplied': 0,
            'category_encoded': df_prod['category_encoded'].mode()[0] if len(df_prod['category_encoded'].mode()) > 0 else 0,
            'store_encoded': df_prod['store_encoded'].mode()[0] if len(df_prod['store_encoded'].mode()) > 0 else 0,
            'payment_encoded': df_prod['payment_encoded'].mode()[0] if len(df_prod['payment_encoded'].mode()) > 0 else 0,
            'InflationMonth': df_prod['InflationMonth'].mean(),
            'InflationYear': df_prod['InflationYear'].mean(),
            'customer_purchase_count': df_prod['customer_purchase_count'].mean(),
            'customer_avg_ticket': df_prod['customer_avg_ticket'].mean(),
            'is_new_customer': 0,
            'days_since_last_purchase': df_prod['days_since_last_purchase'].mean(),
            'ticket_deviation': 0,
            'price_vs_category': 1,
            'estimated_cost': df_prod['estimated_cost'].mean(),
            'category_avg_price': df_prod['category_avg_price'].mean(),
            'current_demand': df_prod['demand'].mean()
        }
        
        # Optimizar para revenue y profit
        try:
            revenue_opt = self.optimize_price(context, objective='revenue')
            profit_opt = self.optimize_price(
                context, 
                cost_per_unit=context['estimated_cost'],
                objective='profit'
            )
            
            elasticity, _, _ = self.calculate_price_elasticity(context)
            
            recommendations.append({
                'ProductID': producto,
                'precio_actual': context['Price'],
                'demanda_actual': context['current_demand'],
                'precio_max_revenue': revenue_opt['optimal_price'],
                'precio_max_profit': profit_opt['optimal_price'],
                'revenue_actual': context['Price'] * context['current_demand'],
                'revenue_optimizado': revenue_opt['expected_revenue'],
                'profit_actual': (context['Price'] - context['estimated_cost']) * context['current_demand'],
                'profit_optimizado': profit_opt['expected_profit'],
                'elasticidad': elasticity,
                'recomendacion': 'Subir precio' if profit_opt['optimal_price'] > context['Price'] else 'Bajar precio'
            })
            
            print(f"\n{producto}:")
            print(f"  Precio actual: ${context['Price']:.2f}")
            print(f"  Recomendado (revenue): ${revenue_opt['optimal_price']:.2f} ({revenue_opt['price_change_pct']:+.1f}%)")
            print(f"  Recomendado (profit):  ${profit_opt['optimal_price']:.2f} ({profit_opt['price_change_pct']:+.1f}%)")
            print(f"  Elasticidad: {elasticity:.3f}")
            print(f"  → {recommendations[-1]['recomendacion']}")
            
        except Exception as e:
            print(f"\n{producto}: Error - {str(e)}")
            continue
    
    df_recommendations = pd.DataFrame(recommendations)
    
    print("\n" + "="*80)
    print(f"✓ Recomendaciones generadas para {len(recommendations)} productos")
    print("="*80 + "\n")
    
    return df_recommendations

