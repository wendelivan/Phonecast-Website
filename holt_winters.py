"""
holt_winters.py — Multiplicative Holt-Winters computation engine for phonecast.

Reads pre-computed Holt-Winters columns from the uploaded CSV,
computes fitted values, and generates future quarter forecasts.
"""

import pandas as pd
import numpy as np


def detect_brands(df):
    """
    Extract and return a sorted list of unique brand names from the Brand column.
    
    Parameters:
        df (pd.DataFrame): The uploaded CSV data.
    
    Returns:
        list: Sorted list of unique brand name strings.
    """
    return sorted(df['Brand'].unique().tolist())


def compute_fitted_values(df, brand):
    """
    Compute the one-step-ahead fitted forecast values (Ft) for a given brand.
    Ft = (Lt_1 + bt_1) * St_s
    
    Parameters:
        df (pd.DataFrame): Full dataset.
        brand (str): Brand name to filter.
    
    Returns:
        pd.DataFrame: Brand-filtered DataFrame with an added 'Ft' column.
    """
    brand_df = df[df['Brand'] == brand].copy()
    brand_df = brand_df.sort_values(['Year', 'Quarter']).reset_index(drop=True)
    
    # Compute fitted values: Ft = (Lt_1 + bt_1) * St_s
    brand_df['Ft'] = (brand_df['Lt_1'] + brand_df['bt_1']) * brand_df['St_s']
    
    # Compute error
    brand_df['Error'] = brand_df['Yt'] - brand_df['Ft']
    brand_df['Abs_Error'] = brand_df['Error'].abs()
    brand_df['Pct_Error'] = (brand_df['Abs_Error'] / brand_df['Yt']) * 100
    
    # Create period label
    brand_df['Period'] = brand_df.apply(
        lambda row: f"Q{int(row['Quarter'])} {int(row['Year'])}", axis=1
    )
    
    return brand_df


def generate_forecast(brand_df, num_quarters=4):
    """
    Generate future quarter forecasts using the Multiplicative Holt-Winters formula:
    Ft+m = (Lt + m * bt) * St+m-s
    
    Uses the last row's Lt, bt values and the seasonal indices from the data.
    
    Parameters:
        brand_df (pd.DataFrame): Processed brand DataFrame (with Ft computed).
        num_quarters (int): Number of future quarters to forecast (1-12).
    
    Returns:
        pd.DataFrame: DataFrame with forecasted quarters and values.
    """
    if brand_df.empty:
        return pd.DataFrame()
    
    # Get the last row values
    last_row = brand_df.iloc[-1]
    Lt = last_row['Lt']
    bt = last_row['bt']
    
    # Get seasonal indices (last full cycle, i.e., last 4 St values)
    s = 4  # quarterly seasonal period
    seasonal_indices = brand_df['St'].tail(s).values
    
    # Determine starting year and quarter for forecasts
    last_year = int(last_row['Year'])
    last_quarter = int(last_row['Quarter'])
    
    forecasts = []
    for m in range(1, num_quarters + 1):
        # Calculate the forecast
        # St+m-s: use the seasonal index from s periods before the forecast period
        seasonal_idx = (m - 1) % s
        St_m = seasonal_indices[seasonal_idx]
        
        Ft_m = (Lt + m * bt) * St_m
        
        # Calculate the future quarter and year
        future_quarter = ((last_quarter - 1 + m) % 4) + 1
        future_year = last_year + ((last_quarter - 1 + m) // 4)
        
        forecasts.append({
            'Brand': last_row['Brand'],
            'Year': future_year,
            'Quarter': future_quarter,
            'Period': f"Q{future_quarter} {future_year}",
            'm': m,
            'Ft_m': round(Ft_m, 4),
            'Lt_base': Lt,
            'bt_base': bt,
            'St_used': St_m
        })
    
    return pd.DataFrame(forecasts)


def process_all_brands(df, forecast_quarters=4):
    """
    Process all brands in the dataset: compute fitted values and generate forecasts.
    
    Parameters:
        df (pd.DataFrame): Full uploaded CSV data.
        forecast_quarters (int): Number of future quarters to forecast per brand.
    
    Returns:
        dict: {
            'brands': list of brand names,
            'historical': dict of brand -> processed DataFrame,
            'forecasts': dict of brand -> forecast DataFrame,
            'summary': dict of brand -> summary info
        }
    """
    brands = detect_brands(df)
    historical = {}
    forecasts = {}
    summary = {}
    
    for brand in brands:
        # Compute fitted values
        brand_df = compute_fitted_values(df, brand)
        historical[brand] = brand_df
        
        # Generate forecasts
        forecast_df = generate_forecast(brand_df, forecast_quarters)
        forecasts[brand] = forecast_df
        
        # Build summary info
        latest_row = brand_df.iloc[-1]
        next_forecast = forecast_df.iloc[0]['Ft_m'] if not forecast_df.empty else None
        
        summary[brand] = {
            'latest_yt': round(latest_row['Yt'], 2),
            'latest_period': latest_row['Period'],
            'next_forecast': round(next_forecast, 2) if next_forecast else 'N/A',
            'next_period': forecast_df.iloc[0]['Period'] if not forecast_df.empty else 'N/A',
            'total_records': len(brand_df),
            'date_range': f"{brand_df.iloc[0]['Period']} – {brand_df.iloc[-1]['Period']}"
        }
    
    first_row = df.iloc[0]
    last_row = df.iloc[-1]
    date_range = f"Q{int(first_row['Quarter'])} {int(first_row['Year'])} – Q{int(last_row['Quarter'])} {int(last_row['Year'])}"
    
    return {
        'brands': brands,
        'historical': historical,
        'forecasts': forecasts,
        'summary': summary,
        'total_brands': len(brands),
        'total_records': len(df),
        'date_range': date_range
    }
