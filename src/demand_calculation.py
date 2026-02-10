def calculate_demand(df):
    """
    Calcula la demanda agregada por (agregada por día/producto/precio)
    La demanda es la suma de Quantity vendida a cada nivel de precio
    """
    df_aggregated = df.groupby(['Date', 'ProductID', 'Price', 'category_encoded']).agg({
        'Quantity': 'sum',
        'CustomerID': 'count',
        'TotalAmount': 'sum',
        'day_of_week': 'first',
        'hour': 'mean',
        'is_weekend': 'first',
        'month': 'first',
        'quarter': 'first',
        'has_discount': 'max',
        'discount_level': 'max',
        'DiscountApplied': 'mean',
        'store_encoded': 'first',
        'payment_encoded': 'first',
        'InflationMonth': 'first',
        'InflationYear': 'first'
    }).reset_index()
    
    # Renombrar para claridad
    df_aggregated.rename(columns={'Quantity': 'demand'}, inplace=True)
    
    return df_aggregated