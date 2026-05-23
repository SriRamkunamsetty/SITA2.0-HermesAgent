import hashlib
import hmac
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import jwt
import redis
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from neo4j import GraphDatabase
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from agents import (
    create_incident_coordination_agent,
    create_regional_coordination_agent,
    create_strategic_command_agent,
)
from workflow_engine import WorkflowKernel


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelos.hermes")

tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)
ot_tracer = trace.get_tracer("sentinelos.hermes")
propagator = TraceContextTextMapPropagator()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
PG_DSN = os.getenv("PG_DSN", "dbname=sentinelos user=postgres password=sentinelos_local_dev_only host=postgres-db")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sentinelos_local_dev_only")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "sentinelos_local_dev_only")
JWT_SECRET = os.getenv("JWT_SECRET", "sentinelos_local_dev_only")
JWT_ALGORITHMS = [alg.strip() for alg in os.getenv("JWT_ALGORITHMS", "HS256").split(",") if alg.strip()]

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
workflow_kernel = WorkflowKernel(PG_DSN, redis_client)
app = FastAPI(title="SentinelOS Hardened Hermes Engine")
security = HTTPBearer()
graph_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="graph-sync")

registry = CollectorRegistry()
webhook_events = Counter("sita_hermes_webhook_events_total", "Received webhook events", registry=registry)
workflow_replays = Counter("sita_hermes_workflow_replays_total", "Workflow replay requests", registry=registry)
workflow_steps = Counter("sita_hermes_workflow_steps_total", "Workflow steps executed", registry=registry)
graph_sync_failures = Counter("sita_hermes_graph_sync_failures_total", "Graph sync failures", registry=registry)
workflow_latency = Histogram("sita_hermes_workflow_latency_seconds", "Incident coordination latency", registry=registry)
active_pipeline_tasks = Gauge("sita_hermes_active_pipeline_tasks", "Active background incident pipelines", registry=registry)


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHMS)


class GraphSyncClient:
    def __init__(self):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as exc:
            logger.error("Neo4j driver initialization failed: %s", exc)

    def sync_incident(self, incident_data: dict, agent_actions: List[Dict[str, object]]):
        if not self.driver:
            return

        plate = incident_data.get("vehicle", {}).get("license_plate") or f"track-{incident_data.get('event_id', 'unknown')}"
        camera_id = incident_data.get("telemetry", {}).get("camera_id", "UNKNOWN")
        timestamp = incident_data.get("timestamp", 0)
        speed = incident_data.get("vehicle", {}).get("speed")
        if speed in (None, ""):
            speed = incident_data.get("vehicle", {}).get("speed_px_per_sec", 0.0)
        category = incident_data.get("category", "vehicle_detected")

        action_rows = []
        for action in agent_actions:
            for proposal in action.get("actions_proposed", []):
                action_rows.append({"agent": action["agent"], "proposal": proposal, "priority": action.get("priority", "LOW")})

        query = """
        MERGE (v:Vehicle {license_plate: $plate})
        MERGE (c:Camera {id: $camera_id})
        MERGE (i:Incident {event_id: $event_id})
        SET i.timestamp = $timestamp,
            i.category = $category,
            i.speed = $speed
        MERGE (v)-[:INVOLVED_IN]->(i)
        MERGE (i)-[:DETECTED_AT]->(c)
        WITH i
        UNWIND $actions AS action
        MERGE (a:Action {name: action.proposal})
        MERGE (i)-[:REQUIRES {agent: action.agent, priority: action.priority}]->(a)
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    plate=plate,
                    camera_id=camera_id,
                    event_id=incident_data.get("event_id"),
                    timestamp=timestamp,
                    speed=float(speed or 0.0),
                    category=category,
                    actions=action_rows,
                )
        except Exception as exc:
            graph_sync_failures.inc()
            logger.error("Graph sync error: %s", exc)


graph_sync_client = GraphSyncClient()


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = decode_jwt_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        logger.warning("Rejected request: Invalid bearer JWT token. %s", exc)
        raise HTTPException(status_code=403, detail="Invalid token credentials")

    scopes = payload.get("scopes", [])
    if "sentinelos:admin" not in scopes and payload.get("role") not in ("sector_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Insufficient scope")
    return payload


def verify_hmac_signature(body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    calculated_sig = hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_sig, signature_header)


@app.post("/webhook/sita-incident")
async def receive_sita_incident(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")
    if not verify_hmac_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC Signature")

    payload = json.loads(body)
    event_id = payload.get("event_id")
    traceparent = payload.get("traceparent", "")
    parent_context = propagator.extract(carrier={"traceparent": traceparent})

    with ot_tracer.start_as_current_span("receive_incident_webhook", context=parent_context) as span:
        span.set_attribute("event_id", event_id)
        webhook_events.inc()
        background_tasks.add_task(process_incident_pipeline, payload)

    return {"status": "accepted", "event_id": event_id}


def process_incident_pipeline(payload: dict):
    event_id = payload.get("event_id")
    active_pipeline_tasks.inc()
    start_time = workflow_latency.time()
    try:
        strategic_agent = create_strategic_command_agent()
        regional_agent = create_regional_coordination_agent(payload.get("telemetry", {}).get("camera_id"))
        incident_agent = create_incident_coordination_agent(event_id)

        outcomes = [
            strategic_agent.run_task(payload),
            regional_agent.run_task(payload),
            incident_agent.run_task(payload),
        ]
        payload["coordination"] = {"agent_outcomes": outcomes}

        workflow_kernel.create_workflow(event_id, event_id, payload)
        for _ in range(5):
            workflow_kernel.execute_workflow_turn(event_id)
            workflow_steps.inc()

        graph_executor.submit(graph_sync_client.sync_incident, payload, outcomes)
    finally:
        active_pipeline_tasks.dec()
        start_time.observe_duration()


@app.get("/workflows/{workflow_id}/history", dependencies=[Depends(verify_jwt_token)])
def get_workflow_history(workflow_id: str):
    history = workflow_kernel.get_state_history(workflow_id)
    return {"workflow_id": workflow_id, "history": history}


@app.post("/workflows/{workflow_id}/replay", dependencies=[Depends(verify_jwt_token)])
def replay_workflow(workflow_id: str):
    workflow_replays.inc()
    logger.info("Operator triggered state replay execution for workflow=%s", workflow_id)
    try:
        conn = workflow_kernel._get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE workflows SET current_state = 'DETECTED', retry_count = 0 WHERE id = %s", (workflow_id,))
        cur.execute(
            "INSERT INTO incident_state_history (workflow_id, from_state, to_state, operator) VALUES (%s, 'REPLAY_RESET', 'DETECTED', 'OPERATOR')",
            (workflow_id,),
        )
        conn.commit()
        cur.close()
        conn.close()
        workflow_kernel.execute_workflow_turn(workflow_id)
        workflow_steps.inc()
        return {"status": "replayed", "workflow_id": workflow_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8644)
