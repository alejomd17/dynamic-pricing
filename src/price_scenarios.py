import pandas as pd
from demand_prediction import DemandPredictor

def analyze_price_scenarios(self, context, cost_per_unit=None, price_changes=None):
    """
    Analiza diferentes escenarios de precio
    
    Returns DataFrame con: price, demand, revenue, profit, elasticity
    """
    if price_changes is None:
        price_changes = [-20, -10, -5, 0, 5, 10, 20]  # % cambios
    
    current_price = context.get('Price', 50)
    
    if cost_per_unit is None:
        # Usar costo estimado del contexto
        cost_per_unit = context.get('estimated_cost', current_price * 0.6)
    
    scenarios = []
    
    for pct_change in price_changes:
        new_price = current_price * (1 + pct_change / 100)
        
        ctx = context.copy()
        ctx['Price'] = new_price
        ctx['price_vs_category'] = new_price / context.get('category_avg_price', new_price)
        
        demand = self.predict_demand(ctx)
        revenue = new_price * demand
        profit = (new_price - cost_per_unit) * demand
        margin = ((new_price - cost_per_unit) / new_price) * 100 if new_price > 0 else 0
        
        scenarios.append({
            'price_change_pct': pct_change,
            'price': new_price,
            'demand': demand,
            'revenue': revenue,
            'profit': profit,
            'margin_pct': margin,
            'units_sold_change': demand - context.get('current_demand', demand)
        })
    
    df_scenarios = pd.DataFrame(scenarios)
    
    # Marcar el mejor
    df_scenarios['best_revenue'] = df_scenarios['revenue'] == df_scenarios['revenue'].max()
    df_scenarios['best_profit'] = df_scenarios['profit'] == df_scenarios['profit'].max()
    
    return df_scenarios
