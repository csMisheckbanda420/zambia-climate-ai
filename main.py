import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from streamlit_searchbox import st_searchbox
from utils.data_loader import get_data_loader
from utils.alert_manager import get_alert_manager
from utils.trend_utils import create_trend_chart, create_risk_gauge

# Render.com specific configuration
if 'RENDER' in os.environ:
    # Disable file watcher on Render
    os.environ['STREAMLIT_SERVER_WATCH_FILES'] = 'false'
    
# Page config
st.set_page_config(
    page_title="Zambia Climate Early Warning System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .stButton button {
        background-color: #2c3e50;
        color: white;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #34495e;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    .risk-high {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-moderate {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-low {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stAlert {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = "Lusaka"
if 'page' not in st.session_state:
    st.session_state.page = "main"
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False

# Load data
@st.cache_resource
def init_system():
    try:
        data_loader = get_data_loader()
        alert_manager = get_alert_manager()
        return data_loader, alert_manager
    except Exception as e:
        st.error(f"Error initializing system: {e}")
        return None, None

data_loader, alert_manager = init_system()

if data_loader is None:
    st.error("Failed to load system. Please check your data files.")
    st.stop()

all_cities = data_loader.get_all_cities()

# Search function
def search_zambia_cities(search_term: str):
    if not search_term:
        return all_cities
    return [city for city in all_cities if search_term.lower() in city.lower()]

# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🌍 Zambia Climate Early Warning System</h1>
    <p style="margin: 10px 0 0 0;">AI-Powered Drought and Flood Forecasting</p>
</div>
""", unsafe_allow_html=True)

# Navigation
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

with col1:
    selected_city = st_searchbox(
        search_zambia_cities,
        placeholder="🔍 Search for a city (e.g., Lusaka, Livingstone)...",
        key="city_search",
        default=st.session_state.selected_city
    )
    if selected_city:
        st.session_state.selected_city = selected_city
        st.session_state.alert_sent = False

with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

with col3:
    if st.button("🌊 Flood Risk", use_container_width=True):
        st.session_state.page = "flood"
        st.rerun()

with col4:
    if st.button("☀️ Drought Risk", use_container_width=True):
        st.session_state.page = "drought"
        st.rerun()

st.divider()

# Main content
if st.session_state.selected_city:
    city = st.session_state.selected_city
    
    try:
        # Get data
        city_data = data_loader.get_city_data(city).tail(180)
        risks = data_loader.predict_risk(city)
        current = data_loader.get_current_conditions(city)
        coords = data_loader.get_city_coordinates(city)
        
        # Risk metrics
        st.subheader(f"📍 {city} - Current Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            flood_risk = risks['flood_risk']
            flood_delta = "🔴 HIGH" if flood_risk > 0.7 else "🟡 MODERATE" if flood_risk > 0.4 else "🟢 LOW"
            st.metric(
                "🌊 Flood Risk",
                f"{flood_risk:.1%}",
                delta=flood_delta,
                delta_color="inverse" if flood_risk > 0.7 else "off"
            )
        
        with col2:
            drought_risk = risks['drought_risk']
            drought_delta = "🔴 HIGH" if drought_risk > 0.7 else "🟡 MODERATE" if drought_risk > 0.4 else "🟢 LOW"
            st.metric(
                "☀️ Drought Risk",
                f"{drought_risk:.1%}",
                delta=drought_delta,
                delta_color="inverse" if drought_risk > 0.7 else "off"
            )
        
        with col3:
            soil_moisture = current['soil_moisture']
            soil_delta = "Critical" if soil_moisture < 30 else "Normal"
            st.metric(
                "💧 Soil Moisture",
                f"{soil_moisture:.0f}%",
                delta=soil_delta,
                delta_color="inverse"
            )
        
        with col4:
            temp_avg = city_data['Temp_C'].mean()
            temp_diff = current['temperature'] - temp_avg
            st.metric(
                "🌡️ Temperature",
                f"{current['temperature']:.1f}°C",
                delta=f"{temp_diff:+.1f}°C vs avg"
            )
        
        # Alert Section
        if st.session_state.page == "flood" and risks['flood_alert'] and not st.session_state.alert_sent:
            st.markdown("""
            <div class="risk-high">
                <strong>🚨 FLOOD ALERT!</strong><br>
                High flood risk detected. Immediate action recommended.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📢 Send Flood Alert", type="primary"):
                alert_manager.send_alert(
                    city, 
                    "Flood", 
                    risks['flood_risk'], 
                    f"High flood risk in {city}. Please take precautions."
                )
                st.session_state.alert_sent = True
                st.success(f"✅ Alert sent for {city}!")
                st.balloons()
                st.rerun()
        
        elif st.session_state.page == "drought" and risks['drought_alert'] and not st.session_state.alert_sent:
            st.markdown("""
            <div class="risk-high">
                <strong>⚠️ DROUGHT ALERT!</strong><br>
                Severe drought conditions detected. Water conservation critical.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📢 Send Drought Alert", type="primary"):
                alert_manager.send_alert(
                    city, 
                    "Drought", 
                    risks['drought_risk'], 
                    f"Drought conditions in {city}. Please conserve water."
                )
                st.session_state.alert_sent = True
                st.success(f"✅ Alert sent for {city}!")
                st.balloons()
                st.rerun()
        
        # Charts
        st.subheader("📊 Climate Trends")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.page == "drought":
                st.plotly_chart(
                    create_trend_chart(city_data, city, 'soil_moisture'), 
                    use_container_width=True,
                    key=f"soil_chart_{city}"
                )
            else:
                st.plotly_chart(
                    create_trend_chart(city_data, city, 'rainfall'), 
                    use_container_width=True,
                    key=f"rainfall_chart_{city}"
                )
        
        with col2:
            st.plotly_chart(
                create_trend_chart(city_data, city, 'temperature'), 
                use_container_width=True,
                key=f"temp_chart_{city}"
            )
        
        # Risk Gauges
        st.subheader("📈 Risk Assessment")
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_risk_gauge(risks['flood_risk'], "Flood Risk Level"),
                use_container_width=True,
                key=f"flood_gauge_{city}"
            )
        
        with col2:
            st.plotly_chart(
                create_risk_gauge(risks['drought_risk'], "Drought Risk Level"),
                use_container_width=True,
                key=f"drought_gauge_{city}"
            )
        
        # Statistics Section
        with st.expander("📊 View Detailed Statistics"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Rainfall Statistics**")
                st.write(f"Average: {city_data['Rainfall_mm'].mean():.1f} mm")
                st.write(f"Maximum: {city_data['Rainfall_mm'].max():.1f} mm")
                st.write(f"Last 7 days: {city_data['Rainfall_mm'].tail(7).mean():.1f} mm")
            
            with col2:
                st.write("**Temperature Statistics**")
                st.write(f"Average: {city_data['Temp_C'].mean():.1f}°C")
                st.write(f"Maximum: {city_data['Temp_C'].max():.1f}°C")
                st.write(f"Minimum: {city_data['Temp_C'].min():.1f}°C")
            
            with col3:
                st.write("**Soil Moisture Statistics**")
                st.write(f"Average: {city_data['Soil_Moisture_Pct'].mean():.1f}%")
                st.write(f"Minimum: {city_data['Soil_Moisture_Pct'].min():.1f}%")
                st.write(f"Current: {current['soil_moisture']:.1f}%")
        
        # Recent Alerts
        with st.expander("📋 Recent Alerts"):
            alerts_df = alert_manager.get_alerts(city=city, days=30)
            if len(alerts_df) > 0:
                st.dataframe(
                    alerts_df[['alert_type', 'severity', 'message', 'sent_at']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No recent alerts for this city")
        
        # City Information
        with st.expander("ℹ️ City Information"):
            st.write(f"""
            - **City:** {city}
            - **Coordinates:** {coords['lat']:.2f}°S, {coords['lon']:.2f}°E
            - **Elevation:** {coords['elevation']:.0f}m
            - **Current Rainfall:** {current['rainfall']:.1f} mm
            - **River Level:** {current['river_level']:.1f}m
            - **Last Update:** {current['date'].strftime('%Y-%m-%d')}
            """)
    
    except Exception as e:
        st.error(f"Error loading data for {city}: {e}")
        st.info("Please try another city or check your data files.")

else:
    st.info("🔍 Please search for a city to view climate data and forecasts")

# Footer
st.divider()
st.markdown("""
<p style='text-align: center; color: #7f8c8d; font-size: 12px;'>
    🌍 Powered by AI | 📊 Data: 1996-2026 | 🚨 For early warning and planning purposes
</p>
""", unsafe_allow_html=True)