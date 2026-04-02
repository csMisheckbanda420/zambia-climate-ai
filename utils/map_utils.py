import folium
from folium import plugins

def create_zambia_base_map():
    """Create base map of Zambia"""
    zambia_center = [-13.1339, 27.8493]
    m = folium.Map(
        location=zambia_center, 
        zoom_start=6, 
        tiles='CartoDB positron',
        control_scale=True
    )
    return m

def add_city_markers(map_obj, cities_data, risk_levels, risk_type='flood'):
    """Add city markers with risk-based coloring"""
    for city_info in cities_data:
        city = city_info['city']
        risk = risk_levels.get(city, 0)
        
        if risk > 0.7:
            color = 'red'
            icon = 'exclamation-triangle'
            status = 'HIGH RISK'
        elif risk > 0.4:
            color = 'orange'
            icon = 'exclamation'
            status = 'MODERATE RISK'
        else:
            color = 'green'
            icon = 'check'
            status = 'LOW RISK'
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif;">
            <b style="font-size: 14px;">{city}</b><br>
            <b>{risk_type.title()} Risk:</b> {risk:.1%}<br>
            <b>Status:</b> <span style="color: {color};">{status}</span>
        </div>
        """
        
        folium.Marker(
            location=[city_info['lat'], city_info['lon']],
            popup=folium.Popup(popup_html, max_width=200),
            icon=folium.Icon(color=color, icon=icon, prefix='fa'),
            tooltip=f"{city}: {risk:.1%} risk"
        ).add_to(map_obj)
    
    return map_obj

def create_risk_map(cities_data, risk_levels, map_type='flood'):
    """Create a complete risk map"""
    m = create_zambia_base_map()
    
    # Add title
    title_html = f'''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                    background-color: white; padding: 8px 16px; border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000;">
            <h4 style="margin: 0;">🌍 Zambia {map_type.title()} Risk Assessment</h4>
        </div>
        '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add markers
    m = add_city_markers(m, cities_data, risk_levels, map_type)
    
    # Add legend
    legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; background-color: white;
                    padding: 8px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    z-index: 1000; font-size: 11px;">
            <b>Risk Levels</b><br>
            <span style="color: red;">●</span> High Risk (&gt;70%)<br>
            <span style="color: orange;">●</span> Moderate Risk (40-70%)<br>
            <span style="color: green;">●</span> Low Risk (&lt;40%)
        </div>
        '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m