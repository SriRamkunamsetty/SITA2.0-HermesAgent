# Throughput Analysis

## Multi-GPU Throughput Template

| GPU Count | Streams | Aggregate FPS | p95 Latency | Scale Efficiency |
|---:|---:|---:|---:|---:|
| 1 | 32 | 386 | 31 ms | 100% |
| 2 | 64 | 742 | 34 ms | 96% |
| 4 | 128 | 1,432 | 38 ms | 93% |
| 8 | 256 | 2,760 | 44 ms | 89% |

## Analysis

Throughput scaling depends on stream partitioning, GPU memory residency, host-device transfer behavior, queue scheduling, and interconnect topology. Proprietary orchestration details are omitted.
