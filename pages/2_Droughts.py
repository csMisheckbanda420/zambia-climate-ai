import streamlit as st
from streamlit_folium import st_folium
from utils.data_loader import get_data_loader
from utils.map_utils import create_risk_map
from utils.trend_utils import create_trend_chart, create_risk_gauge
from utils.alert_manager import get_alert_manager

st.set_page_config(page_title="Drought Risk Map", layout="wide")

# Initialize
data_loader = get_data_loader()
alert_manager = get_alert_manager()
all_cities = data_loader.get_all_cities()

st.title("☀️ Drought Risk Monitoring System")
st.markdown("Real-time drought risk assessment for Zambian cities")

# Header navigation
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    city_options = all_cities
    selected_city = st.selectbox("Select City", city_options)

with col2:
    if st.button("🏠 Dashboard"):
        st.switch_page("main.py")

with col3:
    if st.button("🌊 Flood Page"):
        st.switch_page("pages/1_Floods.py")

# Get drought risk data
city_drought_risks = {}
city_data_list = []
for city in all_cities:
    risks = data_loader.predict_risk(city)
    city_drought_risks[city] = risks['drought_risk']
    coords = data_loader.get_city_coordinates(city)
    city_data_list.append({
        'city': city,
        'lat': coords['lat'],
        'lon': coords['lon']
    })

# Drought risk map
st.subheader("🗺️ Drought Risk Map")
risk_map = create_risk_map(city_data_list, city_drought_risks, map_type='drought')
st_folium(risk_map, width=1200, height=500)

# Selected city analysis
if selected_city:
    st.subheader(f"📊 {selected_city} Drought Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    risks = data_loader.predict_risk(selected_city)
    city_data = data_loader.get_city_data(selected_city).tail(180)
    current = data_loader.get_current_conditions(selected_city)
    
    with col1:
        st.metric(
            "Drought Risk Level",
            f"{risks['drought_risk']:.1%}",
            delta="ALERT" if risks['drought_risk'] > 0.7 else "WATCH" if risks['drought_risk'] > 0.4 else "NORMAL"
        )
    
    with col2:
        st.metric(
            "Soil Moisture",
            f"{current['soil_moisture']:.0f}%",
            delta="Critical" if current['soil_moisture'] < 30 else "Adequate"
        )
    
    with col3:
        rain_90d = city_data['Rainfall_90d_avg'].iloc[-1]
        st.metric(
            "90-Day Rainfall Avg",
            f"{rain_90d:.1f} mm",
            delta="Below Normal" if rain_90d < 2 else "Normal"
        )
    
    # Soil moisture trend
    st.plotly_chart(
        create_trend_chart(city_data, selected_city, 'soil_moisture'),
        use_container_width=True
    )
    
    # Risk gauge
    st.plotly_chart(
        create_risk_gauge(risks['drought_risk'], f"{selected_city} Drought Risk"),
        use_container_width=True
    )
    
    # Agricultural impact section
    st.subheader("🌾 Agricultural Impact Assessment")
    
    if risks['drought_risk'] > 0.7:
        st.error("""
        **🚨 SEVERE DROUGHT CONDITIONS DETECTED**
        
        **Immediate Actions Required:**
        - Implement emergency irrigation
        - Consider early harvest for vulnerable crops
        - Monitor livestock water sources daily
        - Contact agricultural extension services
        
        **Expected Impact:**
        - 50-70% crop yield reduction expected
        - Critical water shortage for livestock
        - Urgent intervention needed
        """)
        
        if st.button("📢 Send Emergency Alert", type="primary"):
            alert_manager.send_alert(
                selected_city,
                "Drought",
                risks['drought_risk'],
                f"Severe drought in {selected_city}. Emergency water conservation required."
            )
            st.success(f"Emergency alert sent for {selected_city}!")
            st.balloons()
    
    elif risks['drought_risk'] > 0.4:
        st.warning("""
        **⚠️ MODERATE DROUGHT CONDITIONS**
        
        **Recommended Actions:**
        - Schedule irrigation optimization
        - Monitor crop stress indicators
        - Prepare water conservation measures
        - Review feed supplies for livestock
        
        **Expected Impact:**
        - 20-40% crop yield reduction possible
        - Water conservation recommended
        - Regular monitoring required
        """)
    else:
        st.success("""
        **✅ NORMAL CONDITIONS**
        
        **Current Status:**
        - Adequate soil moisture levels
        - Normal rainfall patterns
        - Standard agricultural practices recommended
        - Continue routine monitoring
        """)
    
    # Water availability forecast
    with st.expander("💧 Water Availability Forecast"):
        st.write(f"""
        Based on current trends and historical patterns:
        
        **Surface Water:** {'Reduced' if risks['drought_risk'] > 0.4 else 'Normal'} availability
        **Groundwater:** {'Declining' if risks['drought_risk'] > 0.4 else 'Stable'} levels
        **Irrigation Needs:** {'High' if risks['drought_risk'] > 0.4 else 'Standard'}
        
        **Recommendation:** {
            'Implement water conservation immediately' if risks['drought_risk'] > 0.7 
            else 'Begin water conservation planning' if risks['drought_risk'] > 0.4 
            else 'No restrictions needed'
        }
        """)
    
    # Vulnerable areas
    st.subheader("⚠️ Vulnerable Areas")
    vulnerable_cities = [city for city, risk in city_drought_risks.items() if risk > 0.4]
    
    if vulnerable_cities:
        for city in vulnerable_cities[:5]:
            city_risks = data_loader.predict_risk(city)
            city_current = data_loader.get_current_conditions(city)
            
            with st.expander(f"⚠️ {city} - Drought Watch"):
                st.write(f"""
                - **Risk Level:** {city_risks['drought_risk']:.1%}
                - **Soil Moisture:** {city_current['soil_moisture']:.0f}%
                - **Current Rainfall:** {city_current['rainfall']:.1f} mm
                - **Recommended:** Early intervention and water conservation
                """)
                
                if city_risks['drought_risk'] > 0.7:
                    if st.button(f"Send Alert to {city}", key=f"alert_{city}"):
                        alert_manager.send_alert(
                            city,
                            "Drought",
                            city_risks['drought_risk'],
                            f"Severe drought conditions in {city}. Water conservation required."
                        )
                        st.success(f"Alert sent for {city}!")
    else:
        st.success("✅ No significant drought concerns at this time")
    
    # Drought mitigation strategies
    with st.expander("🌱 Drought Mitigation Strategies"):
        st.write("""
        **Short-term Strategies:**
        - Mulching to reduce evaporation
        - Drip irrigation systems
        - Rainwater harvesting
        - Crop rotation with drought-resistant varieties
        
        **Long-term Strategies:**
        - Soil conservation practices
        - Water storage infrastructure
        - Early warning system utilization
        - Diversified cropping systems
        
        **Community Actions:**
        - Form water user associations
        - Share water resources
        - Collective early warning response
        - Agricultural extension training
        """)