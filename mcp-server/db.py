import sqlite3
from datetime import datetime

DB_PATH = "aegisflow.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                temperature REAL,
                pressure REAL,
                vibration REAL,
                humidity REAL,
                power_consumption REAL,
                ingested_at TEXT DEFAULT (datetime('now'))
        )
""" )
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT NOT NULL,
            device_id TEXT NOT NULL,
            severity TEXT NOT NULL,  
            anomaly_type TEXT,       
            description TEXT,
            sensor_values TEXT,     
            diagnosis TEXT,         
            proposed_action TEXT,    
            action_status TEXT DEFAULT 'pending',   
            resolved_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            anomaly_id INTEGER,
            device_id TEXT NOT NULL,
            summary TEXT,          
            root_cause TEXT,
            action_taken TEXT,
            outcome TEXT,          
            lessons_learned TEXT,
            FOREIGN KEY (anomaly_id) REFERENCES anomalies(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON sensor_readings(device_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_device ON anomalies(device_id)")

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)



