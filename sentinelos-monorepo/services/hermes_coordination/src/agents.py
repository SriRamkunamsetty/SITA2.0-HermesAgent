import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger("sentinelos.hermes.agents")


@dataclass
class AgentOutcome:
    agent: str
    status: str
    reasoning: str
    actions_proposed: List[str]
    priority: str


class CoordinationPolicyEngine:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def run_task(self, task_payload: dict) -> Dict[str, object]:
        vehicle = task_payload.get("vehicle", {})
        telemetry = task_payload.get("telemetry", {})
        category = task_payload.get("category", "vehicle_detected")

        actions: List[str] = []
        reasons: List[str] = []
        priority = "LOW"

        license_plate = vehicle.get("license_plate") or ""
        ocr_conf = float(vehicle.get("ocr_confidence") or 0.0)
        speed = vehicle.get("speed")
        if speed in (None, ""):
            speed = vehicle.get("speed_px_per_sec")
        try:
            speed_value = float(speed) if speed not in (None, "") else None
        except (TypeError, ValueError):
            speed_value = None

        try:
            speed_limit = float(vehicle.get("speed_limit")) if vehicle.get("speed_limit") not in (None, "") else None
        except (TypeError, ValueError):
            speed_limit = None

        if license_plate and ocr_conf >= 0.75:
            actions.append("RUN_PLATE_LOOKUP")
            reasons.append(f"plate confidence {ocr_conf:.2f} is high enough for lookup")
            priority = "MEDIUM"
        elif license_plate:
            actions.append("QUEUE_OCR_REVIEW")
            reasons.append(f"plate {license_plate} present but OCR confidence {ocr_conf:.2f} needs review")

        if speed_value is not None and speed_limit is not None and speed_value > speed_limit:
            actions.append("DISPATCH_SPEED_ALERT")
            reasons.append(f"speed {speed_value:.2f} exceeded limit {speed_limit:.2f}")
            priority = "HIGH"

        if category == "license_plate_detected":
            actions.append("PERSIST_VEHICLE_INTELLIGENCE")
            reasons.append("vehicle identity metadata is available for durable storage")

        if not actions:
            actions.append("MONITOR_TRAFFIC_FLOW")
            reasons.append("no enforcement rule matched; continue monitoring")

        reasoning = (
            f"{self.role} reviewed event category={category} "
            f"camera={telemetry.get('camera_id', 'unknown')} and proposed: {', '.join(actions)}"
        )
        if reasons:
            reasoning += f" because {'; '.join(reasons)}."

        outcome = AgentOutcome(
            agent=self.name,
            status="success",
            reasoning=reasoning,
            actions_proposed=actions,
            priority=priority,
        )
        logger.info("Agent outcome %s", outcome)
        return outcome.__dict__


def create_strategic_command_agent() -> CoordinationPolicyEngine:
    return CoordinationPolicyEngine("StrategicCommand", "Strategic Command & Policy Layer")


def create_regional_coordination_agent(sector: str) -> CoordinationPolicyEngine:
    return CoordinationPolicyEngine(f"RegionalCoordination_{sector}", "District Congestion & Patrol Dispatch")


def create_incident_coordination_agent(incident_id: str) -> CoordinationPolicyEngine:
    return CoordinationPolicyEngine(f"IncidentCoordination_{incident_id}", "Local Lifecycle & Sensor Triage")
