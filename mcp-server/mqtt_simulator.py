import csv
import json
import time
import threading
import paho.mqtt.client as mqtt



class MQTTSimulator:
    """Reads sensor_data.csv and publishes to MQTT at accelerated speed."""

    def __init__(self, csv_path: str, broker_host: str = "localhost",
                 broker_port: int = 1883, speed_multiplier: float = 100.0):

                 self.csv_path = csv_path
                 self.broker_host = broker_host
                 self.broker_port = broker_port
                 self.speed_multiplier = speed_multiplier
                 self.client = mqtt.Client(client_id="aegisflow-simulator")
                 self.running = False
                 self._thread = None

    def start(self):
            
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()
        self.running = True
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def _publish_loop(self):
          
          with open(self.csv_path, "r") as f:
                reader = csv.DictReader(f)
                prev_ts = None
                for row in reader:
                      if not self.running:
                            break
                      
                      topic = f"aegisflow/sensors/{row['device_id']}"
                      payload = json.dumps({
                            "timestamp": row["timestamp"],
                            "device_id": row["device_id"],
                            "temperature": float(row["temperature"]),
                            "pressure": float(row["pressure"]),
                            "vibration": float(row["vibration"]),
                            "humidity": float(row["humidity"]),
                            "power_consumption": float(row["power_consumption"]),
                      })

                      self.client.publish(topic, payload, qos=0)

                      if prev_ts:
                            pass
                      prev_ts = row["timestamp"]

          if self.running: 
                self._publish_loop()
                