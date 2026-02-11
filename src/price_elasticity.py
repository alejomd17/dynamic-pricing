import numpy as np    
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
        # Actualizar features dependientes del precio
        ctx['price_vs_category'] = price / context.get('category_avg_price', price)
        
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

