"""
accuracy.py — Forecast accuracy metrics for phonecast.

Computes MAD, MSE, RMSE, and MAPE for each brand's historical
fitted values vs. actual sales.
"""

import numpy as np


def compute_mad(actual, forecast):
    """
    Mean Absolute Deviation: MAD = Σ|At − Ft| / n
    
    Parameters:
        actual (array-like): Actual sales values (Yt/At).
        forecast (array-like): Fitted/forecasted values (Ft).
    
    Returns:
        float: MAD rounded to 4 decimal places.
    """
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)
    return round(np.mean(np.abs(actual - forecast)), 4)


def compute_mse(actual, forecast):
    """
    Mean Squared Error: MSE = Σ(At − Ft)² / n
    
    Parameters:
        actual (array-like): Actual sales values.
        forecast (array-like): Fitted/forecasted values.
    
    Returns:
        float: MSE rounded to 4 decimal places.
    """
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)
    return round(np.mean((actual - forecast) ** 2), 4)


def compute_rmse(actual, forecast):
    """
    Root Mean Squared Error: RMSE = √MSE
    
    Parameters:
        actual (array-like): Actual sales values.
        forecast (array-like): Fitted/forecasted values.
    
    Returns:
        float: RMSE rounded to 4 decimal places.
    """
    mse = compute_mse(actual, forecast)
    return round(np.sqrt(mse), 4)


def compute_mape(actual, forecast):
    """
    Mean Absolute Percentage Error: MAPE = (100 / n) × Σ|At − Ft| / At
    
    Parameters:
        actual (array-like): Actual sales values (must be > 0).
        forecast (array-like): Fitted/forecasted values.
    
    Returns:
        float: MAPE as a percentage, rounded to 4 decimal places.
    """
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)
    
    # Filter out zero actuals to avoid division by zero
    mask = actual != 0
    actual = actual[mask]
    forecast = forecast[mask]
    
    if len(actual) == 0:
        return 0.0
    
    return round((100.0 / len(actual)) * np.sum(np.abs(actual - forecast) / actual), 4)


def accuracy_summary(historical_data):
    """
    Compute all accuracy metrics for each brand.
    
    Parameters:
        historical_data (dict): Mapping of brand name -> DataFrame with 'Yt' and 'Ft' columns.
    
    Returns:
        dict: Mapping of brand name -> {'MAD': float, 'MSE': float, 'RMSE': float, 'MAPE': float}
    """
    results = {}
    
    for brand, df in historical_data.items():
        actual = df['Yt'].values
        forecast = df['Ft'].values
        
        results[brand] = {
            'MAD': compute_mad(actual, forecast),
            'MSE': compute_mse(actual, forecast),
            'RMSE': compute_rmse(actual, forecast),
            'MAPE': compute_mape(actual, forecast)
        }
    
    return results


def get_mape_category(mape_value):
    """
    Classify MAPE value into a color category.
    
    Parameters:
        mape_value (float): MAPE percentage.
    
    Returns:
        str: 'green' (<10%), 'yellow' (10-20%), or 'red' (>20%).
    """
    if mape_value < 10:
        return 'green'
    elif mape_value <= 20:
        return 'yellow'
    else:
        return 'red'


def get_best_worst_brands(accuracy_data):
    """
    Determine the brands with the best and worst forecast accuracy (by MAPE).
    
    Parameters:
        accuracy_data (dict): Output from accuracy_summary().
    
    Returns:
        tuple: (best_brand, worst_brand) names.
    """
    if not accuracy_data:
        return None, None
    
    sorted_brands = sorted(accuracy_data.items(), key=lambda x: x[1]['MAPE'])
    best = sorted_brands[0][0]
    worst = sorted_brands[-1][0]
    
    return best, worst
