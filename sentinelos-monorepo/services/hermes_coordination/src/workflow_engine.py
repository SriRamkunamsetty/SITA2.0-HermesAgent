import time
import json
import logging
import psycopg2
import redis

logger = logging.getLogger("sentinelos.hermes.workflows")


def as_float(value, default=None):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

class WorkflowKernel:
    def __init__(self, pg_dsn: str, redis_client: redis.Redis):
        self.pg_dsn = pg_dsn
        self.redis = redis_client
        self._init_tables()

    def _get_connection(self):
        return psycopg2.connect(self.pg_dsn)

    def _init_tables(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # Workflow state trackers
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id VARCHAR(64) PRIMARY KEY,
                    incident_id VARCHAR(64) NOT NULL,
                    current_state VARCHAR(32) NOT NULL,
                    context TEXT NOT NULL,
                    retry_count INT DEFAULT 0,
                    max_retries INT DEFAULT 5,
                    next_execution TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Historical transition audit trails
            cur.execute("""
                CREATE TABLE IF NOT EXISTS incident_state_history (
                    id SERIAL PRIMARY KEY,
                    workflow_id VARCHAR(64) NOT NULL,
                    from_state VARCHAR(32) NOT NULL,
                    to_state VARCHAR(32) NOT NULL,
                    transition_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    operator VARCHAR(64) DEFAULT 'SYSTEM'
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Durable workflow and audit schemas initialized.")
        except Exception as e:
            logger.warning(f"PostgreSQL initialization deferred (running offline-first mode): {e}")

    def create_workflow(self, workflow_id: str, incident_id: str, context: dict):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO workflows (id, incident_id, current_state, context) VALUES (%s, %s, 'DETECTED', %s) "
                "ON CONFLICT (id) DO NOTHING",
                (workflow_id, incident_id, json.dumps(context))
            )
            # Log initial audit trail record
            cur.execute(
                "INSERT INTO incident_state_history (workflow_id, from_state, to_state) VALUES (%s, 'NONE', 'DETECTED')",
                (workflow_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Created durable workflow instance: {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to persist workflow {workflow_id}: {e}")
            self.redis.set(f"wf:offline:{workflow_id}", json.dumps({"incident_id": incident_id, "state": "DETECTED", "context": context}))

    def execute_workflow_turn(self, workflow_id: str):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT current_state, context, retry_count FROM workflows WHERE id = %s FOR UPDATE", (workflow_id,))
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return

            current_state, context_str, retry_count = row
            context = json.loads(context_str)

            logger.info(f"Executing workflow step: {workflow_id} [State: {current_state}]")

            next_state = current_state

            if current_state == "DETECTED":
                next_state = "VALIDATING"
            elif current_state == "VALIDATING":
                # Check confidence metric
                conf = context.get("vehicle", {}).get("ocr_confidence", 0.0)
                if conf >= 0.85:
                    next_state = "CLASSIFIED"
                else:
                    next_state = "ARCHIVED"
            elif current_state == "CLASSIFIED":
                next_state = "COORDINATING"
            elif current_state == "COORDINATING":
                # Escalate only when we have a real speed signal and limit.
                speed = as_float(context.get("vehicle", {}).get("speed"), None)
                if speed is None:
                    speed = as_float(context.get("vehicle", {}).get("speed_px_per_sec"), None)
                speed_limit = as_float(context.get("vehicle", {}).get("speed_limit"), None)

                if speed is not None and speed_limit is not None and speed > speed_limit:
                    next_state = "RESPONDER_ASSIGNED"
                else:
                    next_state = "RESOLVED"
            elif current_state == "RESPONDER_ASSIGNED":
                next_state = "MONITORING"
            elif current_state == "MONITORING":
                next_state = "RESOLVED"
            elif current_state == "RESOLVED":
                next_state = "ARCHIVED"

            if next_state != current_state:
                cur.execute(
                    "UPDATE workflows SET current_state = %s, retry_count = 0 WHERE id = %s",
                    (next_state, workflow_id)
                )
                cur.execute(
                    "INSERT INTO incident_state_history (workflow_id, from_state, to_state) VALUES (%s, %s, %s)",
                    (workflow_id, current_state, next_state)
                )
                logger.info(f"Workflow {workflow_id} transitioned: {current_state} -> {next_state}")

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Workflow execution failure for {workflow_id}: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()

    def get_state_history(self, workflow_id: str) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT from_state, to_state, transition_time FROM incident_state_history WHERE workflow_id = %s ORDER BY transition_time ASC",
                (workflow_id,)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [{"from_state": r[0], "to_state": r[1], "transition_time": str(r[2])} for r in rows]
        except Exception:
            return []
