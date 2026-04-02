import streamlit as st
from streamlit_folium import st_folium
from utils.data_loader import get_data_loader
from utils.map_utils import create_risk_map
from utils.trend_utils import create_trend_chart, create_risk_gauge
from utils.alert_manager import get_alert_manager

st.set_page_config(page_title="Flood Risk Map", layout="wide")

# Initialize
data_loader = get_data_loader()
alert_manager = get_alert_manager()
all_cities = data_loader.get_all_cities()

st.title("🌊 Flood Risk Monitoring System")
st.markdown("Real-time flood risk assessment for Zambian cities")

# Header navigation
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    city_options = all_cities
    selected_city = st.selectbox("Select City", city_options)

with col2:
    if st.button("🏠 Dashboard"):
        st.switch_page("main.py")

with col3:
    if st.button("☀️ Drought Page"):
        st.switch_page("pages/2_Droughts.py")

# Get risk data for all cities
city_risks = {}
city_data_list = []
for city in all_cities:
    risks = data_loader.predict_risk(city)
    city_risks[city] = risks['flood_risk']
    coords = data_loader.get_city_coordinates(city)
    city_data_list.append({
        'city': city,
        'lat': coords['lat'],
        'lon': coords['lon']
    })

# Create risk map
st.subheader("🗺️ Flood Risk Map")
risk_map = create_risk_map(city_data_list, city_risks, map_type='flood')
st_folium(risk_map, width=1200, height=500)

# Selected city details
if selected_city:
    st.subheader(f"📊 {selected_city} Flood Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    risks = data_loader.predict_risk(selected_city)
    city_data = data_loader.get_city_data(selected_city).tail(90)
    current = data_loader.get_current_conditions(selected_city)
    
    with col1:
        st.metric(
            "Flood Risk Level",
            f"{risks['flood_risk']:.1%}",
            delta="ALERT" if risks['flood_risk'] > 0.7 else "WATCH" if risks['flood_risk'] > 0.4 else "NORMAL"
        )
    
    with col2:
        st.metric(
            "Current Rainfall",
            f"{current['rainfall']:.1f} mm",
            delta="Extreme" if current['rainfall'] > 50 else "Normal"
        )
    
    with col3:
        st.metric(
            "River Level",
            f"{current['river_level']:.1f} m",
            delta="Flood Stage" if current['river_level'] > 8 else "Normal"
        )
    
    # Rainfall trend
    st.plotly_chart(
        create_trend_chart(city_data, selected_city, 'rainfall'),
        use_container_width=True
    )
    
    # Risk gauge
    st.plotly_chart(
        create_risk_gauge(risks['flood_risk'], f"{selected_city} Flood Risk"),
        use_container_width=True
    )
    
    # High risk cities section
    st.subheader("⚠️ High Flood Risk Cities")
    high_risk_cities = [city for city, risk in city_risks.items() if risk > 0.7]
    
    if high_risk_cities:
        for city in high_risk_cities:
            city_risks_data = data_loader.predict_risk(city)
            city_current = data_loader.get_current_conditions(city)
            
            with st.expander(f"🚨 {city} - Immediate Action Required"):
                st.write(f"""
                - **Risk Level:** {city_risks_data['flood_risk']:.1%}
                - **Current Rainfall:** {city_current['rainfall']:.1f} mm
                - **River Level:** {city_current['river_level']:.1f} m
                - **Recommended Action:** Evacuation planning for low-lying areas
                - **Alert Status:** Active
                """)
                
                if st.button(f"Send Alert to {city}", key=f"alert_{city}"):
                    alert_manager.send_alert(
                        city,
                        "Flood",
                        city_risks_data['flood_risk'],
                        f"High flood risk in {city}. Immediate action recommended."
                    )
                    st.success(f"Alert sent for {city}!")
    else:
        st.success("✅ No high flood risk cities at this time")
    
    # Safety recommendations
    with st.expander("🆘 Flood Safety Recommendations"):
        st.write("""
        **Before Flood:**
        - Know your area's flood risk
        - Prepare an emergency kit
        - Keep important documents safe
        
        **During Flood:**
        - Move to higher ground immediately
        - Avoid walking or driving through flood waters
        - Follow evacuation orders
        
        **After Flood:**
        - Wait for authorities to declare it safe
        - Avoid floodwater as it may be contaminated
        - Document damage for insurance
        """)