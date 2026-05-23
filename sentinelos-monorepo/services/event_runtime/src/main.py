import hashlib
import hmac
import json
import logging
import os
import threading
import time
from typing import Optional

import httpx
import redis
import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelos.event_runtime")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
HERMES_WEBHOOK_URL = os.getenv("HERMES_WEBHOOK_URL", "http://localhost:8644/webhook/sita-incident")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "sentinelos_local_dev_only")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=3.0)
app = FastAPI(title="SentinelOS Hardened Event Runtime")

registry = CollectorRegistry()
stream_pending = Gauge("sita_event_stream_pending", "Pending messages in Redis consumer group", registry=registry)
backpressure_flag = Gauge("sita_event_backpressure_active", "1 if backpressure is active", registry=registry)
dispatched_events = Counter("sita_event_dispatch_total", "Successfully dispatched events", registry=registry)
dlq_events = Counter("sita_event_dlq_total", "Events sent to DLQ", registry=registry)
consumer_errors = Counter("sita_event_consumer_errors_total", "Event consumer loop errors", registry=registry)


def parse_float(value: Optional[str], default: Optional[float] = None) -> Optional[float]:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class EventStreamConsumer(threading.Thread):
    def __init__(self, stream_name: str, group_name: str, consumer_name: str):
        super().__init__(daemon=True)
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.running = False
        self._initialize_group()

    def _initialize_group(self):
        try:
            redis_client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                logger.error("Failed to create consumer group: %s", exc)

    def run(self):
        self.running = True
        logger.info("Starting consumer loop for group=%s consumer=%s", self.group_name, self.consumer_name)

        while self.running:
            try:
                self._evaluate_backpressure()
                self._recover_stale_pending()
                streams_data = redis_client.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=10,
                    block=2000,
                )

                if not streams_data:
                    continue

                for _, messages in streams_data:
                    for message_id, payload in messages:
                        self.process_stream_payload(message_id, payload)
            except redis.exceptions.ConnectionError:
                consumer_errors.inc()
                time.sleep(5.0)
            except Exception as exc:
                consumer_errors.inc()
                logger.error("Error in consumer: %s", exc)
                time.sleep(1.0)

    def _recover_stale_pending(self):
        try:
            recovered = redis_client.xautoclaim(
                self.stream_name,
                self.group_name,
                self.consumer_name,
                min_idle_time=30000,
                start_id="0-0",
                count=25,
            )
            if not recovered or len(recovered) < 2:
                return
            messages = recovered[1]
            for message_id, payload in messages:
                self.process_stream_payload(message_id, payload)
        except redis.exceptions.ResponseError:
            # Older Redis servers may not support XAUTOCLAIM; local image does.
            pass
        except Exception as exc:
            logger.warning("Pending recovery failed: %s", exc)

    def _evaluate_backpressure(self):
        try:
            pending_info = redis_client.xpending(self.stream_name, self.group_name)
            pending_count = pending_info.get("pending", 0)
            stream_pending.set(pending_count)

            if pending_count >= 1000:
                redis_client.set("system:backpressure:active", "1")
                backpressure_flag.set(1)
            elif pending_count <= 100:
                redis_client.set("system:backpressure:active", "0")
                backpressure_flag.set(0)
        except Exception as exc:
            logger.error("Failed to check backpressure metrics: %s", exc)

    def process_stream_payload(self, message_id: bytes, payload: dict):
        data = {
            k.decode("utf-8") if isinstance(k, bytes) else k:
            v.decode("utf-8") if isinstance(v, bytes) else v
            for k, v in payload.items()
        }

        license_plate = data.get("license_plate", "")
        camera_id = data.get("camera_id", "CAM-UNKNOWN")
        vehicle_type = data.get("vehicle_type", "unknown")
        color = data.get("color", "unknown")
        color_confidence = parse_float(data.get("color_confidence"), 0.0) or 0.0
        ocr_confidence = parse_float(data.get("ocr_confidence"), 0.0) or 0.0
        speed_px_per_sec = parse_float(data.get("speed_px_per_sec"))
        detection_confidence = parse_float(data.get("confidence"), 0.0) or 0.0
        speed_limit = parse_float(data.get("speed_limit"))
        category = "license_plate_detected" if license_plate else "vehicle_detected"
        priority = "HIGH" if (license_plate and ocr_confidence >= 0.75) else "MEDIUM"

        identity = license_plate or f"{vehicle_type}:{data.get('track_id', 'UNKNOWN')}"
        payload_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        dedup_key = f"lock:dedup:{identity}:{camera_id}:{payload_hash}"
        is_duplicate = not redis_client.set(dedup_key, "1", nx=True, ex=120)
        if is_duplicate:
            redis_client.xack(self.stream_name, self.group_name, message_id)
            return

        incident_package = {
            "event_id": f"evt-{message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id}",
            "timestamp": int(float(data.get("timestamp", time.time()))),
            "category": category,
            "priority": priority,
            "traceparent": data.get("traceparent", ""),
            "telemetry": {
                "camera_id": camera_id,
                "camera_name": f"Camera {camera_id}",
                "latitude": parse_float(data.get("latitude"), 37.7749),
                "longitude": parse_float(data.get("longitude"), -122.4194),
            },
            "vehicle": {
                "type": vehicle_type,
                "color": color,
                "color_confidence": color_confidence,
                "license_plate": license_plate,
                "ocr_confidence": ocr_confidence,
                "detection_confidence": detection_confidence,
                "speed_px_per_sec": speed_px_per_sec,
                "speed_limit": speed_limit,
            },
        }

        success = self.dispatch_to_hermes_webhook_with_dlq(message_id, incident_package)
        if success:
            redis_client.xack(self.stream_name, self.group_name, message_id)

    def dispatch_to_hermes_webhook_with_dlq(self, message_id: bytes, payload: dict) -> bool:
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Request-ID": payload["event_id"],
        }

        for _ in range(3):
            try:
                response = httpx.post(HERMES_WEBHOOK_URL, content=body, headers=headers, timeout=5.0)
                if response.status_code in (200, 202):
                    dispatched_events.inc()
                    return True
            except Exception as exc:
                logger.error("Hermes dispatch failed: %s", exc)
            time.sleep(1.0)

        logger.error("Incident %s exceeded retry limit. Quarantining to DLQ.", payload["event_id"])
        try:
            dlq_payload = {
                "original_message_id": message_id.decode("utf-8") if isinstance(message_id, bytes) else message_id,
                "payload": json.dumps(payload),
                "quarantine_timestamp": str(time.time()),
                "failure_reason": "Hermes endpoint unreachable after 3 attempts",
            }
            redis_client.xadd("sita:stream:dlq", dlq_payload)
            dlq_events.inc()
            return True
        except Exception as exc:
            logger.error("Critical failure: Could not quarantine message to DLQ: %s", exc)
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
        consumer_thread.join(timeout=5.0)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
