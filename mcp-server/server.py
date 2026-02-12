from mcp.server.fastmcp import FastMCP
import json
import sqlite3
import threading
from datetime import datetime
from db import init_db, get_connection
from mqtt_simulator import MQTTSimulator
from anomaly_detector import AnomalyDetector

init_db()
retriever = DeviceManualRetriever("data/device_manual.md")

simulator = MQTTSimulator("data/sensor_data.csv", broker_host="mosquitto", broker_port=100)
detector = AnomalyDetector(broker_host="mosquitto")

anomaly_queue = []

def on_anomaly(info):
    anomaly_queue.append(info)
    print(f"Anomaly detected: {info['device_id']} - {info['severity']}")

detector.on_anomaly_detected = on_anomaly

simulator.start()
detector.start()

mcp = FastMCP("aegisflow")

@mcp.tool()
def get_sensor_stream(device_id: str = "all", limit: int = 20)-> list[dict]:
    """Get the most reent sensor readings from the IoT stream."""

    if device_id == "all":
        return list(detector.latest_readings.values())
    else:
        return detector.get_recent_readings(device_id, limit)

@mcp.tool()
def get_device_status(device_id:str) -> dict:
    """Get the current status of a specific device including its latest sensor readings"""

    latest = detector.latest_readings.get(device_id)
    active_anomaly = detector.active_anomalies.get(device_id)

    return {
        "device_id": device_id,
        "status": "anomaly_active" if active_anomaly else "normal",
        "latest_readings": latest,
        "active_anomaly": active_anomaly,
    }

@mcp.tool()
def get_active_anomalies() -> list[dict]:
    """Get all currently active anomaly alerts across all devices"""
    return list(detector.active_anomalies.values())

@mcp.tool()
def get_anomaly_history(device_id: str = "all", limit: int = 20) -> list[dict]:
    """Get historical anomaly records from db"""

    conn = get_connection()
    cursor = conn.cursor()
    if device_id == "all":
        cursor.execute("""
            SELECT * FROM anomalies ORDER BY detected_at DESC LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT * FROM anomalies WHERE device_id = ? 
            ORDER BY detected_at DESC LIMIT ?
        """, (device_id, limit))
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results

@mcp.tool()
def query_device_manual(query: str) -> str:
    """Search the equipment manuals and standard operating procedures"""

    results = retriever.query(query, k = 3)
    return "\n\n---\n\n".join(results)

@mcp.tool()
def get_incident_reports(device_id: str = "all", limit: int = 10) -> list[dict]:
    """Retrieve past incident reports"""

    conn = get_connection()
    cursor = conn.cursor()
    if device_id == "all":
        cursor.execute("SELECT * FROM incident_reports ORDER BY created_at DESC LIMIT ?", (limit,))
    else:
        cursor.execute("SELECT * FROM incident_reports WHERE device_id = ? ORDER BY created_at DESC LIMIT ?", (device_id, limit))

    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results

@mcp.tool()
def execute_device_command(device_id: str, command: str, parameters: str, justification: str)-> dict:

    valid_commands = ["emergency_shutdown", "reduce_load", "restart", 
                      "set_parameter", "enable_maintenance_mode"]
    
    if command not in valid_commands:
        return {"success": False, "message": f"Invalid command. Valid commands are: {', '.join(valid_commands)}"}
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE anomalies SET proposed_action = ?, action_status = 'executed'
        WHERE device_id = ? AND action_status = 'pending'
        ORDER BY detected_at DESC LIMIT 1
    """, (f"{command}: {parameters} — {justification}", device_id))

    conn.commit()
    conn.close()

    detector.clear_anomaly(device_id)

    return{
        "status": "executed",
        "device_id": device_id,
        "command": command,
        "parameters": parameters,
        "message": f"Command '{command}' executed on {device_id}. Device responding normally.",
        "executed_at": datetime.now().isoformat()
    }

@mcp.tool()
def acknowledge_anomaly(device_id: str, acknowledged_by: str, notes: str) -> dict:
    """Acknowledge an anomaly alert without taking corrective action"""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE anomalies SET action_status = 'acknowledged', 
               proposed_action = ?, resolved_at = datetime('now')
        WHERE device_id = ? AND action_status = 'pending'
        ORDER BY detected_at DESC LIMIT 1
    """, (f"Acknowledged by {acknowledged_by}: {notes}", device_id))
    conn.commit()
    conn.close()
    
    detector.clear_anomaly(device_id)
    
    return {
        "status": "acknowledged",
        "device_id": device_id,
        "message": f"Anomaly for {device_id} acknowledged. Alert cleared."
    }

@mcp.tool()
def log_incident_report(device_id: str, summary: str, root_cause: str, 
                        action_taken: str, outcome: str, lessons_learned: str) -> dict:
    """Create an incident report after resolving an anomaly.
    This becomes part of the agent's long-term memory and will be 
    referenced when similar anomalies occur in the future.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM anomalies WHERE device_id = ? 
        ORDER BY detected_at DESC LIMIT 1
    """, (device_id,))
    anomaly_row = cursor.fetchone()
    anomaly_id = anomaly_row[0] if anomaly_row else None
    
    cursor.execute("""
        INSERT INTO incident_reports 
        (anomaly_id, device_id, summary, root_cause, action_taken, outcome, lessons_learned)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (anomaly_id, device_id, summary, root_cause, action_taken, outcome, lessons_learned))
    conn.commit()
    conn.close()
    
    return {
        "status": "logged",
        "device_id": device_id,
        "message": f"Incident report created for {device_id}. Added to agent memory."
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")