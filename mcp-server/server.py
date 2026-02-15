import json
import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from db import init_db, get_connection
from anomaly_detector import AnomalyDetector
from mqtt_simulator import MQTTSimulator
from rag import DeviceManualRetriever

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "data")
_CSV_PATH = os.path.join(_DATA_DIR, "sensor_data.csv")
_MANUAL_PATH = os.path.join(_DATA_DIR, "device_manual.md")

init_db()
retriever = DeviceManualRetriever(_MANUAL_PATH)

_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
_SPEED = float(os.getenv("SPEED_MULTIPLIER", "100"))

simulator = MQTTSimulator(_CSV_PATH, broker_host=_BROKER_HOST,
                          broker_port=_BROKER_PORT, speed_multiplier=_SPEED)
detector = AnomalyDetector(broker_host=_BROKER_HOST, broker_port=_BROKER_PORT)

anomaly_queue: list[dict] = []


def on_anomaly(info: dict):
    anomaly_queue.append(info)
    print(f"ANOMALY DETECTED: {info['device_id']} — {info['severity'].upper()}")


detector.on_anomaly_detected = on_anomaly

simulator.start()
detector.start()

mcp = FastMCP("aegisflow")


@mcp.tool()
def get_sensor_stream(device_id: str = "all", limit: int = 20) -> list[dict]:
    """Get the most recent sensor readings from the IoT stream.

    Use device_id='all' to get the latest reading from every device, or specify
    a device like 'line-1/compressor-01' to get its recent history.
    Returns readings sorted by timestamp (newest first when using a specific device).
    """
    if device_id == "all":
        return list(detector.latest_readings.values())
    return detector.get_recent_readings(device_id, limit)


@mcp.tool()
def get_device_status(device_id: str) -> dict:
    """Get the current status of a specific device.

    Returns the latest sensor readings and whether the device has an active anomaly alert.
    Use this to check on a specific piece of equipment before or after taking action.

    Args:
        device_id: Device identifier, e.g. 'line-1/compressor-01'
    """
    latest = detector.latest_readings.get(device_id)
    active_anomaly = detector.active_anomalies.get(device_id)
    return {
        "device_id":      device_id,
        "status":         "anomaly_active" if active_anomaly else "normal",
        "latest_readings": latest,
        "active_anomaly": active_anomaly,
    }


@mcp.tool()
def get_active_anomalies() -> list[dict]:
    """Get all currently active anomaly alerts across the entire plant.

    Returns anomalies that have been statistically detected but not yet resolved.
    Each entry includes device_id, severity, anomalous metrics with Z-scores,
    and the sensor values at detection time.
    Poll this regularly to monitor plant health.
    """
    return list(detector.active_anomalies.values())


@mcp.tool()
def get_anomaly_history(device_id: str = "all", limit: int = 20) -> list[dict]:
    """Get historical anomaly records from the database.

    Use this to check past incidents for a device, identify recurring patterns,
    and inform root cause analysis. Shows resolved and pending anomalies.

    Args:
        device_id: Filter by device, or 'all' for every device
        limit: Maximum number of records to return (default 20)
    """
    conn = get_connection()
    cursor = conn.cursor()
    if device_id == "all":
        cursor.execute(
            "SELECT * FROM anomalies ORDER BY detected_at DESC LIMIT ?", (limit,)
        )
    else:
        cursor.execute(
            "SELECT * FROM anomalies WHERE device_id = ? ORDER BY detected_at DESC LIMIT ?",
            (device_id, limit),
        )
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results


@mcp.tool()
def query_device_manual(query: str) -> str:
    """Search the equipment manuals and Standard Operating Procedures (SOPs).

    Use this to look up:
    - Normal operating parameters for compressors, motors, and pumps
    - Response protocols for specific anomaly types (thermal runaway, pressure leak, etc.)
    - Emergency shutdown procedures and safety checks
    - Maintenance schedules and inspection intervals
    - Escalation matrix — who to notify and when

    ALWAYS consult this before proposing corrective actions on equipment.

    Args:
        query: Natural language description of what you need, e.g.
               'thermal runaway compressor emergency procedure'
    """
    results = retriever.query(query, k=3)
    return "\n\n---\n\n".join(results)


@mcp.tool()
def get_incident_reports(device_id: str = "all", limit: int = 10) -> list[dict]:
    """Retrieve past incident reports (agent long-term memory).

    Use this to check how similar anomalies were handled previously.
    Incident reports include root cause, action taken, outcome, and lessons learned.
    Reference these when diagnosing new anomalies on the same or similar equipment.

    Args:
        device_id: Filter by device, or 'all' for all devices
        limit: Maximum number of records to return (default 10)
    """
    conn = get_connection()
    cursor = conn.cursor()
    if device_id == "all":
        cursor.execute(
            "SELECT * FROM incident_reports ORDER BY created_at DESC LIMIT ?", (limit,)
        )
    else:
        cursor.execute(
            "SELECT * FROM incident_reports WHERE device_id = ? ORDER BY created_at DESC LIMIT ?",
            (device_id, limit),
        )
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results



@mcp.tool()
def execute_device_command(
    device_id: str,
    command: str,
    parameters: str,
    justification: str,
) -> dict:
    """Execute a command on a physical device. THIS IS A CRITICAL ACTION requiring operator approval.

    Available commands:
    - 'emergency_shutdown'     — Immediately stop the device (use for CRITICAL anomalies)
    - 'reduce_load'            — Decrease operating load; parameters: {"reduction_pct": 20-80}
    - 'restart'                — Power cycle the device after shutdown
    - 'set_parameter'          — Change a specific operating parameter
    - 'enable_maintenance_mode'— Switch device to maintenance mode (safe state)

    Args:
        device_id:     Target device, e.g. 'line-1/compressor-01'
        command:       One of the commands listed above
        parameters:    JSON string of command parameters, e.g. '{"reduction_pct": 50}'
        justification: Detailed explanation of WHY this action is necessary.
                       This text is shown to the human operator for approval.
                       Include: anomaly readings, SOP reference, and expected outcome.
    """
    valid_commands = [
        "emergency_shutdown", "reduce_load", "restart",
        "set_parameter", "enable_maintenance_mode",
    ]
    if command not in valid_commands:
        return {
            "status":  "error",
            "message": f"Invalid command. Must be one of: {valid_commands}",
        }

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE anomalies
        SET proposed_action = ?, action_status = 'executed'
        WHERE device_id = ? AND action_status = 'pending'
        ORDER BY detected_at DESC
        LIMIT 1
        """,
        (f"{command}: {parameters} — {justification}", device_id),
    )
    conn.commit()
    conn.close()

    detector.clear_anomaly(device_id)

    return {
        "status":      "executed",
        "device_id":   device_id,
        "command":     command,
        "parameters":  parameters,
        "message":     f"Command '{command}' executed on {device_id}. Device responding normally.",
        "executed_at": datetime.now().isoformat(),
    }


@mcp.tool()
def acknowledge_anomaly(device_id: str, acknowledged_by: str, notes: str) -> dict:
    """Acknowledge an anomaly alert without taking corrective action.

    Use this when the anomaly is a known condition, a false positive, or when
    the situation requires monitoring rather than immediate intervention.
    This clears the active alert so the device is no longer flagged.

    Args:
        device_id:        The device with the active anomaly
        acknowledged_by:  Who is acknowledging ('operator', 'agent', operator name)
        notes:            Explanation of why no action is needed right now
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE anomalies
        SET action_status = 'acknowledged',
            proposed_action = ?,
            resolved_at = datetime('now')
        WHERE device_id = ? AND action_status = 'pending'
        ORDER BY detected_at DESC
        LIMIT 1
        """,
        (f"Acknowledged by {acknowledged_by}: {notes}", device_id),
    )
    conn.commit()
    conn.close()

    detector.clear_anomaly(device_id)

    return {
        "status":    "acknowledged",
        "device_id": device_id,
        "message":   f"Anomaly for {device_id} acknowledged. Alert cleared.",
    }


@mcp.tool()
def log_incident_report(
    device_id: str,
    summary: str,
    root_cause: str,
    action_taken: str,
    outcome: str,
    lessons_learned: str,
) -> dict:
    """Create an incident report after resolving an anomaly.

    This record becomes part of the agent's long-term memory and will be
    retrieved by get_incident_reports when similar anomalies occur in the future,
    enabling the agent to improve its diagnoses and responses over time.

    ALWAYS create an incident report after resolving a HIGH or CRITICAL anomaly.

    Args:
        device_id:        The device involved
        summary:          Brief description of what happened and how it was resolved
        root_cause:       Determined root cause of the anomaly
        action_taken:     What was done to resolve it (commands executed, etc.)
        outcome:          Result — 'resolved', 'escalated', 'monitoring', 'recurring'
        lessons_learned:  Key takeaways: what to watch for, recommended maintenance, etc.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM anomalies WHERE device_id = ? ORDER BY detected_at DESC LIMIT 1",
        (device_id,),
    )
    row = cursor.fetchone()
    anomaly_id = row[0] if row else None

    cursor.execute(
        """
        INSERT INTO incident_reports
            (anomaly_id, device_id, summary, root_cause, action_taken, outcome, lessons_learned)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (anomaly_id, device_id, summary, root_cause, action_taken, outcome, lessons_learned),
    )
    conn.commit()
    conn.close()

    return {
        "status":    "logged",
        "device_id": device_id,
        "message":   f"Incident report created for {device_id}. Added to agent memory.",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
