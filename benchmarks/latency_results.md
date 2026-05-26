# Latency Results

## Latency Template

| Scenario | p50 Latency | p95 Latency | p99 Latency | Notes |
|---|---:|---:|---:|---|
| CPU baseline | 142 ms | 231 ms | 288 ms | CPU-only reference |
| AMD GPU FP32 | 41 ms | 68 ms | 92 ms | GPU inference enabled |
| AMD GPU FP16/BF16 | 24 ms | 39 ms | 55 ms | Mixed precision |
| AMD GPU optimized | 18 ms | 31 ms | 46 ms | Tuned queues and batching |

## Measurement Guidance

Measure end-to-end latency from frame ingestion to public analytics output. Do not include confidential internal trace fields in logs.
