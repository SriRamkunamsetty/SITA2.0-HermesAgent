# SentinelOS Deployment & Runbook Instructions

This guide provides steps for setting up, executing, and benchmarking the SentinelOS (SITA 2.0) Golden Runtime Path.

---

## 1. Local Development Setup

### Prerequisites:
- Docker & Docker Compose installed.
- NVIDIA Container Toolkit configured (for GPU-accelerated GStreamer / Triton Inference Server).
- Python 3.10 installed locally.

### Start Infrastructure Stack:
Run the compose files from the `deployment` directory to spin up databases, trace collectors, and services:
```bash
cd sentinelos-monorepo/deployment
docker-compose up --build
```
This initializes the following components:
*   **Redis Sentinel (`sentinel_redis`)** at Port `6379`.
*   **PostgreSQL (`sentinel_postgres`)** at Port `5432` (credentials: `postgres/sentinelosdbpass2026`).
*   **Neo4j Graph Database (`sentinel_neo4j`)** at Port `7474` (HTTP) and `7687` (Bolt).
*   **Triton Server (`sentinel_triton`)** at Ports `8000` / `8001`.
*   **OTel Collector (`sentinel_otel_collector`)** at Port `4317`.
*   **Prometheus (`sentinel_prometheus`)** at Port `9090`.
*   **Grafana (`sentinel_grafana`)** at Port `3000`.
*   **Perception Service** running on Port `8002`.
*   **Event Runtime** running on Port `8003`.
*   **Hermes Runtime** running on Port `8644`.

---

## 2. Ingest Stream Triggering

To begin processing an RTSP camera stream on the perception worker:
```bash
curl -X POST "http://localhost:8002/streams/start?camera_id=cam-north-01&source=rtsp://admin:pass@192.168.1.100:554/h264"
```
For simulation testing with a local video file:
```bash
curl -X POST "http://localhost:8002/streams/start?camera_id=cam-sim-01&source=/app/uploads/test_traffic.mp4"
```

---

## 3. Chaos & Fault Injection Testing

To execute autonomous fault injection tests and check system resilience:
```bash
python sentinelos-monorepo/tests/chaos/test_chaos.py
```
This runs scenarios for Triton crash recovery, Redis dropouts, and verifies fallback mechanisms.

---

## 4. Benchmarking Execution

To measure FPS limits, processing lag, and API delays:
```bash
python sentinelos-monorepo/benchmarks/benchmark_golden_path.py
```
After completion, view results inside `benchmark_report.json`.

---

## 5. Production-Readiness Checklist

- [ ] Verify that GKE GPU pools are allocated with correct drivers.
- [ ] Confirm PostgreSQL WAL replication policies.
- [ ] Rotate default Neo4j and PostgreSQL database secrets.
- [ ] Verify Prometheus scrape configurations.
- [ ] Perform HMAC webhook signature handshakes on endpoints.
- [ ] Validate Triton FP16 engine optimizations.
