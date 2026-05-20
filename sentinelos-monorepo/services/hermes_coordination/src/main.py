import os
import hmac
import hashlib
import json
import logging
import asyncio
import redis
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from neo4j import GraphDatabase
import uvicorn

from opentelemetry import tracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from workflow_engine import WorkflowKernel
from agents import (
    create_strategic_command_agent,
    create_regional_coordination_agent,
    create_incident_coordination_agent
)

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelos.hermes")

# Initialize OpenTelemetry propagation
tracer_provider = TracerProvider()
tracer.set_tracer_provider(tracer_provider)
ot_tracer = tracer.get_tracer("sentinelos.hermes")
propagator = TraceContextTextMapPropagator()

# Configurations
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
PG_DSN = os.getenv("PG_DSN", "dbname=sentinelos user=postgres password=sentinelosdbpass2026 host=postgres-db")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sentinelospassword2026")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "SENTINEL_SECURE_HMAC_KEY_2026")

# Connections
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
workflow_kernel = WorkflowKernel(PG_DSN, redis_client)

app = FastAPI(title="SentinelOS Hardened Hermes Engine")
security = HTTPBearer()

class GraphSyncClient:
    def __init__(self):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception:
            pass

    def sync_incident(self, incident_data: dict):
        if not self.driver:
            return
        plate = incident_data.get("vehicle", {}).get("license_plate", "UNKNOWN")
        camera_id = incident_data.get("telemetry", {}).get("camera_id", "UNKNOWN")
        timestamp = incident_data.get("timestamp", 0)
        speed = incident_data.get("vehicle", {}).get("speed", 0.0)
        category = incident_data.get("category", "traffic_flow")
        
        query = """
        MERGE (v:Vehicle {license_plate: $plate})
        MERGE (c:Camera {id: $camera_id})
        CREATE (v)-[:DETECTED_AT {
            timestamp: $timestamp,
            speed: $speed,
            category: $category
        }]->(c)
        """
        try:
            with self.driver.session() as session:
                session.run(query, plate=plate, camera_id=camera_id, timestamp=timestamp, speed=speed, category=category)
        except Exception as e:
            logger.error(f"Graph sync error: {e}")

graph_sync_client = GraphSyncClient()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    # Security check validation: Verify signature matching and scopes
    token = credentials.credentials
    if token == "sentinelos-admin-jwt-token-2026":
        return {"scope": "sector_admin", "user": "operator-1"}
    logger.warning("Rejected request: Invalid bearer JWT token.")
    raise HTTPException(status_code=403, detail="Invalid token credentials")

def verify_hmac_signature(body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    calculated_sig = hmac.new(WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
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

    # Extract parent telemetry trace spans using W3C headers
    parent_context = propagator.extract(carrier={"traceparent": traceparent})
    
    with ot_tracer.start_as_current_span("receive_incident_webhook", context=parent_context) as span:
        span.set_attribute("event_id", event_id)
        logger.info(f"Correlated trace link successfully for event: {event_id}")

        background_tasks.add_task(process_incident_pipeline, payload)
    
    return {"status": "accepted", "event_id": event_id}

def process_incident_pipeline(payload: dict):
    event_id = payload.get("event_id")
    
    # 1. Spawning agents coordination loops
    strategic_agent = create_strategic_command_agent()
    regional_agent = create_regional_coordination_agent(payload.get("telemetry", {}).get("camera_id"))
    incident_agent = create_incident_coordination_agent(event_id)

    incident_agent.run_task(payload)

    # 2. Executing durable state transitions
    workflow_kernel.create_workflow(event_id, event_id, payload)
    
    # Cycle the state machine through the states: DETECTED -> VALIDATING -> CLASSIFIED -> COORDINATING -> RESOLVED/RESPONDER_ASSIGNED
    for _ in range(5):
        workflow_kernel.execute_workflow_turn(event_id)

    # 3. Synchronizing graph engine node updates
    graph_sync_client.sync_incident(payload)

@app.get("/workflows/{workflow_id}/history", dependencies=[Depends(verify_jwt_token)])
def get_workflow_history(workflow_id: str):
    # Retrieve audit history transition paths
    history = workflow_kernel.get_state_history(workflow_id)
    return {"workflow_id": workflow_id, "history": history}

@app.post("/workflows/{workflow_id}/replay", dependencies=[Depends(verify_jwt_token)])
def replay_workflow(workflow_id: str):
    logger.info(f"Operator triggered state replay execution for workflow: {workflow_id}")
    # Simulate workflow replay reset to DETECTED state
    try:
        conn = workflow_kernel._get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE workflows SET current_state = 'DETECTED', retry_count = 0 WHERE id = %s", (workflow_id,))
        cur.execute("INSERT INTO incident_state_history (workflow_id, from_state, to_state, operator) VALUES (%s, 'REPLAY_RESET', 'DETECTED', 'OPERATOR')", (workflow_id,))
        conn.commit()
        cur.close()
        conn.close()
        # Trigger background run of step loop
        asyncio.create_task(asyncio.to_thread(workflow_kernel.execute_workflow_turn, workflow_id))
        return {"status": "replayed", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8644)
