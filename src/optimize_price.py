import numpy as np
from scipy.optimize import minimize
def optimize_price(self, context, cost_per_unit=None, objective='revenue', 
                    price_bounds=None, constraints=None):
    """
    Optimiza precio
    
    Parameters:
    -----------
    objective: 'revenue', 'profit', o 'demand'
    """
    current_price = context.get('Price', 50)
    
    if price_bounds is None:
        price_bounds = (current_price * 0.5, current_price * 1.5)
    
    if cost_per_unit is None:
        cost_per_unit = context.get('estimated_cost', current_price * 0.6)
    
    def objective_function(price):
        ctx = context.copy()
        ctx['Price'] = price[0]
        ctx['price_vs_category'] = price[0] / context.get('category_avg_price', price[0])
        
        demand = self.predict_demand(ctx)
        
        if objective == 'revenue':
            return -demand * price[0]
        elif objective == 'profit':
            return -(demand * (price[0] - cost_per_unit))
        elif objective == 'demand':
            return -demand
        else:
            raise ValueError("objective debe ser 'revenue', 'profit', o 'demand'")
    
    cons = []
    if constraints and 'min_demand' in constraints:
        def demand_constraint(price):
            ctx = context.copy()
            ctx['Price'] = price[0]
            ctx['price_vs_category'] = price[0] / context.get('category_avg_price', price[0])
            demand = self.predict_demand(ctx)
            return demand - constraints['min_demand']
        
        cons.append({'type': 'ineq', 'fun': demand_constraint})
    
    result = minimize(
        objective_function,
        x0=[(price_bounds[0] + price_bounds[1]) / 2],
        method='SLSQP',
        bounds=[price_bounds],
        constraints=cons if cons else None
    )
    
    optimal_price = result.x[0]
    
    ctx_optimal = context.copy()
    ctx_optimal['Price'] = optimal_price
    ctx_optimal['price_vs_category'] = optimal_price / context.get('category_avg_price', optimal_price)
    
    optimal_demand = self.predict_demand(ctx_optimal)
    optimal_revenue = optimal_demand * optimal_price
    optimal_profit = optimal_demand * (optimal_price - cost_per_unit)
    
    return {
        'optimal_price': optimal_price,
        'predicted_demand': optimal_demand,
        'expected_revenue': optimal_revenue,
        'expected_profit': optimal_profit,
        'cost_per_unit': cost_per_unit,
        'margin_pct': ((optimal_price - cost_per_unit) / optimal_price) * 100 if optimal_price > 0 else 0,
        'price_change_pct': ((optimal_price - current_price) / current_price) * 100
    }

