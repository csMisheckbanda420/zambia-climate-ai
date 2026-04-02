import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "data/alerts.db"

class AlertManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for alerts"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                alert_type TEXT,
                severity REAL,
                message TEXT,
                sent_at TIMESTAMP,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_alert(self, city, alert_type, severity, message):
        """Log alert to database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (city, alert_type, severity, message, sent_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (city, alert_type, severity, message, datetime.now(), 'sent'))
        
        conn.commit()
        conn.close()
        
    def get_alerts(self, city=None, days=7):
        """Get recent alerts"""
        conn = sqlite3.connect(DB_PATH)
        
        query = '''
            SELECT city, alert_type, severity, message, sent_at, status
            FROM alerts
            WHERE sent_at > datetime('now', '-{} days')
        '''.format(days)
        
        if city:
            query += f" AND city = '{city}'"
        
        query += " ORDER BY sent_at DESC"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def send_alert(self, city, alert_type, severity, message):
        """Send alert (simulated)"""
        print(f"🚨 ALERT: {city} - {alert_type} (Severity: {severity:.1%})")
        print(f"   Message: {message}")
        self.log_alert(city, alert_type, severity, message)
        return True

_alert_manager = None

def get_alert_manager():
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager