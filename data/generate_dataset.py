import csv
import math
import random
from datetime import datetime, timedelta

def generate_dataset(output_path="sensor_data.csv", duration_hours=24, interval_seconds=5):
    """Generate synthetic IoT sensor data with injected anomalies."""
    
    devices = [
        "line-1/compressor-01", "line-1/motor-02", "line-1/pump-03",
        "line-2/compressor-01", "line-2/motor-02", "line-2/pump-03",
        "line-3/compressor-01", "line-3/motor-02", "line-3/pump-03",
    ]
    
    normals = {
        "temperature": (75.0, 3.0),    
        "pressure": (31.5, 1.0),
        "vibration": (1.5, 0.4),
        "humidity": (40.0, 3.0),
        "power_consumption": (20.0, 2.0),
    }
        
    start_time = datetime(2026, 2, 11, 0, 0, 0)
    rows = []
    
    for device in devices:
        t = start_time
        while t < start_time + timedelta(hours=duration_hours):
            hour = (t - start_time).total_seconds() / 3600
            
            daily_cycle = math.sin(2 * math.pi * hour / 24) * 2  
            
            temp = random.gauss(normals["temperature"][0] + daily_cycle, normals["temperature"][1])
            pres = random.gauss(normals["pressure"][0], normals["pressure"][1])
            vib = abs(random.gauss(normals["vibration"][0], normals["vibration"][1]))
            hum = random.gauss(normals["humidity"][0], normals["humidity"][1])
            power = abs(random.gauss(normals["power_consumption"][0], normals["power_consumption"][1]))
            
            is_anomaly = 0
            anomaly_type = ""
            
            rows.append({
                "timestamp": t.isoformat() + "Z",
                "device_id": device,
                "temperature": round(temp, 2),
                "pressure": round(pres, 2),
                "vibration": round(vib, 3),
                "humidity": round(hum, 1),
                "power_consumption": round(power, 2),
                "is_anomaly": is_anomaly,
                "anomaly_type": anomaly_type,
            })
            
            t += timedelta(seconds=interval_seconds)
    
    rows.sort(key=lambda r: (r["timestamp"], r["device_id"]))
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated {len(rows)} rows to {output_path}")

if __name__ == "__main__":
    generate_dataset()