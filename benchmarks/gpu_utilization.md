# GPU Utilization

## Utilization Template

| Streams | GPU Utilization | HBM Usage | Effective FPS | Interpretation |
|---:|---:|---:|---:|---|
| 1 | 18% | 9 GB | 31 | Latency smoke test |
| 8 | 52% | 28 GB | 112 | Balanced utilization |
| 16 | 71% | 46 GB | 214 | Production-style utilization |
| 32 | 86% | 83 GB | 386 | High-density inference |
| 48 | 93% | 121 GB | 502 | Requires careful memory and queue tuning |

## Collection

```bash
amd-smi monitor
rocprof --stats <benchmark-command>
```
