"""
report_gen.py — PDF and CSV report generator for phonecast.

Generates downloadable PDF reports and CSV exports of
all computation results and forecasts.
"""

import io
import csv
import pandas as pd
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# phonecast colors for ReportLab
PC_PRIMARY = colors.HexColor('#0D2B6E')
PC_ACCENT = colors.HexColor('#2B7FCC')
PC_MID = colors.HexColor('#1A56A0')
PC_LIGHT = colors.HexColor('#D0E4F5')
PC_BG = colors.HexColor('#F4F7FB')
PC_GREEN = colors.HexColor('#28A745')
PC_YELLOW = colors.HexColor('#FFC107')
PC_RED = colors.HexColor('#DC3545')


def _get_styles():
    """Create custom paragraph styles for the PDF report."""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'PhonecastTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=PC_PRIMARY,
        spaceAfter=6,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'PhonecastSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=PC_ACCENT,
        spaceAfter=20,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PC_PRIMARY,
        spaceBefore=20,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        'BrandHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=PC_MID,
        spaceBefore=14,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=PC_PRIMARY
    ))
    
    styles.add(ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        leading=14
    ))
    
    return styles


def _make_table(headers, rows, col_widths=None):
    """Create a styled ReportLab table."""
    data = [headers] + rows
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PC_MID),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PC_LIGHT]),
    ]))
    
    return table


def generate_pdf_report(processed_data, accuracy_data, forecast_data_dict):
    """
    Generate a comprehensive PDF report with all brand tables, accuracy metrics,
    and forecast summaries.
    
    Parameters:
        processed_data (dict): Output from process_all_brands().
        accuracy_data (dict): Output from accuracy_summary().
        forecast_data_dict (dict): brand -> forecast DataFrame.
    
    Returns:
        io.BytesIO: PDF file in memory.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = _get_styles()
    elements = []
    
    # === Title Page ===
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph('phonecast', styles['PhonecastTitle']))
    elements.append(Paragraph('Smartphone Sales Forecasting Report', styles['PhonecastSubtitle']))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
        styles['BodyText']
    ))
    elements.append(Paragraph(
        f'Total Brands: {processed_data["total_brands"]} | '
        f'Total Records: {processed_data["total_records"]} | '
        f'Date Range: {processed_data["date_range"]}',
        styles['BodyText']
    ))
    elements.append(PageBreak())
    
    # === Accuracy Summary ===
    elements.append(Paragraph('Forecast Accuracy Summary', styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=1, color=PC_ACCENT))
    elements.append(Spacer(1, 0.2*inch))
    
    acc_headers = ['Brand', 'MAD', 'MSE', 'RMSE', 'MAPE (%)']
    acc_rows = []
    for brand, metrics in accuracy_data.items():
        acc_rows.append([
            brand,
            f'{metrics["MAD"]:.4f}',
            f'{metrics["MSE"]:.4f}',
            f'{metrics["RMSE"]:.4f}',
            f'{metrics["MAPE"]:.4f}%'
        ])
    
    acc_table = _make_table(acc_headers, acc_rows, col_widths=[2.5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    elements.append(acc_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Best/worst accuracy
    sorted_acc = sorted(accuracy_data.items(), key=lambda x: x[1]['MAPE'])
    if sorted_acc:
        best = sorted_acc[0]
        worst = sorted_acc[-1]
        elements.append(Paragraph(
            f'<b>Best Accuracy:</b> {best[0]} (MAPE: {best[1]["MAPE"]:.4f}%)',
            styles['BodyText']
        ))
        elements.append(Paragraph(
            f'<b>Lowest Accuracy:</b> {worst[0]} (MAPE: {worst[1]["MAPE"]:.4f}%)',
            styles['BodyText']
        ))
    
    elements.append(PageBreak())
    
    # === Per-Brand Details ===
    for brand in processed_data['brands']:
        elements.append(Paragraph(f'{brand} — Detailed Analysis', styles['SectionHeader']))
        elements.append(HRFlowable(width='100%', thickness=1, color=PC_ACCENT))
        elements.append(Spacer(1, 0.2*inch))
        
        brand_df = processed_data['historical'][brand]
        
        # Holt-Winters Table
        elements.append(Paragraph('Holt-Winters Computation Table', styles['BrandHeader']))
        hw_headers = ['Year', 'Qtr', 'Yt', 'Lt', 'bt', 'St', 'Ft']
        hw_rows = []
        for _, row in brand_df.iterrows():
            hw_rows.append([
                str(int(row['Year'])),
                f'Q{int(row["Quarter"])}',
                f'{row["Yt"]:.2f}',
                f'{row["Lt"]:.4f}',
                f'{row["bt"]:.4f}',
                f'{row["St"]:.4f}',
                f'{row["Ft"]:.2f}'
            ])
        
        hw_table = _make_table(hw_headers, hw_rows,
                               col_widths=[1.8*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        elements.append(hw_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Forecast Table
        forecast_df = forecast_data_dict.get(brand)
        if forecast_df is not None and not forecast_df.empty:
            elements.append(Paragraph('Forecast Values', styles['BrandHeader']))
            fc_headers = ['Period', 'Steps Ahead (m)', 'Forecast (Ft+m)']
            fc_rows = []
            for _, row in forecast_df.iterrows():
                fc_rows.append([
                    row['Period'],
                    str(int(row['m'])),
                    f'{row["Ft_m"]:,.2f}'
                ])
            
            fc_table = _make_table(fc_headers, fc_rows,
                                    col_widths=[4*cm, 4*cm, 4*cm])
            elements.append(fc_table)
        
        # Accuracy for this brand
        if brand in accuracy_data:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph('Accuracy Metrics', styles['BrandHeader']))
            m = accuracy_data[brand]
            elements.append(Paragraph(
                f'MAD: {m["MAD"]:.4f}  |  MSE: {m["MSE"]:.4f}  |  '
                f'RMSE: {m["RMSE"]:.4f}  |  MAPE: {m["MAPE"]:.4f}%',
                styles['BodyText']
            ))
        
        elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_csv_export(processed_data, forecast_data_dict):
    """
    Generate a CSV export containing all historical data with Holt-Winters values
    and forecasted values appended.
    
    Parameters:
        processed_data (dict): Output from process_all_brands().
        forecast_data_dict (dict): brand -> forecast DataFrame.
    
    Returns:
        io.BytesIO: CSV file in memory.
    """
    buffer = io.BytesIO()
    
    # Combine all historical data
    all_historical = []
    for brand, df in processed_data['historical'].items():
        export_df = df[['Brand', 'Year', 'Quarter', 'Yt', 'Lt', 'bt', 'St', 'Ft']].copy()
        export_df['Type'] = 'Historical'
        all_historical.append(export_df)
    
    # Combine all forecast data
    all_forecasts = []
    for brand, df in forecast_data_dict.items():
        if not df.empty:
            fc_df = pd.DataFrame({
                'Brand': df['Brand'],
                'Year': df['Year'],
                'Quarter': df['Quarter'],
                'Yt': '',
                'Lt': '',
                'bt': '',
                'St': '',
                'Ft': df['Ft_m'],
                'Type': 'Forecast'
            })
            all_forecasts.append(fc_df)
    
    # Merge and write
    combined = pd.concat(all_historical + all_forecasts, ignore_index=True)
    csv_string = combined.to_csv(index=False)
    buffer.write(csv_string.encode('utf-8'))
    buffer.seek(0)
    
    return buffer
