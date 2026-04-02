import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

DATA_PATH = "data/zambia_climate_30yr.csv"
MODEL_DIR = "models"

class ClimateDataLoader:
    def __init__(self):
        self.df = None
        self.flood_model = None
        self.drought_model = None
        self.scaler = None
        self.load_data()
        self.load_models()
    
    def load_data(self):
        """Load the climate dataset"""
        if os.path.exists(DATA_PATH):
            self.df = pd.read_csv(DATA_PATH)
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            print(f"✅ Data loaded: {len(self.df):,} records")
        else:
            raise FileNotFoundError(f"Data not found at {DATA_PATH}")
    
    def load_models(self):
        """Load trained models if they exist"""
        flood_path = os.path.join(MODEL_DIR, "flood_model.pkl")
        drought_path = os.path.join(MODEL_DIR, "drought_model.pkl")
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
        
        if os.path.exists(flood_path):
            self.flood_model = joblib.load(flood_path)
            print("✅ Flood model loaded")
        else:
            print("⚠️ Flood model not found")
            
        if os.path.exists(drought_path):
            self.drought_model = joblib.load(drought_path)
            print("✅ Drought model loaded")
            
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
    
    def get_city_data(self, city_name):
        """Get historical data for a specific city"""
        city_df = self.df[self.df['City'] == city_name].copy()
        return city_df
    
    def get_all_cities(self):
        """Get list of all cities"""
        return sorted(self.df['City'].unique())
    
    def get_city_coordinates(self, city_name):
        """Get coordinates for a city"""
        city_data = self.df[self.df['City'] == city_name].iloc[0]
        return {
            'lat': city_data['Latitude'],
            'lon': city_data['Longitude'],
            'elevation': city_data['Elevation_m']
        }
    
    def get_current_conditions(self, city_name):
        """Get current conditions for a city"""
        city_data = self.get_city_data(city_name)
        latest = city_data.iloc[-1]
        
        return {
            'rainfall': latest['Rainfall_mm'],
            'temperature': latest['Temp_C'],
            'soil_moisture': latest['Soil_Moisture_Pct'],
            'river_level': latest['River_Level_m'],
            'date': latest['Date']
        }
    
    def predict_risk(self, city_name):
        """Predict flood and drought risk for a city"""
        city_data = self.get_city_data(city_name).tail(90)
        
        if len(city_data) < 30:
            return {
                'flood_risk': 0.5,
                'drought_risk': 0.5,
                'flood_alert': False,
                'drought_alert': False
            }
        
        latest = city_data.iloc[-1]
        
        # Prepare features (simplified for web dashboard)
        if self.flood_model and self.drought_model and self.scaler:
            try:
                # Simple feature set for prediction
                features = np.array([[
                    latest['Rainfall_mm'],
                    latest['Temp_C'],
                    latest['Soil_Moisture_Pct'],
                    latest['Month'],
                    latest.get('Rainfall_30d_avg', latest['Rainfall_mm']),
                    latest.get('Rainfall_90d_avg', latest['Rainfall_mm'])
                ]])
                features_scaled = self.scaler.transform(features)
                flood_prob = self.flood_model.predict_proba(features_scaled)[0][1]
                drought_prob = self.drought_model.predict_proba(features_scaled)[0][1]
            except:
                # Fallback to threshold-based logic
                flood_prob = min(1.0, max(0, (latest['Rainfall_mm'] - 30) / 70))
                drought_prob = min(1.0, max(0, (30 - latest['Soil_Moisture_Pct']) / 30))
        else:
            # Fallback threshold-based logic
            flood_prob = min(1.0, max(0, (latest['Rainfall_mm'] - 30) / 70))
            drought_prob = min(1.0, max(0, (30 - latest['Soil_Moisture_Pct']) / 30))
        
        return {
            'flood_risk': round(float(flood_prob), 3),
            'drought_risk': round(float(drought_prob), 3),
            'flood_alert': flood_prob > 0.7,
            'drought_alert': drought_prob > 0.7
        }
    
    def get_trend_data(self, city_name, days=90):
        """Get trend data for visualization"""
        city_data = self.get_city_data(city_name).tail(days)
        return city_data[['Date', 'Rainfall_mm', 'Temp_C', 'Soil_Moisture_Pct']]

_data_loader = None

def get_data_loader():
    global _data_loader
    if _data_loader is None:
        _data_loader = ClimateDataLoader()
    return _data_loader