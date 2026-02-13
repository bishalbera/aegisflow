# AegisFlow Plant Equipment Manual
**Version 3.2 | Revision Date: 2026-01-15**
**Facility: Smart Manufacturing Complex — Lines 1, 2, 3**

---

## 1. Equipment Overview

This manual covers the three primary equipment categories deployed across production lines 1, 2, and 3 of the AegisFlow Smart Manufacturing Complex. Each production line contains one compressor, one electric motor, and one industrial pump operating in series.

### 1.1 Industrial Compressors (Models: C-100, C-200)

Industrial compressors are responsible for maintaining pneumatic pressure throughout the production line. They operate continuously at rated load and are critical to overall line throughput.

**Normal Operating Parameters:**
- Operating temperature: 65–85°C (sustained; alarm threshold 90°C)
- Discharge pressure: 28–35 PSI (nominal 31.5 PSI)
- Vibration level: 0.5–2.5 mm/s RMS
- Relative humidity at intake: 25–55%
- Power consumption: 18–25 kW at full load

**Design Limits (Do Not Exceed):**
- Maximum temperature: 105°C (auto-shutdown)
- Maximum pressure: 42 PSI (relief valve activation)
- Maximum vibration: 6.0 mm/s RMS (structural damage risk)

**Maintenance Interval:** Every 2,000 operating hours or 3 months, whichever comes first.
**Coolant system flush:** Every 4,000 hours.
**Bearing replacement:** Every 8,000 hours or at first sign of vibration increase.

### 1.2 Electric Motors (Models: M-300, M-400)

Electric motors drive the compressor and pump shafts via direct coupling. Motor health is indicated primarily by vibration signature and thermal profile.

**Normal Operating Parameters:**
- Operating temperature: 60–80°C (winding temperature)
- Vibration level: 0.3–2.0 mm/s RMS
- Power consumption: 15–25 kW (load-dependent)
- Ambient humidity: 20–60%

**Design Limits:**
- Maximum winding temperature: 95°C (Class F insulation)
- Maximum vibration: 5.0 mm/s RMS (ISO 10816 Zone C/D boundary)
- Insulation resistance: Minimum 1 MΩ at 500 VDC

**Maintenance Interval:** Every 4,000 operating hours.
**Lubrication (grease):** Every 1,000 hours for frame sizes M-300; every 2,000 hours for M-400.
**Electrical inspection:** Annually or following any electrical fault event.

### 1.3 Industrial Pumps (Models: P-500, P-600)

Centrifugal pumps circulate process fluid through the production line. Pump integrity is monitored via inlet/outlet pressure differential and power draw.

**Normal Operating Parameters:**
- Inlet pressure: 28–35 PSI
- Pressure differential (inlet to outlet): 8–12 PSI nominal
- Vibration level: 0.5–2.5 mm/s RMS
- Operating temperature (fluid): 50–80°C
- Flow rate: ±5% of rated capacity

**Design Limits:**
- Minimum inlet pressure: 18 PSI (cavitation risk below this level)
- Maximum temperature: 95°C
- Maximum vibration: 5.0 mm/s RMS

**Maintenance Interval:** Every 2,500 operating hours.
**Seal inspection:** Every 1,500 hours or at first sign of leakage.
**Impeller inspection:** Every 5,000 hours.

---

## 2. Anomaly Response Procedures

When the monitoring system detects a sensor deviation, follow the appropriate protocol below. Severity levels are defined by the Escalation Matrix in Section 4.

### 2.1 Thermal Runaway Protocol

**Trigger Conditions:**
- Temperature exceeds 90°C (WARNING) or 95°C (CRITICAL)
- Rate of temperature increase greater than 2°C per minute sustained for 3+ minutes
- Combined: temperature above 80°C AND vibration above 3.0 mm/s (correlated failure pattern)

**Severity:** CRITICAL

**Immediate Actions (in order):**
1. **Reduce load by 50%** using the `reduce_load` command with `{"reduction_pct": 50}`. This is the first-line response per SOP-THERM-01.
2. Monitor temperature trend for 5 minutes. If temperature continues rising above 100°C, proceed to step 3.
3. **Execute emergency shutdown** (`emergency_shutdown` command). Log the time and temperature at shutdown.
4. Notify maintenance team and plant manager immediately.
5. **Do NOT restart** the equipment until root cause is identified and documented.
6. Inspect coolant system: check coolant level, pump flow rate, and heat exchanger condition.
7. Inspect bearings for signs of seizure (discoloration, unusual resistance).

**Common Root Causes:**
- Coolant system failure (blocked lines, failed coolant pump, low coolant level)
- Bearing seizure causing friction heat
- Overloading beyond rated capacity (check production schedule)
- Blocked air intake or discharge causing recirculation heating
- Fouled heat exchanger reducing thermal transfer efficiency

**Recovery Criteria:** Temperature stable below 80°C for 15 consecutive minutes before restart attempt.

---

### 2.2 Pressure Leak Protocol

**Trigger Conditions:**
- Inlet pressure drops below 22 PSI (WARNING) or 18 PSI (CRITICAL)
- Pressure drop exceeding 25% from running average within 5 minutes
- Sustained low pressure (below 20 PSI) for more than 2 minutes

**Severity:** HIGH

**Immediate Actions (in order):**
1. **Enable maintenance mode** (`enable_maintenance_mode`) to safely reduce flow demand on the line.
2. Cross-reference adjacent devices on the same line: if line pressure is normal upstream and anomalous at this pump, the leak is likely at the pump seals or downstream piping.
3. Check power consumption: a leaking pump often shows elevated power draw as it compensates for reduced backpressure.
4. If pressure continues falling below 15 PSI, **execute emergency shutdown** to prevent cavitation damage.
5. Physically inspect accessible piping joints, flange gaskets, and valve stems for visible leakage.
6. Check pump inlet strainer for blockage (can cause false pressure drop reading).

**Common Root Causes:**
- Mechanical seal degradation (most common after 1,500+ operating hours)
- Pipe joint failure at flanged connections
- Valve malfunction (partially closed or stuck open)
- Strainer blockage causing inlet starvation
- Cavitation erosion of pump internals

**Recovery Criteria:** Pressure stable at 28–35 PSI range for 10 consecutive minutes following maintenance intervention.

---

### 2.3 Bearing Failure Protocol

**Trigger Conditions:**
- Vibration exceeds 3.5 mm/s RMS (WARNING) or 5.0 mm/s RMS (CRITICAL)
- Vibration sustained above threshold for more than 2 minutes
- Vibration above 3.0 mm/s combined with temperature rise of 5°C above baseline

**Severity:** HIGH (above 5 mm/s) → CRITICAL (above 8 mm/s)

**Immediate Actions (in order):**
1. **Reduce motor speed by 30%** using `reduce_load` with `{"reduction_pct": 30}`. This reduces mechanical stress on failing bearings.
2. Monitor vibration trend: if vibration is stabilizing (not increasing), continue monitoring for 10 minutes.
3. If vibration exceeds 8 mm/s RMS at any point, **execute emergency shutdown immediately**. Catastrophic bearing failure can cause shaft damage, seal failure, and secondary damage to coupled equipment.
4. Schedule bearing inspection within 4 hours of initial detection.
5. Do not attempt restart until bearing inspection is complete.

**Common Root Causes:**
- Normal bearing wear (expected near end of maintenance interval)
- Inadequate lubrication (check grease interval compliance)
- Shaft misalignment (check coupling alignment)
- Contamination of lubricant (water ingress, particulates)
- Electrical fluting from VFD operation (check shaft grounding)
- Overloading causing fatigue failure

**Recovery Criteria:** Following bearing replacement, vibration below 2.0 mm/s at rated speed for 30 minutes of run-in period.

---

### 2.4 Sensor Drift Protocol

**Trigger Conditions:**
- All readings for a single device drift more than 10% above or below established baseline over a period exceeding 30 minutes
- Gradual, correlated increase across all sensor types (temperature, pressure, vibration, power) without sudden step change
- Readings inconsistent with adjacent devices operating under similar conditions

**Severity:** MEDIUM

**Immediate Actions (in order):**
1. **Do NOT take corrective equipment action** based on potentially drifted sensor readings. Acting on false data can cause unnecessary downtime or damage.
2. Cross-reference with adjacent device readings on the same production line. If adjacent devices show normal readings, the originating device's sensors are suspect.
3. **Acknowledge the anomaly** with a note indicating suspected sensor calibration drift.
4. Flag the device for sensor recalibration by the instrumentation team within the next maintenance window (within 8 hours for MEDIUM severity).
5. Continue monitoring at increased frequency. If any sensor shows a sudden step-change (not gradual drift), re-evaluate — this may indicate a real equipment event.

**Sensor Recalibration Procedure:**
- Temperature sensors: Compare against calibrated reference thermometer at known temperature point. Acceptable drift: ±2°C.
- Pressure sensors: Zero-point and span calibration using dead-weight tester. Acceptable drift: ±0.5 PSI.
- Vibration sensors: Perform calibration shaker test per ISO 16063-21. Acceptable drift: ±5% of reading.

**Common Root Causes:**
- Normal sensor aging and drift (expected after 2+ years of service)
- Connector corrosion or loose wiring causing signal offset
- Environmental contamination affecting sensor element
- Electronic drift in signal conditioning circuitry

---

### 2.5 Electrical Fault Protocol

**Trigger Conditions:**
- Power consumption oscillating more than 50% above and below normal operating level
- Power consumption exceeding 35 kW or dropping below 8 kW for more than 30 seconds
- Rapid cycling of power readings (oscillation frequency above 1 Hz)

**Severity:** CRITICAL

**Immediate Actions (in order):**
1. **Execute emergency shutdown immediately** (`emergency_shutdown`). Electrical faults carry risk of fire, arc flash, or equipment destruction. Do not delay.
2. Isolate the electrical circuit at the upstream disconnect switch (physical action required by maintenance personnel).
3. **Do NOT attempt restart** until a qualified electrician has inspected the equipment and circuit.
4. Notify plant manager and safety officer immediately.
5. Check for signs of overheating, burning smell, or discoloration at motor terminal box and VFD output.

**Common Root Causes:**
- Variable Frequency Drive (VFD) failure or instability
- Motor winding fault (turn-to-turn short, phase-to-ground fault)
- Wiring fault in motor leads or terminal connections
- Power supply instability (utility voltage fluctuations)
- Capacitor failure in power factor correction bank

**Recovery Criteria:** Electrical inspection certificate issued by qualified electrician before restart is authorized.

---

## 3. Emergency Shutdown Procedures

### 3.1 Automated Emergency Shutdown (via `emergency_shutdown` command)

When the AI agent executes an `emergency_shutdown` command:
1. The command is published to the device's MQTT command topic.
2. The device PLC receives the command and initiates controlled shutdown sequence.
3. Load is reduced to zero over 10 seconds (controlled ramp-down to prevent mechanical shock).
4. Main power contactor opens, de-energizing the motor.
5. Shutdown event is logged to the SCADA historian.
6. Status changes to SHUTDOWN on the monitoring dashboard.

### 3.2 Post-Shutdown Safety Checks

Before any restart attempt following an emergency shutdown:

1. **Visual inspection** — Walk-down of equipment for visible damage, fluid leaks, burning, or unusual odors.
2. **Temperature check** — Verify equipment surface temperature has returned to within 15°C of ambient before restart.
3. **Electrical check** — Measure insulation resistance (minimum 1 MΩ) and verify no fault codes on VFD or motor protection relay.
4. **Mechanical check** — Rotate shaft by hand (for accessible equipment) to verify no binding or unusual resistance.
5. **Documentation** — Complete the Post-Shutdown Checklist (Form PSC-001) and obtain supervisor sign-off.
6. **Restart authorization** — Supervisor or plant manager must authorize restart in the SCADA system.

### 3.3 Controlled Shutdown Sequence (Non-Emergency)

For planned maintenance or `enable_maintenance_mode`:
1. Reduce load to 20% over 5 minutes.
2. Allow 5-minute cool-down period at 20% load.
3. Complete shutdown.
4. Lock out / tag out (LOTO) per safety procedure SP-002.

---

## 4. Escalation Matrix

| Severity | Response Time | Primary Notification | Secondary Notification | Authority to Execute Action |
|----------|--------------|---------------------|----------------------|---------------------------|
| Low      | Within 4 hours | Maintenance log only | — | AI Agent (autonomous) |
| Medium   | Within 1 hour | Shift Supervisor | Maintenance team | AI Agent (autonomous, with log) |
| High     | Within 15 minutes | Plant Manager | Maintenance Supervisor | Operator approval required |
| Critical | Immediate (< 5 min) | Plant Manager + Safety Officer | Department Manager | Operator approval required |

**Notification Contacts:**
- Shift Supervisor: Ext. 2100 / Radio Channel 3
- Plant Manager: Ext. 2001 / Mobile: on-call schedule
- Maintenance Supervisor: Ext. 2200
- Safety Officer: Ext. 2050 / Emergency: Site Safety Line

**Escalation Trigger:** If a HIGH or CRITICAL anomaly is not acknowledged within the response time above, the system automatically escalates to the next notification level.

---

## 5. Preventive Maintenance Schedule

### 5.1 Daily Checks (Operator Walkdown)
- Visual inspection of all equipment for leaks, unusual sounds, or odors
- Verify all sensor readings are within normal operating range
- Check fluid levels (coolant, lubrication)
- Inspect all connection points for signs of vibration-induced loosening

### 5.2 Weekly Maintenance
- Clean air intake filters on all compressors
- Check belt tensions (where applicable) on M-300 series motors
- Lubricate sliding components per equipment-specific lube chart
- Test alarm and shutdown setpoints (rotating schedule, 1 device per week)

### 5.3 Monthly Maintenance
| Equipment | Task | Interval |
|-----------|------|----------|
| Compressors C-100/C-200 | Oil sample analysis | Monthly |
| Compressors C-100/C-200 | Air/oil separator element inspection | Every 500 hrs |
| Motors M-300/M-400 | Electrical connections retorque | Monthly |
| Motors M-300/M-400 | Bearing temperature measurement (infrared) | Monthly |
| Pumps P-500/P-600 | Seal flush inspection | Monthly |
| Pumps P-500/P-600 | Coupling alignment check | Every 1,000 hrs |
| All equipment | Sensor calibration verification | Quarterly |

### 5.4 Annual Overhaul
- Complete disassembly and inspection of all bearings
- Replace all seals and gaskets as preventive measure
- Rewind inspection for all motors (megger testing)
- Ultrasonic leak testing of all piping
- Full instrumentation calibration

---

## 6. Troubleshooting Guide

### 6.1 Compressor Troubleshooting

| Symptom | Likely Cause | First Action |
|---------|-------------|--------------|
| High discharge temperature | Low coolant flow, fouled heat exchanger | Check coolant level and pump operation |
| Pressure oscillation | Inlet valve flutter, partially blocked filter | Inspect inlet filter and valve |
| High vibration | Loose mounting bolts, worn bearings | Retorque mounting bolts; schedule bearing inspection |
| Excess power draw | Worn compression elements, air leak in system | Perform system leak test |
| Oil carry-over in discharge | Failed oil separator | Replace air/oil separator element |

### 6.2 Motor Troubleshooting

| Symptom | Likely Cause | First Action |
|---------|-------------|--------------|
| High winding temperature | Overloading, cooling fan failure, high ambient temp | Reduce load; check cooling airflow |
| High vibration | Bearing wear, rotor imbalance, misalignment | Check alignment first; then bearing condition |
| Low insulation resistance | Moisture ingress, winding deterioration | Perform megger test; dry out windings if recent moisture |
| Tripping on overcurrent | Mechanical overload, phase imbalance | Check driven load and incoming power quality |
| Bearing noise (rumbling/squealing) | Inadequate lubrication, contamination | Regrease bearings; if noise persists, replace |

### 6.3 Pump Troubleshooting

| Symptom | Likely Cause | First Action |
|---------|-------------|--------------|
| Low flow / low pressure | Air lock, worn impeller, closed valve | Vent pump casing; check suction valve position |
| Mechanical seal leakage | Seal wear, seal face damage | Inspect seal faces; replace seal assembly |
| Cavitation noise | Insufficient inlet pressure, high fluid temperature | Check NPSH available vs. required; reduce speed |
| Excess power | Impeller wear causing recirculation | Measure differential pressure; inspect impeller |
| Overheating | Running dry, blocked discharge | Verify fluid supply; open discharge valve |

---

## 7. Safety Protocols

### 7.1 General Safety Rules
1. Never defeat safety interlocks or bypasses without written authorization from Safety Officer.
2. All work on energized equipment requires two-person rule.
3. Lockout/Tagout (LOTO) is mandatory for any mechanical work — no exceptions.
4. Personal Protective Equipment (PPE) minimum for equipment area: safety glasses, hearing protection, steel-toed footwear.
5. For work near high-temperature surfaces (>60°C): add heat-resistant gloves and face shield.
6. For electrical work: arc flash PPE per NFPA 70E incident energy analysis.

### 7.2 AI Agent Action Constraints
The AI monitoring agent (AegisFlow) operates within the following safety boundaries:
- **Autonomous actions:** Low and Medium severity anomalies may be acknowledged or logged without operator confirmation.
- **Operator-approved actions:** All HIGH and CRITICAL severity commands (including `emergency_shutdown`, `reduce_load` for load reduction > 30%) require explicit human operator approval before execution.
- **Prohibited autonomous actions:** No AI agent may autonomously restart equipment following an emergency shutdown. Restart authorization is exclusively a human responsibility.
- **Uncertainty protocol:** When root cause is ambiguous or sensor readings are potentially drifted, the agent must default to acknowledgment with monitoring rather than corrective action.

### 7.3 Emergency Contact and Evacuation
- In the event of fire, explosion risk, or uncontrolled chemical release: activate plant evacuation alarm (pull station at each line exit).
- Emergency Assembly Point: Parking Lot B, east gate.
- Emergency Services: Dial 911 first; then notify Plant Security (Ext. 2999).
- Process Safety Coordinator: Available 24/7 on emergency pager.
