import numpy as np
import matplotlib.pyplot as plt

def plot_elasticity_analysis(self, context, cost_per_unit=None, save_path=None):
    """
    Visualiza análisis de elasticidad y escenarios
    """
    elasticity, prices, demands = self.calculate_price_elasticity(context)
    
    if cost_per_unit is None:
        cost_per_unit = context.get('estimated_cost', context.get('Price', 50) * 0.6)
    
    revenues = [p * d for p, d in zip(prices, demands)]
    profits = [(p - cost_per_unit) * d for p, d in zip(prices, demands)]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Demanda vs Precio
    axes[0, 0].plot(prices, demands, 'b-', linewidth=2)
    axes[0, 0].axvline(context.get('Price', 50), color='red', linestyle='--', alpha=0.5, label='Precio actual')
    axes[0, 0].set_xlabel('Precio ($)', fontsize=12)
    axes[0, 0].set_ylabel('Demanda (unidades)', fontsize=12)
    axes[0, 0].set_title(f'Curva de Demanda\nElasticidad: {elasticity:.3f}', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Revenue vs Precio
    axes[0, 1].plot(prices, revenues, 'g-', linewidth=2)
    max_rev_idx = np.argmax(revenues)
    axes[0, 1].scatter(prices[max_rev_idx], revenues[max_rev_idx], 
                        color='red', s=100, zorder=5, label=f'Máx: ${prices[max_rev_idx]:.2f}')
    axes[0, 1].axvline(context.get('Price', 50), color='red', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel('Precio ($)', fontsize=12)
    axes[0, 1].set_ylabel('Revenue ($)', fontsize=12)
    axes[0, 1].set_title('Revenue vs Precio', fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Profit vs Precio
    axes[1, 0].plot(prices, profits, 'purple', linewidth=2)
    max_prof_idx = np.argmax(profits)
    axes[1, 0].scatter(prices[max_prof_idx], profits[max_prof_idx], 
                        color='red', s=100, zorder=5, label=f'Máx: ${prices[max_prof_idx]:.2f}')
    axes[1, 0].axvline(context.get('Price', 50), color='red', linestyle='--', alpha=0.5)
    axes[1, 0].set_xlabel('Precio ($)', fontsize=12)
    axes[1, 0].set_ylabel('Profit ($)', fontsize=12)
    axes[1, 0].set_title(f'Profit vs Precio\n(Costo: ${cost_per_unit:.2f})', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Análisis de escenarios
    scenarios = self.analyze_price_scenarios(context, cost_per_unit)
    
    x_pos = np.arange(len(scenarios))
    width = 0.35
    
    axes[1, 1].bar(x_pos - width/2, scenarios['revenue'], width, label='Revenue', alpha=0.8)
    axes[1, 1].bar(x_pos + width/2, scenarios['profit'], width, label='Profit', alpha=0.8)
    axes[1, 1].set_xlabel('Cambio de Precio (%)', fontsize=12)
    axes[1, 1].set_ylabel('Monto ($)', fontsize=12)
    axes[1, 1].set_title('Escenarios de Precio', fontsize=14, fontweight='bold')
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels([f"{int(x)}%" for x in scenarios['price_change_pct']])
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n✓ Gráfico guardado: {save_path}")
    
    return fig

