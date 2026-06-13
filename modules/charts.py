"""
charts.py — Plotly chart builders for phonecast.

All charts use the phonecast blue color palette and return
Plotly JSON for client-side rendering.
"""

import plotly
import plotly.graph_objects as go
import plotly.express as px
import json


# phonecast color palette
COLORS = {
    'primary': '#0D2B6E',
    'accent': '#2B7FCC',
    'mid': '#1A56A0',
    'light': '#D0E4F5',
    'background': '#F4F7FB',
    'white': '#FFFFFF',
    'text': '#444444',
    'green': '#28A745',
    'yellow': '#FFC107',
    'red': '#DC3545',
}

# Extended brand color palette for multi-brand charts
BRAND_COLORS = [
    '#0D2B6E', '#2B7FCC', '#1A56A0', '#4A90D9', '#6FB3E0',
    '#0E4D92', '#1E88E5', '#42A5F5', '#7CB9E8', '#00497B',
    '#003D6B', '#2196F3', '#64B5F6', '#0277BD', '#01579B',
]


def _get_brand_color(index):
    """Get a color from the palette by index, cycling if needed."""
    return BRAND_COLORS[index % len(BRAND_COLORS)]


def _base_layout(title='', height=450):
    """Create a base Plotly layout matching the phonecast theme."""
    return go.Layout(
        title=dict(
            text=title,
            font=dict(family='Arial, sans-serif', size=18, color=COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        font=dict(family='Arial, sans-serif', size=13, color=COLORS['text']),
        plot_bgcolor=COLORS['white'],
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.25,
            xanchor='center',
            x=0.5,
            font=dict(size=11)
        ),
        xaxis=dict(
            gridcolor='#E8EDF3',
            linecolor='#CCC',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            gridcolor='#E8EDF3',
            linecolor='#CCC',
            tickfont=dict(size=11),
            title_font=dict(size=13)
        ),
        hoverlabel=dict(
            bgcolor=COLORS['primary'],
            font_size=12,
            font_family='Arial'
        )
    )


def to_json(fig):
    """Convert a Plotly figure to JSON for client-side rendering."""
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def all_brands_historical_chart(historical_data):
    """
    Multi-line chart of Yt (actual sales) per brand over quarters.
    
    Parameters:
        historical_data (dict): brand -> DataFrame with 'Period' and 'Yt' columns.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    for i, (brand, df) in enumerate(historical_data.items()):
        fig.add_trace(go.Scatter(
            x=df['Period'],
            y=df['Yt'],
            mode='lines+markers',
            name=brand,
            line=dict(color=_get_brand_color(i), width=2.5),
            marker=dict(size=6),
            hovertemplate=f'<b>{brand}</b><br>%{{x}}<br>Sales: %{{y:,.0f}}<extra></extra>'
        ))
    
    layout = _base_layout('Historical Sales by Brand')
    layout.yaxis.title = 'Sales (Yt)'
    layout.xaxis.title = 'Quarter'
    fig.update_layout(layout)
    
    return to_json(fig)


def forecast_overview_bar_chart(forecast_data, num_quarters=4):
    """
    Grouped bar chart of forecasted quarters by brand.
    
    Parameters:
        forecast_data (dict): brand -> forecast DataFrame with 'Period' and 'Ft_m' columns.
        num_quarters (int): Number of quarters to show.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    for i, (brand, df) in enumerate(forecast_data.items()):
        display_df = df.head(num_quarters)
        fig.add_trace(go.Bar(
            x=display_df['Period'],
            y=display_df['Ft_m'],
            name=brand,
            marker_color=_get_brand_color(i),
            hovertemplate=f'<b>{brand}</b><br>%{{x}}<br>Forecast: %{{y:,.0f}}<extra></extra>'
        ))
    
    layout = _base_layout('Forecast Overview — Next Quarters')
    layout.yaxis.title = 'Forecasted Sales (Ft+m)'
    layout.xaxis.title = 'Quarter'
    layout.barmode = 'group'
    fig.update_layout(layout)
    
    return to_json(fig)


def market_share_pie_chart(historical_data):
    """
    Donut chart of brand market share based on the latest period's Yt.
    
    Parameters:
        historical_data (dict): brand -> DataFrame with 'Yt' column.
    
    Returns:
        str: Plotly JSON string.
    """
    brands = []
    values = []
    colors = []
    
    for i, (brand, df) in enumerate(historical_data.items()):
        brands.append(brand)
        values.append(df.iloc[-1]['Yt'])
        colors.append(_get_brand_color(i))
    
    fig = go.Figure(data=[go.Pie(
        labels=brands,
        values=values,
        hole=0.45,
        marker=dict(colors=colors, line=dict(color=COLORS['white'], width=2)),
        textinfo='label+percent',
        textfont=dict(size=12),
        hovertemplate='<b>%{label}</b><br>Sales: %{value:,.0f}<br>Share: %{percent}<extra></extra>'
    )])
    
    layout = _base_layout('Brand Market Share (Latest Period)', height=400)
    layout.legend = dict(orientation='v', x=1.02, y=0.5)
    fig.update_layout(layout)
    
    return to_json(fig)


def historical_vs_fitted_chart(brand_df, brand_name):
    """
    Line chart: Yt (actual) vs Ft (fitted) for a single brand.
    
    Parameters:
        brand_df (pd.DataFrame): Brand DataFrame with 'Period', 'Yt', 'Ft' columns.
        brand_name (str): Brand name for the title.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=brand_df['Period'],
        y=brand_df['Yt'],
        mode='lines+markers',
        name='Actual (Yt)',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(size=7)
    ))
    
    fig.add_trace(go.Scatter(
        x=brand_df['Period'],
        y=brand_df['Ft'],
        mode='lines+markers',
        name='Fitted (Ft)',
        line=dict(color=COLORS['accent'], width=2.5, dash='dash'),
        marker=dict(size=7, symbol='diamond')
    ))
    
    layout = _base_layout(f'{brand_name} — Historical vs Fitted Values')
    layout.yaxis.title = 'Sales'
    layout.xaxis.title = 'Quarter'
    fig.update_layout(layout)
    
    return to_json(fig)


def level_area_chart(brand_df, brand_name):
    """
    Area chart of Level (Lt) over time for a single brand.
    
    Parameters:
        brand_df (pd.DataFrame): Brand DataFrame with 'Period' and 'Lt' columns.
        brand_name (str): Brand name.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=brand_df['Period'],
        y=brand_df['Lt'],
        mode='lines',
        fill='tozeroy',
        name='Level (Lt)',
        line=dict(color=COLORS['accent'], width=2),
        fillcolor='rgba(43, 127, 204, 0.2)',
        hovertemplate='%{x}<br>Level: %{y:,.2f}<extra></extra>'
    ))
    
    layout = _base_layout(f'{brand_name} — Level Component (Lt)')
    layout.yaxis.title = 'Level (Lt)'
    layout.xaxis.title = 'Quarter'
    fig.update_layout(layout)
    
    return to_json(fig)


def trend_line_chart(brand_df, brand_name):
    """
    Line chart of Trend (bt) over time for a single brand.
    
    Parameters:
        brand_df (pd.DataFrame): Brand DataFrame with 'Period' and 'bt' columns.
        brand_name (str): Brand name.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=brand_df['Period'],
        y=brand_df['bt'],
        mode='lines+markers',
        name='Trend (bt)',
        line=dict(color=COLORS['mid'], width=2.5),
        marker=dict(size=6, color=COLORS['primary']),
        hovertemplate='%{x}<br>Trend: %{y:,.2f}<extra></extra>'
    ))
    
    # Add zero reference line
    fig.add_hline(y=0, line_dash='dot', line_color='#999', line_width=1)
    
    layout = _base_layout(f'{brand_name} — Trend Component (bt)')
    layout.yaxis.title = 'Trend (bt)'
    layout.xaxis.title = 'Quarter'
    fig.update_layout(layout)
    
    return to_json(fig)


def seasonal_bar_chart(brand_df, brand_name):
    """
    Bar chart of Seasonal Index (St) grouped by quarter.
    
    Parameters:
        brand_df (pd.DataFrame): Brand DataFrame with 'Quarter', 'St', 'Year' columns.
        brand_name (str): Brand name.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    # Group by quarter to show seasonal pattern
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    years = sorted(brand_df['Year'].unique())
    
    for i, year in enumerate(years):
        year_data = brand_df[brand_df['Year'] == year]
        fig.add_trace(go.Bar(
            x=[f"Q{int(q)}" for q in year_data['Quarter']],
            y=year_data['St'],
            name=str(int(year)),
            marker_color=_get_brand_color(i),
            hovertemplate=f'{int(year)}<br>%{{x}}<br>Seasonal Index: %{{y:.4f}}<extra></extra>'
        ))
    
    # Add reference line at 1.0
    fig.add_hline(y=1.0, line_dash='dot', line_color='#999', line_width=1,
                  annotation_text='Neutral (1.0)', annotation_position='top right')
    
    layout = _base_layout(f'{brand_name} — Seasonal Index (St) by Quarter')
    layout.yaxis.title = 'Seasonal Index (St)'
    layout.xaxis.title = 'Quarter'
    layout.barmode = 'group'
    fig.update_layout(layout)
    
    return to_json(fig)


def forecast_line_chart(brand_df, forecast_df, brand_name):
    """
    Combined historical + projected future line chart with shaded forecast zone.
    
    Parameters:
        brand_df (pd.DataFrame): Historical data with 'Period' and 'Yt' columns.
        forecast_df (pd.DataFrame): Forecast data with 'Period' and 'Ft_m' columns.
        brand_name (str): Brand name.
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    # Historical line
    fig.add_trace(go.Scatter(
        x=brand_df['Period'],
        y=brand_df['Yt'],
        mode='lines+markers',
        name='Historical (Yt)',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(size=6)
    ))
    
    # Connect historical to forecast with a bridge point
    if not forecast_df.empty:
        bridge_x = [brand_df.iloc[-1]['Period']] + forecast_df['Period'].tolist()
        bridge_y = [brand_df.iloc[-1]['Yt']] + forecast_df['Ft_m'].tolist()
        
        fig.add_trace(go.Scatter(
            x=bridge_x,
            y=bridge_y,
            mode='lines+markers',
            name='Forecast (Ft+m)',
            line=dict(color=COLORS['accent'], width=2.5, dash='dash'),
            marker=dict(size=7, symbol='diamond', color=COLORS['accent'])
        ))
        
        # Shaded forecast area
        fig.add_trace(go.Scatter(
            x=forecast_df['Period'],
            y=forecast_df['Ft_m'],
            fill='tozeroy',
            mode='none',
            name='Forecast Zone',
            fillcolor='rgba(43, 127, 204, 0.1)',
            showlegend=False
        ))
    
    layout = _base_layout(f'{brand_name} — Sales Forecast')
    layout.yaxis.title = 'Sales'
    layout.xaxis.title = 'Quarter'
    fig.update_layout(layout)
    
    return to_json(fig)


def accuracy_grouped_bar_chart(accuracy_data):
    """
    Grouped bar chart of MAD, MSE, RMSE per brand.
    
    Parameters:
        accuracy_data (dict): brand -> {'MAD': float, 'MSE': float, 'RMSE': float, 'MAPE': float}
    
    Returns:
        str: Plotly JSON string.
    """
    brands = list(accuracy_data.keys())
    metrics = ['MAD', 'MSE', 'RMSE']
    colors_map = {
        'MAD': COLORS['primary'],
        'MSE': COLORS['accent'],
        'RMSE': COLORS['mid']
    }
    
    fig = go.Figure()
    
    for metric in metrics:
        values = [accuracy_data[b][metric] for b in brands]
        fig.add_trace(go.Bar(
            x=brands,
            y=values,
            name=metric,
            marker_color=colors_map[metric],
            hovertemplate=f'<b>%{{x}}</b><br>{metric}: %{{y:,.4f}}<extra></extra>'
        ))
    
    layout = _base_layout('Accuracy Metrics by Brand (MAD, MSE, RMSE)')
    layout.yaxis.title = 'Value'
    layout.xaxis.title = 'Brand'
    layout.barmode = 'group'
    fig.update_layout(layout)
    
    return to_json(fig)


def mape_bar_chart(accuracy_data):
    """
    MAPE bar chart per brand with green/yellow/red color thresholds.
    
    Parameters:
        accuracy_data (dict): brand -> {'MAPE': float}
    
    Returns:
        str: Plotly JSON string.
    """
    brands = list(accuracy_data.keys())
    mapes = [accuracy_data[b]['MAPE'] for b in brands]
    
    # Color each bar by threshold
    bar_colors = []
    for m in mapes:
        if m < 10:
            bar_colors.append(COLORS['green'])
        elif m <= 20:
            bar_colors.append(COLORS['yellow'])
        else:
            bar_colors.append(COLORS['red'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=brands,
        y=mapes,
        marker_color=bar_colors,
        text=[f'{m:.2f}%' for m in mapes],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>MAPE: %{y:.4f}%<extra></extra>'
    ))
    
    # Add threshold lines
    fig.add_hline(y=10, line_dash='dash', line_color=COLORS['green'], line_width=1,
                  annotation_text='Good (<10%)', annotation_position='top right',
                  annotation_font_color=COLORS['green'])
    fig.add_hline(y=20, line_dash='dash', line_color=COLORS['yellow'], line_width=1,
                  annotation_text='Fair (<20%)', annotation_position='top right',
                  annotation_font_color=COLORS['yellow'])
    
    layout = _base_layout('MAPE by Brand (Forecast Accuracy)')
    layout.yaxis.title = 'MAPE (%)'
    layout.xaxis.title = 'Brand'
    fig.update_layout(layout)
    
    return to_json(fig)


def multi_brand_forecast_chart(historical_data, forecast_data, selected_brands=None):
    """
    Multi-brand forecast line chart for the Forecast Explorer page.
    
    Parameters:
        historical_data (dict): brand -> historical DataFrame.
        forecast_data (dict): brand -> forecast DataFrame.
        selected_brands (list): Brands to include (None = all).
    
    Returns:
        str: Plotly JSON string.
    """
    fig = go.Figure()
    
    brands = selected_brands or list(forecast_data.keys())
    
    for i, brand in enumerate(brands):
        if brand not in forecast_data:
            continue
        
        color = _get_brand_color(i)
        
        # Historical
        if brand in historical_data:
            hist_df = historical_data[brand]
            fig.add_trace(go.Scatter(
                x=hist_df['Period'],
                y=hist_df['Yt'],
                mode='lines+markers',
                name=f'{brand} (Historical)',
                line=dict(color=color, width=2),
                marker=dict(size=5),
                legendgroup=brand
            ))
        
        # Forecast
        fc_df = forecast_data[brand]
        if not fc_df.empty:
            # Bridge from last historical to first forecast
            bridge_x = []
            bridge_y = []
            if brand in historical_data:
                h_df = historical_data[brand]
                bridge_x = [h_df.iloc[-1]['Period']]
                bridge_y = [h_df.iloc[-1]['Yt']]
            
            fig.add_trace(go.Scatter(
                x=bridge_x + fc_df['Period'].tolist(),
                y=bridge_y + fc_df['Ft_m'].tolist(),
                mode='lines+markers',
                name=f'{brand} (Forecast)',
                line=dict(color=color, width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond'),
                legendgroup=brand
            ))
    
    layout = _base_layout('Multi-Brand Forecast Comparison')
    layout.yaxis.title = 'Sales'
    layout.xaxis.title = 'Quarter'
    layout.height = 500
    fig.update_layout(layout)
    
    return to_json(fig)
