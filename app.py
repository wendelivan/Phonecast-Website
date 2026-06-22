"""
app.py — Flask application entry point for phonecast.

Smartphone Sales Forecasting Web Application using
Multiplicative Holt-Winters Time Series Analysis.
"""

import os
import json
import tempfile
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file, jsonify
)

from modules.holt_winters import detect_brands, compute_fitted_values, generate_forecast, process_all_brands
from modules.accuracy import accuracy_summary, get_mape_category, get_best_worst_brands
from modules.charts import (
    all_brands_historical_chart, forecast_overview_bar_chart, market_share_pie_chart,
    historical_vs_fitted_chart, level_area_chart, trend_line_chart,
    seasonal_bar_chart, forecast_line_chart, accuracy_grouped_bar_chart,
    mape_bar_chart, multi_brand_forecast_chart
)
from modules.report_gen import generate_pdf_report, generate_csv_export

app = Flask(__name__)
app.secret_key = 'phonecast-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# In-memory storage for session data (single-user, session-based)
app_data = {}

REQUIRED_COLUMNS = [
    'Brand', 'Year', 'Quarter', 'Alpha', 'Beta', 'Gamma',
    'Yt', 'St_s', 'Lt_1', 'bt_1', 'Lt', 'bt', 'St', 'm'
]


def get_session_data():
    """Retrieve processed data for the current session."""
    session_id = session.get('session_id')
    if session_id and session_id in app_data:
        return app_data[session_id]
    return None


def validate_csv(df):
    """
    Validate the uploaded CSV file against required columns and data types.
    
    Returns:
        tuple: (is_valid: bool, errors: list of error strings)
    """
    errors = []
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors
    
    # Check data types
    string_cols = ['Brand']
    int_cols = ['Year', 'Quarter']
    float_cols = ['Alpha', 'Beta', 'Gamma', 'Yt', 'St_s', 'Lt_1', 'bt_1', 'Lt', 'bt', 'St']
    int_float_cols = ['m']
    
    for col in int_cols:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isna().any():
                errors.append(f"Column '{col}' contains non-numeric values.")
        except Exception:
            errors.append(f"Column '{col}' must contain integer values.")
    
    for col in float_cols:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isna().any():
                errors.append(f"Column '{col}' contains non-numeric values.")
        except Exception:
            errors.append(f"Column '{col}' must contain numeric values.")
    
    # Validate Quarter range (1-4)
    if 'Quarter' in df.columns and not df['Quarter'].isna().all():
        invalid_quarters = df[(df['Quarter'] < 1) | (df['Quarter'] > 4)]
        if not invalid_quarters.empty:
            errors.append("Column 'Quarter' must contain values between 1 and 4.")
    
    # Validate Alpha, Beta, Gamma range (0-1)
    for col in ['Alpha', 'Beta', 'Gamma']:
        if col in df.columns and not df[col].isna().all():
            invalid = df[(df[col] < 0) | (df[col] > 1)]
            if not invalid.empty:
                errors.append(f"Column '{col}' must contain values between 0 and 1.")
    
    # Validate Yt > 0
    if 'Yt' in df.columns and not df['Yt'].isna().all():
        if (df['Yt'] <= 0).any():
            errors.append("Column 'Yt' must contain positive non-zero values.")
    
    # Validate m >= 1
    if 'm' in df.columns and not df['m'].isna().all():
        df['m'] = pd.to_numeric(df['m'], errors='coerce')
        if (df['m'] < 1).any():
            errors.append("Column 'm' must contain values >= 1.")
    
    return len(errors) == 0, errors


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Home page with CSV upload interface."""
    return render_template('index.html', required_columns=REQUIRED_COLUMNS)


@app.route('/upload', methods=['POST'])
def upload():
    """Handle CSV file upload, validate, and process."""
    if 'file' not in request.files:
        flash('No file selected. Please choose a CSV file.', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected. Please choose a CSV file.', 'error')
        return redirect(url_for('index'))
    
    if not file.filename.lower().endswith('.csv'):
        flash('Please upload a .csv file. Other file formats are not supported.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Read CSV
        df = pd.read_csv(file)
        
        # Validate
        is_valid, errors = validate_csv(df)
        
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('index'))
        
        # Ensure numeric types
        numeric_cols = ['Year', 'Quarter', 'Alpha', 'Beta', 'Gamma',
                       'Yt', 'St_s', 'Lt_1', 'bt_1', 'Lt', 'bt', 'St', 'm']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Process all brands
        processed = process_all_brands(df, forecast_quarters=4)
        
        # Compute accuracy
        acc_data = accuracy_summary(processed['historical'])
        
        # Find best accuracy brand
        best_brand, worst_brand = get_best_worst_brands(acc_data)
        processed['best_accuracy_brand'] = best_brand
        processed['worst_accuracy_brand'] = worst_brand
        processed['accuracy'] = acc_data
        
        # Store in session
        import uuid
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        app_data[session_id] = {
            'raw_df': df,
            'processed': processed,
            'accuracy': acc_data
        }
        
        flash('CSV file uploaded and processed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Main results dashboard."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    accuracy = data['accuracy']
    
    # Generate charts
    hist_chart = all_brands_historical_chart(processed['historical'])
    forecast_chart = forecast_overview_bar_chart(processed['forecasts'])
    pie_chart = market_share_pie_chart(processed['historical'])
    
    # Add MAPE category to summaries
    for brand in processed['brands']:
        if brand in accuracy:
            processed['summary'][brand]['mape'] = accuracy[brand]['MAPE']
            processed['summary'][brand]['mape_category'] = get_mape_category(accuracy[brand]['MAPE'])
    
    return render_template('dashboard.html',
        processed=processed,
        accuracy=accuracy,
        hist_chart=hist_chart,
        forecast_chart=forecast_chart,
        pie_chart=pie_chart
    )


@app.route('/brand/<brand_name>')
def brand_detail(brand_name):
    """Per-brand detail page."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    accuracy = data['accuracy']
    
    if brand_name not in processed['historical']:
        flash(f'Brand "{brand_name}" not found in the data.', 'error')
        return redirect(url_for('dashboard'))
    
    brand_df = processed['historical'][brand_name]
    forecast_df = processed['forecasts'][brand_name]
    brand_accuracy = accuracy.get(brand_name, {})
    
    # Generate brand-specific charts
    hist_fitted = historical_vs_fitted_chart(brand_df, brand_name)
    level_chart = level_area_chart(brand_df, brand_name)
    trend_chart = trend_line_chart(brand_df, brand_name)
    season_chart = seasonal_bar_chart(brand_df, brand_name)
    fc_chart = forecast_line_chart(brand_df, forecast_df, brand_name)
    
    # MAPE category
    mape_category = get_mape_category(brand_accuracy.get('MAPE', 0)) if brand_accuracy else 'green'
    
    return render_template('brand.html',
        brand_name=brand_name,
        brand_df=brand_df,
        forecast_df=forecast_df,
        accuracy=brand_accuracy,
        mape_category=mape_category,
        hist_fitted_chart=hist_fitted,
        level_chart=level_chart,
        trend_chart=trend_chart,
        seasonal_chart=season_chart,
        forecast_chart=fc_chart,
        brands=processed['brands']
    )


@app.route('/forecast')
def forecast_page():
    """Forecast explorer page."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    
    return render_template('forecast.html',
        brands=processed['brands'],
        processed=processed
    )


@app.route('/api/forecast', methods=['POST'])
def api_forecast():
    """API endpoint for dynamic forecast generation."""
    data = get_session_data()
    if not data:
        return jsonify({'error': 'No data uploaded'}), 400
    
    req_data = request.get_json()
    num_quarters = min(max(int(req_data.get('quarters', 4)), 1), 12)
    selected_brands = req_data.get('brands', data['processed']['brands'])
    
    raw_df = data['raw_df']
    
    # Recompute forecasts with new horizon
    new_forecasts = {}
    historical = data['processed']['historical']
    
    for brand in selected_brands:
        if brand in historical:
            brand_df = historical[brand]
            forecast_df = generate_forecast(brand_df, num_quarters)
            new_forecasts[brand] = forecast_df
    
    # Generate chart
    chart = multi_brand_forecast_chart(
        {b: historical[b] for b in selected_brands if b in historical},
        new_forecasts,
        selected_brands
    )
    
    # Build forecast table data
    table_data = {}
    periods = []
    for brand, df in new_forecasts.items():
        if not df.empty:
            table_data[brand] = {row['Period']: round(row['Ft_m'], 2) for _, row in df.iterrows()}
            if not periods:
                periods = df['Period'].tolist()
    
    return jsonify({
        'chart': chart,
        'table': table_data,
        'periods': periods
    })


@app.route('/accuracy')
def accuracy_page():
    """Accuracy analysis page."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    accuracy = data['accuracy']
    
    # Generate accuracy charts
    acc_bar = accuracy_grouped_bar_chart(accuracy)
    mape_chart = mape_bar_chart(accuracy)
    
    best, worst = get_best_worst_brands(accuracy)
    
    # Add MAPE categories
    acc_with_categories = {}
    for brand, metrics in accuracy.items():
        acc_with_categories[brand] = {
            **metrics,
            'mape_category': get_mape_category(metrics['MAPE'])
        }
    
    return render_template('accuracy.html',
        accuracy=acc_with_categories,
        brands=processed['brands'],
        acc_bar_chart=acc_bar,
        mape_chart=mape_chart,
        best_brand=best,
        worst_brand=worst
    )


@app.route('/report')
def report_page():
    """Report generation page."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    accuracy = data['accuracy']
    
    return render_template('report.html',
        processed=processed,
        accuracy=accuracy
    )


@app.route('/download/pdf')
def download_pdf():
    """Generate and download PDF report."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    accuracy = data['accuracy']
    
    pdf_buffer = generate_pdf_report(processed, accuracy, processed['forecasts'])
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='phonecast_report.pdf'
    )


@app.route('/download/csv')
def download_csv():
    """Generate and download CSV export."""
    data = get_session_data()
    if not data:
        flash('Please upload a CSV file first.', 'error')
        return redirect(url_for('index'))
    
    processed = data['processed']
    
    csv_buffer = generate_csv_export(processed, processed['forecasts'])
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='phonecast_data_export.csv'
    )


@app.route('/download/forecast-csv', methods=['POST'])
def download_forecast_csv():
    """Download forecast table as CSV."""
    data = get_session_data()
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    req_data = request.get_json()
    num_quarters = min(max(int(req_data.get('quarters', 4)), 1), 12)
    selected_brands = req_data.get('brands', data['processed']['brands'])
    
    historical = data['processed']['historical']
    
    import io
    buffer = io.BytesIO()
    
    rows = []
    for brand in selected_brands:
        if brand in historical:
            brand_df = historical[brand]
            forecast_df = generate_forecast(brand_df, num_quarters)
            for _, row in forecast_df.iterrows():
                rows.append({
                    'Brand': brand,
                    'Period': row['Period'],
                    'Year': int(row['Year']),
                    'Quarter': int(row['Quarter']),
                    'Forecast_Ft_m': round(row['Ft_m'], 4)
                })
    
    result_df = pd.DataFrame(rows)
    csv_string = result_df.to_csv(index=False)
    buffer.write(csv_string.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='phonecast_forecast.csv'
    )


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)
