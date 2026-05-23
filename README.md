# SITA 2.0 - Hermes Agent

## Real-Time Civic Intelligence and Coordination Platform

SITA 2.0 is a multi-part project that combines:

- real-time vehicle perception
- Redis Streams eventing
- workflow coordination
- graph persistence
- observability infrastructure
- a longer-term autonomous operations vision

This repository is not just one service. It contains:

- a legacy but real computer vision runtime in `SITA/`
- a newer distributed runtime scaffold in `sentinelos-monorepo/`
- a vendored upstream `hermes-agent/` codebase for future deeper integration

The current engineering goal is to turn those pieces into one reliable local-first operational system.

---

## What The Project Does

At a high level, SITA 2.0 is designed to:

1. ingest live or recorded traffic video
2. detect and track vehicles in real time
3. extract useful metadata such as vehicle type, color, speed estimate, and plate text
4. publish structured detection events into Redis Streams
5. route those events into a coordination runtime
6. persist workflow and graph state for investigation and follow-up
7. expose operational telemetry for monitoring and debugging

The target category is:

- AI perception system
- event-driven backend
- workflow orchestration platform
- civic operations intelligence stack

---

## Repository Layout

### `SITA/`

Legacy working application with:

- Flask backend
- YOLO vehicle detection
- ByteTrack-based tracking
- EasyOCR-based OCR
- SQLite and file output flow
- dashboard-oriented processing path

This is the most mature perception implementation in the repo history.

### `sentinelos-monorepo/`

Current distributed runtime foundation with:

- `services/perception`
- `services/event_runtime`
- `services/hermes_coordination`
- `deployment/docker-compose.yaml`
- Prometheus, Loki, Grafana, Postgres, Neo4j, Redis, OTel collector

This is the main local stack now used for system hardening.

### `hermes-agent/`

Vendored upstream Hermes Agent codebase.

Important note:

- it is present in the repository
- it is not yet deeply integrated into the active Sentinel runtime path
- current `hermes_coordination` is still a custom coordination service, not full upstream Hermes runtime execution

---

## Current Runtime Architecture

```text
Video / RTSP / MP4
        |
        v
Perception Service
(YOLO + tracking + OCR + color analysis)
        |
        v
Redis Streams
        |
        v
Event Runtime
        |
        v
Hermes Coordination Service
        |
        +--> PostgreSQL workflow state
        |
        +--> Neo4j graph state
        |
        +--> Prometheus metrics / OTel hooks
```

---

## What Has Been Completed

## 1. Real Perception Path

Completed:

- random and fake detections removed
- real YOLO-based detection path added in `sentinelos-monorepo/services/perception`
- ByteTrack-backed `model.track(...)` pipeline used for persistent IDs
- real EasyOCR integration enabled
- LAB and HSV-based vehicle color analysis implemented
- speed estimation propagated from track movement
- actual detection metadata emitted into Redis Streams

Completed CPU support:

- perception container now builds and runs on CPU
- startup no longer depends on remote YOLO weight download
- local YOLO model is mounted from `SITA/yolov8s.pt`
- EasyOCR weights are mounted locally from `sentinelos-monorepo/deployment/easyocr-models/`

Validated locally:

- sample MP4 processed through the perception service
- frames processed
- real detections emitted
- metrics exposed on `/metrics`

## 2. Distributed Event Runtime

Completed:

- Redis Streams consumer group flow is working
- detection events are consumed from `sita:stream:detections`
- event runtime forwards events to Hermes webhook
- stronger deduplication logic added
- pending message recovery support improved
- metrics exposed for dispatch, DLQ, lag, and backpressure state

Validated locally:

- real events moved from perception into Redis
- event runtime dispatched all observed test events
- Redis consumer group pending count reached `0`
- Redis consumer group lag reached `0`

## 3. Hermes Coordination Service

Completed:

- service boots with Postgres and Neo4j dependencies
- HMAC-protected webhook intake is working
- JWT decoding path improved
- workflow persistence is real
- graph sync writes real nodes such as `Incident`, `Vehicle`, `Camera`, and `Action`
- service exposes metrics

Validated locally:

- webhook events received from event runtime
- workflow rows created in Postgres
- graph nodes created in Neo4j

## 4. Observability Stack

Completed:

- Prometheus boots and scrapes active services
- Grafana boots
- Loki boots and responds on readiness endpoint
- OTel collector boots
- perception, event runtime, and Hermes all expose `/metrics`

Validated locally:

- Prometheus target health is up for:
  - `perception-service`
  - `event-runtime`
  - `hermes-runtime`
  - `otel-collector`
- Loki readiness endpoint responds

## 5. Local Deployment Hardening

Completed:

- local Docker Compose ports moved to non-conflicting host ports
- services can boot alongside other local software
- CPU-first local path established
- perception runtime no longer depends on startup-time model downloads

## 6. Security Fixes Already Applied

Completed:

- Flask debug mode no longer forced on
- super-admin creation now hashes passwords
- open-access organization bypass is no longer enabled by default
- Hermes JWT path improved from simple token compare toward real decode flow

---

## What Has Been Validated End-to-End

The following path has been manually validated locally:

```text
MP4 input
-> perception service
-> YOLO detections
-> tracking
-> color analysis
-> Redis Stream publish
-> event runtime dispatch
-> Hermes webhook intake
-> PostgreSQL workflow persistence
-> Neo4j graph persistence
-> Prometheus metrics
```

Observed during validation:

- perception processed a real sample MP4
- `17` real detection events were emitted during one test run
- `17` events were dispatched by event runtime
- `17` events were received by Hermes
- Redis pending count was `0`
- Redis lag was `0`

---

## What Is Currently In Progress

These areas are actively being hardened now:

## 1. Runtime Unification

In progress:

- reducing duplication between legacy `SITA/` runtime and `sentinelos-monorepo/`
- defining one stable golden path for local-first execution

## 2. Perception Accuracy Hardening

In progress:

- OCR stabilization across frames
- better plate preprocessing
- temporal voting for OCR
- temporal voting for color stability
- smoother CPU behavior under load
- GPU path re-validation after CPU path stabilization

## 3. Distributed Reliability

In progress:

- replay validation
- DLQ recovery tooling
- service restart behavior testing
- Redis failure testing
- idempotency validation across workflow execution

## 4. Observability Maturity

In progress:

- better OTel export verification
- more complete latency instrumentation
- stream lag and workflow latency dashboards
- tighter operational visibility on perception internals

---

## What Is Still Pending

## 1. Full Upstream Hermes Integration

Pending:

- replace or deeply integrate the custom `hermes_coordination` service with real upstream `hermes-agent` runtime semantics
- add true tool-execution orchestration
- add durable autonomous reasoning loops
- add richer agent memory integration

Current truth:

- the repo contains `hermes-agent`
- the active runtime path does not yet fully use it

## 2. GPU Production Path

Pending:

- Triton server golden-path validation
- TensorRT-backed inference validation
- GPU batching and queue design
- NVDEC / GStreamer optimized ingest path
- GPU telemetry validation with real NVIDIA runtime

Current truth:

- GPU profile exists in Compose
- the validated working path today is CPU-first
- Triton was not part of the validated end-to-end run

## 3. OCR Production Accuracy

Pending:

- multi-frame confidence aggregation tuning
- night and blur handling validation
- perspective robustness on angled plates
- better false-positive suppression
- dataset-based accuracy benchmarking

## 4. Cross-Camera Graph Intelligence

Pending:

- trajectory reconstruction
- cross-camera movement linking
- spatial-temporal search flows
- investigation-oriented graph queries

Current truth:

- Neo4j persistence exists
- deeper graph intelligence is not complete yet

## 5. Replay and Recovery Maturity

Pending:

- operator-driven DLQ replay
- broader crash/restart simulations
- workflow resume guarantees across outages
- tighter pending-claim and replay tooling

## 6. Security Hardening

Pending:

- stronger auth model across the full stack
- removal of remaining header-trust patterns in legacy paths
- RBAC
- secrets management cleanup
- service-to-service auth tightening

## 7. Kubernetes and Cloud Scale

Pending:

- Helm or Kubernetes manifests
- GPU node scheduling design
- autoscaling policies
- edge/cloud topology
- production-grade deployment docs

---

## Completion Matrix

| Area | Status | Notes |
|---|---|---|
| Local Docker stack | Working | Boots successfully on validated CPU path |
| Perception runtime | Working, improving | Real YOLO/OCR/color flow, CPU validated |
| Tracking | Working, improving | ByteTrack-backed path active |
| Redis Streams | Working | End-to-end event flow validated |
| Event runtime | Working | Dispatch validated with real events |
| Hermes coordination | Partially real | Real persistence and webhook flow, not full upstream Hermes |
| Postgres persistence | Working | Workflow rows present |
| Neo4j persistence | Working | Graph nodes present |
| Prometheus metrics | Working | Active targets scraping |
| Grafana/Loki/OTel boot | Working | Booted locally |
| Triton GPU path | Pending validation | Not part of current validated path |
| True autonomous agent runtime | Pending | Still not full upstream Hermes execution |
| Production replay recovery | Partial | Core pieces exist, full validation pending |
| Enterprise security posture | Partial | Some fixes done, more work pending |

---

## What We Are Doing Right Now

Current engineering focus:

1. stabilize one local golden runtime path
2. keep all AI outputs real
3. improve OCR and color consistency
4. harden replay, recovery, and workflow correctness
5. move from "working demo path" to "reliable operational system"

Short-term next steps:

- validate more videos and RTSP sources
- measure OCR quality and color consistency
- stress the Redis and workflow path
- tighten workflow state semantics
- improve graph usefulness
- reintroduce GPU/Triton path in a controlled way

---

## Known Operational Gaps

These are important and should be treated honestly:

- the system is not fully production-ready yet
- the GPU path is not the validated golden path today
- full upstream Hermes Agent orchestration is not yet wired in
- observability is better, but still not fully complete
- security is improved, but not enterprise-complete
- replay and DLQ operations still need more hardening

---

## How To Run The Current Local Stack

From `sentinelos-monorepo/deployment/`:

```powershell
docker compose up -d --build
```

Important local notes:

- validated host ports are defined in `sentinelos-monorepo/deployment/docker-compose.yaml`
- CPU mode is the currently validated default
- YOLO weights are mounted from `SITA/yolov8s.pt`
- EasyOCR weights are mounted from `sentinelos-monorepo/deployment/easyocr-models/`

Useful endpoints:

- Perception: `http://localhost:18012/health`
- Event runtime: `http://localhost:18003/health`
- Hermes runtime: `http://localhost:18644/health`
- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13000`
- Loki: `http://localhost:13100/ready`

---

## Manual Test Flow

Example local manual validation flow:

1. start the Docker stack
2. send a local MP4 or RTSP stream to the perception service
3. confirm `/health` and `/metrics` on perception
4. inspect Redis stream growth
5. confirm event runtime dispatch metrics
6. confirm Hermes webhook metrics
7. inspect Postgres workflow rows
8. inspect Neo4j nodes and relationships
9. verify Prometheus target health

---

## Final Project Status

Current status:

- the project has moved from concept-heavy scaffolding toward a real locally working runtime
- the perception-to-event-to-workflow path is now real on CPU
- the system is in active production-hardening phase
- major work remains before enterprise or city-scale deployment

Best concise description:

SITA 2.0 is now a partially realized autonomous civic intelligence platform with a working local golden path, real AI outputs, real event flow, real persistence, and active hardening still underway around orchestration depth, GPU scale, replay resilience, and production security.
