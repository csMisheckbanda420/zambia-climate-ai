#!/bin/bash
# setup.sh - Render deployment setup script

echo "🚀 Setting up Zambia Climate Early Warning System on Render..."

# Create necessary directories
mkdir -p data models evaluation .streamlit

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate dataset
echo "📊 Generating climate dataset..."
python generate_dataset.py

# Create alert database
echo "🗄️ Initializing alert database..."
python -c "
from utils.alert_manager import get_alert_manager
get_alert_manager()
"

echo "✅ Setup complete! Starting application..."