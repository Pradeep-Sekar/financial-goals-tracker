def recommend_investment(time_horizon, cagr):
    """Return investment recommendations based on time horizon and expected CAGR."""
    
    if time_horizon < 1:
        return "Fixed Deposits (FDs), Liquid Funds - Safe, low returns"
    
    elif 1 <= time_horizon <= 3:
        if cagr < 8:
            return "Debt Mutual Funds - Low risk, stable returns"
        else:
            return "Conservative Hybrid Funds - Mix of debt and equity"

    elif 3 < time_horizon <= 5:
        if cagr < 12:
            return "Balanced Mutual Funds - Moderate risk, good returns"
        else:
            return "Large-Cap Stocks or Index Funds - Growth potential with lower volatility"

    elif 5 < time_horizon <= 10:
        if cagr < 15:
            return "Equity Mutual Funds (Large & Mid-Cap) - Long-term wealth creation"
        else:
            return "Index Funds, High-Growth Stocks - Higher volatility, better returns"

    elif time_horizon > 10:
        return "Small-Cap Stocks, Thematic Funds - High risk, high reward for long-term investors"

    return "Custom Investment Plan Needed - Consult an expert!"