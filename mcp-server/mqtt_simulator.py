import csv
import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt


class MQTTSimulator:
    """Reads sensor_data.csv and publishes rows to MQTT at accelerated speed."""

    def __init__(self, csv_path: str, broker_host: str = "localhost",
                 broker_port: int = 1883, speed_multiplier: float = 100.0):
        """
        Args:
            csv_path: Path to sensor_data.csv
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            speed_multiplier: Replay speed relative to real-time.
                100x means 24 hours of data plays back in ~14.4 minutes.
        """
        self.csv_path = csv_path
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.speed_multiplier = speed_multiplier
        self.client = mqtt.Client(client_id="aegisflow-simulator")
        self.running = False
        self._thread = None

    def start(self, retries: int = 10, delay: float = 3.0):
        """Connect to broker and start publishing in a background daemon thread."""
        for attempt in range(1, retries + 1):
            try:
                self.client.connect(self.broker_host, self.broker_port)
                break
            except ConnectionRefusedError:
                if attempt == retries:
                    raise
                print(f"⏳ MQTT broker not ready, retrying in {delay}s ({attempt}/{retries})...")
                time.sleep(delay)
        self.client.loop_start()
        self.running = True
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def _parse_ts(self, ts_str: str) -> datetime:
        """Parse ISO-8601 timestamp string to datetime (handles trailing Z)."""
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    def _publish_loop(self):
        """
        Read CSV rows sequentially, publish to MQTT, and sleep between rows
        proportional to the real-time gap divided by speed_multiplier.
        Loops back to the start when the file is exhausted (continuous replay).
        """
        while self.running:
            with open(self.csv_path, "r") as f:
                reader = csv.DictReader(f)
                prev_dt = None

                for row in reader:
                    if not self.running:
                        return

                    topic = f"aegisflow/sensors/{row['device_id']}"
                    payload = json.dumps({
                        "timestamp":         row["timestamp"],
                        "device_id":         row["device_id"],
                        "temperature":       float(row["temperature"]),
                        "pressure":          float(row["pressure"]),
                        "vibration":         float(row["vibration"]),
                        "humidity":          float(row["humidity"]),
                        "power_consumption": float(row["power_consumption"]),
                        # NOTE: is_anomaly / anomaly_type deliberately excluded
                    })

                    self.client.publish(topic, payload, qos=0)

                    curr_dt = self._parse_ts(row["timestamp"])
                    if prev_dt is not None:
                        delta_seconds = (curr_dt - prev_dt).total_seconds()
                        if delta_seconds > 0:
                            sleep_time = delta_seconds / self.speed_multiplier
                            time.sleep(sleep_time)

                    prev_dt = curr_dt

