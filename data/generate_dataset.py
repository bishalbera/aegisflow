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

    anomaly_windows = [
        ("line-1/compressor-01", 3.0,  4.0,  "thermal_runaway"),
        ("line-2/pump-03",       8.0,  8.5,  "pressure_leak"),
        ("line-3/motor-02",      12.0, 13.0, "bearing_failure"),
        ("line-1/motor-02",      18.0, 20.0, "sensor_drift"),
        ("line-2/compressor-01", 22.0, 22.5, "electrical_fault"),
    ]

    start_time = datetime(2026, 2, 11, 0, 0, 0)
    rows = []

    for device in devices:
        t = start_time
        while t < start_time + timedelta(hours=duration_hours):
            hour = (t - start_time).total_seconds() / 3600

            daily_cycle = math.sin(2 * math.pi * hour / 24) * 2

            temp  = random.gauss(normals["temperature"][0] + daily_cycle, normals["temperature"][1])
            pres  = random.gauss(normals["pressure"][0], normals["pressure"][1])
            vib   = abs(random.gauss(normals["vibration"][0], normals["vibration"][1]))
            hum   = random.gauss(normals["humidity"][0], normals["humidity"][1])
            power = abs(random.gauss(normals["power_consumption"][0], normals["power_consumption"][1]))

            is_anomaly = 0
            anomaly_type = ""

            for a_device, a_start, a_end, a_type in anomaly_windows:
                if device != a_device:
                    continue
                if not (a_start <= hour < a_end):
                    continue

                progress = (hour - a_start) / (a_end - a_start)
                is_anomaly = 1
                anomaly_type = a_type

                if a_type == "thermal_runaway":
                    temp_offset = 5 + progress * 45          # +5 → +50 °C
                    vib_offset  = progress * 3.0
                    temp  = random.gauss(normals["temperature"][0] + temp_offset, 1.5)
                    vib   = abs(random.gauss(normals["vibration"][0] + vib_offset, 0.3))

                elif a_type == "pressure_leak":
                    if progress < 0.1:
                        pres = random.gauss(32 - progress * 170, 0.5)  # 32 → ~15
                    else:
                        pres = random.gauss(15.0, 1.0)
                    power_spike = (1 - progress) * 15          # power surge as pump fights leak
                    power = abs(random.gauss(normals["power_consumption"][0] + power_spike, 1.5))

                elif a_type == "bearing_failure":
                    vib_target = 2.0 + progress * 6.5
                    temp_offset = progress * 8
                    vib  = abs(random.gauss(vib_target, 0.5))
                    temp = random.gauss(normals["temperature"][0] + temp_offset, 1.5)

                elif a_type == "sensor_drift":
                    # All readings slowly drift +15% from baseline over 2 hours
                    drift = 1.0 + progress * 0.15
                    temp  = random.gauss(normals["temperature"][0] * drift, normals["temperature"][1])
                    pres  = random.gauss(normals["pressure"][0] * drift, normals["pressure"][1])
                    vib   = abs(random.gauss(normals["vibration"][0] * drift, normals["vibration"][1]))
                    hum   = random.gauss(normals["humidity"][0] * drift, normals["humidity"][1])
                    power = abs(random.gauss(normals["power_consumption"][0] * drift, normals["power_consumption"][1]))

                elif a_type == "electrical_fault":
                    # Use a high-frequency sine to simulate oscillation
                    osc_freq = 6  
                    osc = math.sin(2 * math.pi * osc_freq * (hour - a_start))
                    power = 25.0 + osc * 20.0 + random.gauss(0, 2.0)
                    power = max(2.0, power)

                break  

            rows.append({
                "timestamp":         t.isoformat() + "Z",
                "device_id":         device,
                "temperature":       round(temp, 2),
                "pressure":          round(pres, 2),
                "vibration":         round(vib, 3),
                "humidity":          round(hum, 1),
                "power_consumption": round(power, 2),
                "is_anomaly":        is_anomaly,
                "anomaly_type":      anomaly_type,
            })

            t += timedelta(seconds=interval_seconds)

    rows.sort(key=lambda r: (r["timestamp"], r["device_id"]))

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    anomaly_count = sum(1 for r in rows if r["is_anomaly"])
    print(f"Generated {total} rows ({anomaly_count} anomaly rows) to {output_path}")

    from collections import Counter
    types = Counter(r["anomaly_type"] for r in rows if r["anomaly_type"])
    for atype, count in types.items():
        print(f"  {atype}: {count} rows")


if __name__ == "__main__":
    generate_dataset()
