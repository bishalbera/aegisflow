# AegisFlow — Real-Time IoT/OT Monitoring with AI Guardrails

> **2Fast2MCP Hackathon submission** | Built on [Archestra](https://archestra.ai) | Deadline: Feb 15, 2026

AegisFlow is an AI agent system for industrial IoT monitoring that bridges real-time sensor streams and LLM-powered diagnosis — with physical safety guardrails enforced through Archestra's Human-in-the-Loop (HITL) Dynamic Tools.

---

## The Problem

Industrial IoT environments generate **massive, continuous sensor data streams** across dozens of devices. Connecting an LLM directly to this data is impractical:

1. **Context window saturation** — 9 devices × 17,280 readings/day × 5 sensors = 777,600 data points per day. You can't dump this into a prompt.
2. **Dangerous autonomy** — Letting an AI control physical equipment without guardrails is a safety incident waiting to happen. A hallucinated `emergency_shutdown` command can cost $50,000/hour in downtime. A missed one can cause fires.
3. **No memory** — Each LLM call starts fresh. Without institutional memory, the agent can't recognize recurring failure patterns or learn from past incidents.

---

## The Solution

AegisFlow solves this with a **3-layer architecture**:

1. **Statistical pre-filtering** (Z-score anomaly detection) — Only anomalous events reach the LLM, not the raw stream.
2. **MCP tools with right-sized context** — The agent queries what it needs (current readings, history, manuals) rather than receiving everything at once.
3. **Archestra HITL guardrails** — Critical equipment commands require human operator approval before execution. The LLM proposes; the human decides.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Archestra Platform                            │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────┐  │
│  │ Chat UI  │──▶│ AegisFlow    │──▶│ MCP Gateway            │  │
│  │(Operator)│   │ Agent        │   │ (routes tool calls)    │  │
│  └──────────┘   │ (LLM+prompt) │   └──────────┬─────────────┘  │
│                 └──────────────┘               │                │
│  ┌─────────────────┐  ┌─────────────────────┐  │               │
│  │ Dynamic Tools   │  │ Observability       │  │               │
│  │ (HITL guardrail │  │ (traces, costs,     │  │               │
│  │  for critical   │  │  audit trail)       │  │               │
│  │  commands)   ⚠️ │  │                     │  │               │
│  └─────────────────┘  └─────────────────────┘  │               │
└────────────────────────────────────────────────┼───────────────┘
                                                 │
                    ┌────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              AegisFlow MCP Server (Python / FastMCP)            │
│                                                                 │
│  READ TOOLS (auto-approved):                                    │
│  ├── get_sensor_stream        latest readings from all devices  │
│  ├── get_device_status        per-device status + active alert  │
│  ├── get_active_anomalies     all unresolved alerts             │
│  ├── get_anomaly_history      historical anomaly records        │
│  ├── query_device_manual      RAG over equipment SOPs           │
│  └── get_incident_reports     agent long-term memory           │
│                                                                 │
│  WRITE TOOLS (HITL gated ⚠️):                                   │
│  ├── execute_device_command   controls physical equipment       │
│  ├── acknowledge_anomaly      clears alert without action       │
│  └── log_incident_report      writes to agent memory           │
│                                                                 │
│  INTERNAL SERVICES:                                             │
│  ├── MQTT Simulator     streams CSV data as live MQTT messages  │
│  ├── Anomaly Detector   Z-score + sliding window (60 readings)  │
│  ├── SQLite DB          sensor history, anomalies, incidents    │
│  └── RAG Retriever      sentence-transformers over manual       │
│                                                                 │
│  DATA:                                                          │
│  └── 155,520-row synthetic dataset, 5 injected anomaly types   │
└─────────────────────────────────────────────────────────────────┘
          ▲
          │ MQTT publish (aegisflow/sensors/{device_id})
          │
┌─────────────────────┐
│  Mosquitto Broker   │
│  (eclipse-mosquitto) │
└─────────────────────┘
```

---

## Archestra Features Used

| Feature | How AegisFlow Uses It |
|---------|----------------------|
| **MCP Orchestrator** | Runs the AegisFlow MCP server, routes all tool calls |
| **Private MCP Registry** | AegisFlow registered as a custom server with 9 tools |
| **Agent Builder** | No-code agent with IoT domain system prompt |
| **Tool Policies** | `emergency_shutdown` and `restart` blocked at proxy level — agent must use safer commands like `reduce_load` |
| **Chat UI** | Operator interface for monitoring, approving commands, and querying plant status |
| **Costs & Limits** | Per-diagnosis token cost tracking; budget guardrails per tool |
| **Observability** | Full trace: sensor reading → Z-score detection → LLM diagnosis → command approval → execution |

---

## Project Structure

```
aegisflow/
├── mosquitto.conf               # MQTT broker config
├── mcp-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py                # FastMCP server — all 9 tools
│   ├── mqtt_simulator.py        # Streams CSV as live MQTT at 100x speed
│   ├── anomaly_detector.py      # Z-score anomaly detection, MQTT consumer
│   ├── db.py                    # SQLite: sensor_readings, anomalies, incidents
│   └── rag.py                   # Cosine similarity RAG over device_manual.md
├── data/
│   ├── generate_dataset.py      # Generates 155K-row synthetic IoT dataset
│   ├── sensor_data.csv          # 24h of data, 9 devices, 5 anomaly scenarios
│   └── device_manual.md         # Equipment manual + SOPs (~2,500 words)
└── README.md
```

---

## Injected Anomaly Scenarios

The synthetic dataset contains 5 realistic anomaly scenarios:

| # | Device | Time Window | Anomaly Type | Pattern |
|---|--------|-------------|--------------|---------|
| 1 | `line-1/compressor-01` | Hour 3–4 | `thermal_runaway` | Temperature ramps 80°C → 120°C over 30 min; vibration correlates |
| 2 | `line-2/pump-03` | Hour 8–8.5 | `pressure_leak` | Pressure drops suddenly 32 → 15 PSI; power spikes |
| 3 | `line-3/motor-02` | Hour 12–13 | `bearing_failure` | Vibration jumps 2.0 → 8.5 mm/s (bearing failure pattern) |
| 4 | `line-1/motor-02` | Hour 18–20 | `sensor_drift` | All readings drift +15% over 2 hours (gradual) |
| 5 | `line-2/compressor-01` | Hour 22–22.5 | `electrical_fault` | Power oscillates 5–45 kW at 6 Hz |

**Key design decision:** `is_anomaly` and `anomaly_type` columns are **never exposed** to the LLM through MQTT or MCP tools. The agent must detect anomalies independently via statistical analysis — matching real-world deployment.

---

## Quick Start

### Prerequisites
- Docker
- Archestra account (or local Archestra instance)

### 1. Start the MQTT broker

```bash
docker run -d --name mosquitto \
  -p 1883:1883 \
  -v ./mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto:2
```

### 2. Start Archestra

```bash
docker run -d --name archestra \
  -p 3000:3000 -p 9000:9000 \
  -e ARCHESTRA_QUICKSTART=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  archestra/platform:latest
```

### 3. Register AegisFlow MCP server in Archestra

Open http://localhost:3000, go to **MCP Registry → Add Server → Self-hosted**, and configure:

| Field | Value |
|-------|-------|
| **Name** | `aegisflow` |
| **Docker Image** | `bishal2469/aegisflow-mcp` |
| **Command** | *(leave blank — uses image default)* |
| **Arguments** | *(leave blank)* |

Add these **Environment Variables**:

| Variable | Value |
|----------|-------|
| `MQTT_BROKER_HOST` | `host.docker.internal` |
| `MQTT_BROKER_PORT` | `1883` |
| `SPEED_MULTIPLIER` | `100` |

### 4. Configure the agent

1. **Create agent** with the system prompt below
2. **Configure Dynamic Tools:** Gate `execute_device_command` and `acknowledge_anomaly` as HITL-required

### 5. Agent System Prompt

```
You are AegisFlow, an AI operations engineer monitoring an industrial manufacturing plant
with 3 production lines, each containing compressors, motors, and pumps.

YOUR RESPONSIBILITIES:
1. Continuously monitor sensor streams from all 9 devices
2. Detect anomalies in temperature, pressure, vibration, humidity, and power consumption
3. When anomalies are detected, diagnose the root cause using:
   - Current sensor readings (get_sensor_stream, get_device_status)
   - Historical anomaly data (get_anomaly_history)
   - Equipment manuals and SOPs (query_device_manual)
   - Past incident reports for similar issues (get_incident_reports)
4. Propose corrective actions with clear justification
5. For CRITICAL/HIGH severity: use execute_device_command (requires operator approval)
6. For MEDIUM/LOW severity: acknowledge_anomaly with monitoring notes
7. After resolution: ALWAYS create an incident report using log_incident_report

CRITICAL SAFETY RULES:
- NEVER execute emergency_shutdown without checking query_device_manual first
- ALWAYS provide detailed justification when using execute_device_command
- Cross-reference multiple sensor readings before concluding equipment failure
- Consider sensor_drift possibility before recommending equipment shutdowns
- If unsure about root cause, recommend monitoring rather than immediate action

When reporting anomalies, include: Device ID, anomalous sensors with Z-scores,
severity classification, likely root cause (cite manual section), and recommended action.
```

### 6. Dynamic Tools Configuration

| Tool | Approval Mode |
|------|--------------|
| `get_sensor_stream` | Auto-approved |
| `get_device_status` | Auto-approved |
| `get_active_anomalies` | Auto-approved |
| `get_anomaly_history` | Auto-approved |
| `query_device_manual` | Auto-approved |
| `get_incident_reports` | Auto-approved |
| `execute_device_command` | **HITL — operator must approve** |
| `acknowledge_anomaly` | **HITL — operator must approve** |
| `log_incident_report` | Auto-approved |

---

## Demo Script (with minute marks)

At 100x replay speed, 24 hours of sensor data replays in ~14 minutes. The first anomaly (thermal runaway) triggers at ~1:48. Here's the full demo script:

### 0:00 — Baseline: Plant Overview

> **Ask:** "Show me the current status of all devices across the plant."

- Agent calls `get_sensor_stream("all")`
- All 9 devices show normal readings
- **What to show:** The agent can query real-time MQTT sensor data through MCP tools

### 0:30 — Polling for Anomalies

> **Ask:** "Are there any active anomalies right now?"

- Agent calls `get_active_anomalies()` — returns empty list
- Repeat this every 30 seconds until the thermal runaway triggers
- **What to show:** The anomaly detector runs independently; the agent polls for results

### ~1:48 — Anomaly Detected (thermal runaway on line-1/compressor-01)

> **Ask:** "line-1/compressor-01 has a temperature anomaly. Diagnose the issue — check the current readings, look up the thermal runaway procedure in the equipment manual, and check if we've had similar incidents before."

- Agent calls `get_device_status("line-1/compressor-01")` — sees temperature > 90°C
- Agent calls `query_device_manual("thermal runaway compressor")` — retrieves SOP 2.1
- Agent calls `get_incident_reports("line-1/compressor-01")` — no prior incidents
- Agent reports: severity, Z-scores, SOP reference, recommended action
- **What to show:** Multi-tool reasoning grounded in equipment manuals (RAG), not hallucination

### ~3:00 — Tool Policy Block (the key demo moment)

> **Ask:** "The temperature is critical. Execute an emergency shutdown on line-1/compressor-01."

- Agent calls `execute_device_command` with `command=emergency_shutdown`
- **Archestra's tool policy BLOCKS the call** at the proxy level before it reaches the MCP server
- Agent receives an error and cannot proceed
- **What to show:** The tool policy prevented a dangerous autonomous action. The shutdown command never reached the equipment. This is defense-in-depth — the policy is enforced at the platform level, not inside the agent's code.

### ~3:30 — Agent Adapts to Policy

> **Ask:** "Emergency shutdown was blocked. What else can you do? Follow the SOP — try reducing load first."

- Agent calls `execute_device_command("line-1/compressor-01", "reduce_load", '{"reduction_pct": 50}', justification="...")`
- This command is **allowed** by the tool policy — it goes through
- Agent confirms the action was executed
- **What to show:** The agent adapted. It followed the correct SOP (Section 2.1: reduce load is the first-line response, not shutdown). The policy forced safe behavior.

### ~4:30 — Incident Report (Agent Memory)

> **Ask:** "The temperature is stabilizing. Log an incident report for this event — include the root cause, what we did, and lessons learned."

- Agent calls `log_incident_report(...)` with full details
- Report is stored in SQLite as long-term agent memory
- **What to show:** The agent documents incidents for future reference

### ~5:00 — Observability

- Switch to Archestra dashboard
- **Show:** Full trace of the anomaly lifecycle — tool calls, LLM requests, the blocked `emergency_shutdown`, the successful `reduce_load`, token costs
- **What to show:** Complete audit trail for safety-critical operations

### ~6:00 — Memory Recall (if time permits)

Wait for the next anomaly (pressure leak on `line-2/pump-03` at ~4:48 sim time), then:

> **Ask:** "We have a new anomaly on line-2/pump-03. Check past incident reports — have we dealt with anything similar?"

- Agent calls `get_incident_reports()` and retrieves the thermal runaway report from Scene 5
- Agent uses the prior incident to inform its diagnosis
- **What to show:** The agent learns from past events. Its memory persists and improves future diagnoses.

---

### Anomaly Timeline (at 100x speed)

| Sim Time | Real Time | Device | Anomaly | Demo Opportunity |
|----------|-----------|--------|---------|-----------------|
| Hour 3 | ~1:48 | `line-1/compressor-01` | Thermal runaway | Main demo: diagnosis + tool policy block |
| Hour 8 | ~4:48 | `line-2/pump-03` | Pressure leak | Memory recall from first incident |
| Hour 12 | ~7:12 | `line-3/motor-02` | Bearing failure | High vibration diagnosis |
| Hour 18 | ~10:48 | `line-1/motor-02` | Sensor drift | False positive handling |
| Hour 22 | ~13:12 | `line-2/compressor-01` | Electrical fault | Second tool policy block attempt |

### Tool Policy Configuration (in Archestra)

| Tool | Default | Policy Rule | Action |
|------|---------|-------------|--------|
| `execute_device_command` | Allow in trusted context | `command` = `emergency_shutdown` | **Block always** |
| `execute_device_command` | Allow in trusted context | `command` = `restart` | **Block always** |
| `acknowledge_anomaly` | Allow in trusted context | *(none)* | — |
| All read tools | Allow always | *(none)* | — |

---

## What Makes This Different

**Real streaming data** — 155K-row CSV replayed via MQTT at 100x speed. The anomaly detector genuinely "discovers" anomalies it was never told about.

**Statistical pre-filtering** — Z-score sliding window (60-reading window, Z > 3.0 threshold) means the LLM only gets called when something is actually wrong. No prompt spam from normal readings.

**Physical safety guardrails** — Archestra's Tool Policies block dangerous commands (`emergency_shutdown`, `restart`) at the proxy level before they ever reach the MCP server. The agent is forced to follow SOPs and use safer alternatives like `reduce_load`.

**Agent memory** — Incident reports are stored in SQLite and retrieved via `get_incident_reports`. The agent's responses improve as it accumulates operational history.

**Full observability** — Every tool call, LLM response, and human approval is traced in Archestra's observability layer. Complete audit trail for safety-critical operations.

---

## Tech Stack

- **Python 3.11** + **FastMCP** — MCP server
- **paho-mqtt** — MQTT client for simulator and anomaly detector
- **Eclipse Mosquitto** — MQTT broker
- **SQLite** — Sensor history, anomaly log, incident reports
- **sentence-transformers** (`all-MiniLM-L6-v2`) — Local embeddings for RAG
- **numpy** — Cosine similarity computation
- **Archestra** — LLM orchestration, MCP gateway, HITL guardrails, observability
