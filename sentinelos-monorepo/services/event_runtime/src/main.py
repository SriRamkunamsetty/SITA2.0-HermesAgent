import os
import time
import json
import logging
import hmac
import hashlib
import threading
import redis
import httpx
import uvicorn
from fastapi import FastAPI

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelos.event_runtime")

# Configurations
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
HERMES_WEBHOOK_URL = os.getenv("HERMES_WEBHOOK_URL", "http://localhost:8644/webhook/sita-incident")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "SENTINEL_SECURE_HMAC_KEY_2026")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=3.0)
app = FastAPI(title="SentinelOS Hardened Event Runtime")

class EventStreamConsumer(threading.Thread):
    def __init__(self, stream_name: str, group_name: str, consumer_name: str):
        super().__init__()
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.running = False
        self._initialize_group()

    def _initialize_group(self):
        try:
            redis_client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create consumer group: {e}")

    def run(self):
        self.running = True
        logger.info(f"Starting consumer loop for group: {self.group_name}")
        
        while self.running:
            try:
                # 1. Run Dynamic Backpressure Evaluation Checks
                self._evaluate_backpressure()

                # 2. Consume events
                streams_data = redis_client.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=10,
                    block=2000
                )
                
                if not streams_data:
                    continue

                for stream, messages in streams_data:
                    for message_id, payload in messages:
                        self.process_stream_payload(message_id, payload)
                        
            except redis.exceptions.ConnectionError:
                time.sleep(5.0)
            except Exception as e:
                logger.error(f"Error in consumer: {e}")
                time.sleep(1.0)

    def _evaluate_backpressure(self):
        try:
            # Query stream pending status length
            pending_info = redis_client.xpending(self.stream_name, self.group_name)
            pending_count = pending_info.get("pending", 0)
            
            # Export lag metric inside Redis
            redis_client.set("metrics:triton:lag", str(pending_count))

            if pending_count >= 1000:
                # Threshold reached: set backpressure throttle flag
                redis_client.set("system:backpressure:active", "1")
                logger.warning(f"Backpressure ACTIVATED. Ingestion stream lag: {pending_count}")
            elif pending_count <= 100:
                # Normal conditions: release backpressure throttling
                redis_client.set("system:backpressure:active", "0")
        except Exception as e:
            logger.error(f"Failed to check backpressure metrics: {e}")

    def process_stream_payload(self, message_id: bytes, payload: dict):
        data = {k.decode('utf-8') if isinstance(k, bytes) else k: 
                v.decode('utf-8') if isinstance(v, bytes) else v for k, v in payload.items()}
        
        license_plate = data.get("license_plate", f"PLATE-{data.get('track_id', 'UNKNOWN')}")
        camera_id = data.get("camera_id", "CAM-UNKNOWN")
        
        # Deduplication Lock check
        dedup_key = f"lock:dedup:{license_plate}:{camera_id}"
        is_duplicate = not redis_client.set(dedup_key, "1", nx=True, ex=30)
        
        if is_duplicate:
            redis_client.xack(self.stream_name, self.group_name, message_id)
            return

        # Prepare payload structure and carry W3C trace parents
        incident_package = {
            "event_id": f"evt-{message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id}",
            "timestamp": int(float(data.get("timestamp", time.time()))),
            "category": "blacklist_alert" if int(data.get("class_id", 0)) == 2 else "traffic_flow",
            "priority": "HIGH" if int(data.get("class_id", 0)) == 2 else "LOW",
            "traceparent": data.get("traceparent", ""),
            "telemetry": {
                "camera_id": camera_id,
                "camera_name": f"Camera {camera_id}",
                "latitude": 37.7749,
                "longitude": -122.4194
            },
            "vehicle": {
                "type": "Car" if int(data.get("class_id", 0)) == 2 else "Truck",
                "color": "Black",
                "license_plate": license_plate,
                "ocr_confidence": float(data.get("confidence", 0.90)),
                "speed": 85.0,
                "speed_limit": 60.0
            }
        }

        # Dispatch with Retries and Dead Letter Queue (DLQ) Fallback
        success = self.dispatch_to_hermes_webhook_with_dlq(message_id, incident_package)
        if success:
            redis_client.xack(self.stream_name, self.group_name, message_id)

    def dispatch_to_hermes_webhook_with_dlq(self, message_id: bytes, payload: dict) -> bool:
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Request-ID": payload["event_id"]
        }
        
        # Dispatch retry loop
        for attempt in range(3):
            try:
                response = httpx.post(HERMES_WEBHOOK_URL, content=body, headers=headers, timeout=5.0)
                if response.status_code in [200, 202]:
                    return True
            except Exception as e:
                logger.error(f"Hermes dispatch attempt {attempt+1} failed: {e}")
            time.sleep(1.0)
            
        # All retry attempts failed: route event payload to Dead Letter Queue (DLQ)
        logger.error(f"Incident {payload['event_id']} exceeded retry limit. Quarantining to DLQ.")
        try:
            dlq_payload = {
                "original_message_id": message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id,
                "payload": json.dumps(payload),
                "quarantine_timestamp": str(time.time()),
                "failure_reason": "Hermes endpoint unreachable after 3 attempts"
            }
            redis_client.xadd("sita:stream:dlq", dlq_payload)
            # Acknowledge the message inside the source stream since it has been safely quarantined in DLQ
            return True
        except Exception as e:
            logger.error(f"Critical failure: Could not quarantine message to DLQ: {e}")
            return False

    def stop(self):
        self.running = False

consumer_thread = None

@app.on_event("startup")
def startup_event():
    global consumer_thread
    consumer_thread = EventStreamConsumer("sita:stream:detections", "hermes-event-relay", "relay-worker-1")
    consumer_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    global consumer_thread
    if consumer_thread:
        consumer_thread.stop()
        consumer_thread.join()

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
