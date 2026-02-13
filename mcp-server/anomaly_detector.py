from collections import defaultdict, deque
import json
import time
import paho.mqtt.client as mqtt
from db import get_connection, DB_PATH


class AnomalyDetector:

    WINDOW_SIZE = 60   # readings per device per metric
    Z_THRESHOLD = 3.0

    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id="aegisflow-detector")

        self.windows = defaultdict(lambda: defaultdict(lambda: deque(maxlen=self.WINDOW_SIZE)))

        self.active_anomalies = {}

        self.on_anomaly_detected = None

        self.latest_readings = {}

        self._read_counter = defaultdict(int)

    def start(self, retries: int = 10, delay: float = 3.0):
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        for attempt in range(1, retries + 1):
            try:
                self.client.connect(self.broker_host, self.broker_port)
                break
            except ConnectionRefusedError:
                if attempt == retries:
                    raise
                print(f"⏳ Detector: MQTT broker not ready, retrying in {delay}s ({attempt}/{retries})...")
                time.sleep(delay)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe("aegisflow/sensors/#")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            device_id = data["device_id"]

            self.latest_readings[device_id] = data

            self._read_counter[device_id] += 1
            if self._read_counter[device_id] % 5 == 0:
                self._store_reading(data)

            metrics = ["temperature", "pressure", "vibration", "humidity", "power_consumption"]
            anomalous_metrics = []

            for metric in metrics:
                value = data.get(metric)
                if value is None:
                    continue

                window = self.windows[device_id][metric]

                if len(window) >= 20:
                    mean = sum(window) / len(window)
                    std = (sum((x - mean) ** 2 for x in window) / len(window)) ** 0.5

                    if std > 0:
                        z_score = abs(value - mean) / std
                        if z_score > self.Z_THRESHOLD:
                            anomalous_metrics.append({
                                "metric":  metric,
                                "value":   value,
                                "mean":    round(mean, 2),
                                "std":     round(std, 2),
                                "z_score": round(z_score, 2),
                            })

                window.append(value)

            if anomalous_metrics and device_id not in self.active_anomalies:
                severity = self._classify_severity(anomalous_metrics)
                anomaly_info = {
                    "detected_at":      data["timestamp"],
                    "device_id":        device_id,
                    "severity":         severity,
                    "anomalous_metrics": anomalous_metrics,
                    "sensor_values":    data,
                }
                self.active_anomalies[device_id] = anomaly_info
                self._store_anomaly(anomaly_info)

                if self.on_anomaly_detected:
                    self.on_anomaly_detected(anomaly_info)

        except Exception as e:
            print(f"Error processing message: {e}")

    def _classify_severity(self, anomalous_metrics):
        max_z = max(m["z_score"] for m in anomalous_metrics)
        num_metrics = len(anomalous_metrics)

        if max_z > 5 or num_metrics >= 3:
            return "critical"
        elif max_z > 4 or num_metrics >= 2:
            return "high"
        elif max_z > 3.5:
            return "medium"
        else:
            return "low"

    def _store_reading(self, data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_readings
                (timestamp, device_id, temperature, pressure, vibration, humidity, power_consumption)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["timestamp"], data["device_id"],
            data["temperature"], data["pressure"], data["vibration"],
            data["humidity"], data["power_consumption"],
        ))
        conn.commit()
        conn.close()

    def _store_anomaly(self, info):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anomalies (detected_at, device_id, severity, description, sensor_values)
            VALUES (?, ?, ?, ?, ?)
        """, (
            info["detected_at"], info["device_id"], info["severity"],
            json.dumps(info["anomalous_metrics"]),
            json.dumps(info["sensor_values"]),
        ))
        conn.commit()
        conn.close()

    def clear_anomaly(self, device_id):
        """Clear active anomaly for a device after resolution."""
        self.active_anomalies.pop(device_id, None)

    def get_recent_readings(self, device_id, limit=50):
        """Fetch recent stored readings for a device from SQLite."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, temperature, pressure, vibration, humidity, power_consumption
            FROM sensor_readings
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (device_id, limit))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
