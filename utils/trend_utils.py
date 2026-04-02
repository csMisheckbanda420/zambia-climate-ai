import plotly.graph_objects as go
import pandas as pd

def create_trend_chart(city_data, city_name, metric='rainfall'):
    """Create interactive trend chart"""
    
    if metric == 'rainfall':
        y_col = 'Rainfall_mm'
        title = f'🌧️ Rainfall Trend - {city_name}'
        y_label = 'Rainfall (mm)'
        color = '#1f77b4'
        threshold = 50
        threshold_label = 'Flood Alert'
    elif metric == 'temperature':
        y_col = 'Temp_C'
        title = f'🌡️ Temperature Trend - {city_name}'
        y_label = 'Temperature (°C)'
        color = '#ff7f0e'
        threshold = None
    else:
        y_col = 'Soil_Moisture_Pct'
        title = f'💧 Soil Moisture Trend - {city_name}'
        y_label = 'Soil Moisture (%)'
        color = '#2ca02c'
        threshold = 30
        threshold_label = 'Drought Alert'
    
    fig = go.Figure()
    
    # Daily data
    fig.add_trace(go.Scatter(
        x=city_data['Date'],
        y=city_data[y_col],
        mode='lines',
        name='Daily',
        line=dict(color=color, width=1, dash='dot'),
        opacity=0.5
    ))
    
    # 7-day moving average
    fig.add_trace(go.Scatter(
        x=city_data['Date'],
        y=city_data[y_col].rolling(7, min_periods=1).mean(),
        mode='lines',
        name='7-day Avg',
        line=dict(color=color, width=2)
    ))
    
    # Add threshold line
    if threshold:
        fig.add_hline(y=threshold, line_dash="dash", line_color="red",
                      annotation_text=threshold_label)
    
    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_title='Date',
        yaxis_title=y_label,
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_risk_gauge(risk_score, title):
    """Create a gauge chart for risk visualization"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score * 100,
        title={'text': title, 'font': {'size': 14}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 30], 'color': '#d4edda'},
                {'range': [30, 70], 'color': '#fff3cd'},
                {'range': [70, 100], 'color': '#f8d7da'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        },
        number={'suffix': "%", 'font': {'size': 20}}
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig