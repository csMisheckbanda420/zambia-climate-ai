import pandas as pd
import numpy as np
from datetime import datetime
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Configuration for 10 Zambian cities
cities = {
    "Lusaka": {"lat": -15.3875, "lon": 28.3228, "base_rain": 2.2, "temp_avg": 21, "elevation": 1300},
    "Livingstone": {"lat": -17.8441, "lon": 25.8507, "base_rain": 1.8, "temp_avg": 24, "elevation": 986},
    "Kitwe": {"lat": -12.8091, "lon": 28.2130, "base_rain": 3.5, "temp_avg": 20, "elevation": 1200},
    "Mongu": {"lat": -15.2550, "lon": 23.1290, "base_rain": 2.8, "temp_avg": 23, "elevation": 1025},
    "Mazabuka": {"lat": -15.8500, "lon": 27.7400, "base_rain": 2.1, "temp_avg": 22, "elevation": 1050},
    "Choma": {"lat": -16.8100, "lon": 26.9800, "base_rain": 1.9, "temp_avg": 21, "elevation": 1300},
    "Ndola": {"lat": -12.9700, "lon": 28.6500, "base_rain": 3.4, "temp_avg": 20, "elevation": 1300},
    "Chipata": {"lat": -13.6300, "lon": 32.6400, "base_rain": 2.5, "temp_avg": 22, "elevation": 1150},
    "Kasama": {"lat": -10.2114, "lon": 31.1795, "base_rain": 3.2, "temp_avg": 20, "elevation": 1400},
    "Solwezi": {"lat": -12.1833, "lon": 26.4000, "base_rain": 3.0, "temp_avg": 21, "elevation": 1380}
}

# Generate 30 years of daily data
start_date = datetime(1996, 1, 1)
end_date = datetime(2026, 1, 1)
date_range = pd.date_range(start_date, end_date, freq='D')

data = []
print("Generating 30-year climate dataset for 10 Zambian cities...")
print(f"Total days: {len(date_range)}")
print(f"Total records to generate: {len(date_range) * len(cities):,}")

np.random.seed(42)

for city, coords in cities.items():
    print(f"Processing {city}...")
    for date in date_range:
        month = date.month
        year = date.year
        day_of_year = date.dayofyear
        
        # Rainy season: November to April
        is_rainy_season = 1 if (month >= 11 or month <= 4) else 0
        
        # Generate rainfall
        if is_rainy_season:
            # Base rainfall with gamma distribution
            base_rain = np.random.gamma(2, coords["base_rain"])
            
            # Add seasonal peak
            if month in [12, 1, 2]:
                seasonal_factor = 1.4
            elif month in [11, 3]:
                seasonal_factor = 1.1
            else:
                seasonal_factor = 0.8
                
            rain = base_rain * seasonal_factor
            
            # Extreme event probability (1 in 50 chance)
            if np.random.random() > 0.98:
                rain *= np.random.uniform(5, 12)
        else:
            # Dry season
            if np.random.random() > 0.95:
                rain = np.random.gamma(1, 0.5)
            else:
                rain = 0
        
        # El Niño years (drought)
        if year in [1997, 1998, 2002, 2009, 2015, 2016, 2023, 2024]:
            rain *= 0.6
            temp_mod = 2.0
        # La Niña years (wetter)
        elif year in [1999, 2000, 2007, 2010, 2021, 2022]:
            rain *= 1.3
            temp_mod = -0.8
        else:
            temp_mod = 0
        
        # Temperature calculation
        temp_seasonal = np.sin((day_of_year - 30) / 365 * 2 * np.pi) * 5
        temp_noise = np.random.normal(0, 1)
        temp = coords["temp_avg"] + temp_seasonal + temp_noise + temp_mod
        
        # Soil moisture
        soil_moisture = 30 + (rain * 1.8) - (temp * 0.3)
        soil_moisture = max(0, min(100, soil_moisture))
        
        # River level for flood-prone cities
        if city in ["Mongu", "Mazabuka"]:
            river_level = 2.0 + (rain * 0.05) + (soil_moisture * 0.02)
            river_level = min(12, river_level)
        else:
            river_level = 0
        
        data.append([
            date.strftime('%Y-%m-%d'),
            city,
            coords["lat"],
            coords["lon"],
            coords["elevation"],
            round(rain, 2),
            round(temp, 1),
            round(soil_moisture, 1),
            round(river_level, 1)
        ])

# Create DataFrame
columns = ["Date", "City", "Latitude", "Longitude", "Elevation_m", 
           "Rainfall_mm", "Temp_C", "Soil_Moisture_Pct", "River_Level_m"]
df = pd.DataFrame(data, columns=columns)

# Add derived features
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['DayOfYear'] = df['Date'].dt.dayofyear

# Calculate rolling averages
df = df.sort_values(['City', 'Date'])
df['Rainfall_7d_avg'] = df.groupby('City')['Rainfall_mm'].transform(
    lambda x: x.rolling(window=7, min_periods=1).mean()
)
df['Rainfall_30d_avg'] = df.groupby('City')['Rainfall_mm'].transform(
    lambda x: x.rolling(window=30, min_periods=1).mean()
)
df['Rainfall_90d_avg'] = df.groupby('City')['Rainfall_mm'].transform(
    lambda x: x.rolling(window=90, min_periods=1).mean()
)

# Create event labels
def classify_events(row):
    # Drought: 90-day rainfall < 1mm AND soil moisture < 30%
    if row['Rainfall_90d_avg'] < 1.0 and row['Soil_Moisture_Pct'] < 30:
        drought = 1
    else:
        drought = 0
    
    # Flood: daily rainfall > 50mm OR river level > 8m
    if row['Rainfall_mm'] > 50 or (row['River_Level_m'] > 8):
        flood = 1
    else:
        flood = 0
    
    return drought, flood

drought_labels, flood_labels = zip(*df.apply(classify_events, axis=1))
df['Drought_Event'] = drought_labels
df['Flood_Event'] = flood_labels

# Save to CSV
csv_path = "data/zambia_climate_30yr.csv"
df.to_csv(csv_path, index=False)
print(f"\n✅ Dataset created successfully!")
print(f"📁 Saved to: {csv_path}")
print(f"📊 Total records: {len(df):,}")
print(f"📈 Columns: {len(df.columns)}")
print(f"\n📋 Data Statistics:")
print(f"  - Drought events: {df['Drought_Event'].sum():,}")
print(f"  - Flood events: {df['Flood_Event'].sum():,}")
print(f"  - Avg rainfall: {df['Rainfall_mm'].mean():.2f} mm")
print(f"  - Avg temperature: {df['Temp_C'].mean():.1f}°C")
print(f"  - Avg soil moisture: {df['Soil_Moisture_Pct'].mean():.1f}%")

# Display sample
print(f"\n📋 Sample Data (first 5 rows):")
print(df[['Date', 'City', 'Rainfall_mm', 'Temp_C', 'Soil_Moisture_Pct']].head())