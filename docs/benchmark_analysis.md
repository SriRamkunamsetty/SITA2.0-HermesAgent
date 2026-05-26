# Benchmark Analysis

## Benchmark Goals

The benchmark framework is designed to evaluate the public AMD GPU acceleration surface of SITA Hermes Agent without exposing proprietary implementation details.

Metrics:

- FPS
- p50 latency
- p95 latency
- Inference throughput
- GPU utilization
- HBM memory usage
- CPU vs AMD GPU speedup

## CPU vs AMD GPU Template

| Execution Mode | Streams | Avg FPS | p50 Latency | p95 Latency | Relative Throughput |
|---|---:|---:|---:|---:|---:|
| CPU baseline | 4 | 18 | 142 ms | 231 ms | 1.0x |
| AMD GPU FP32 | 8 | 96 | 41 ms | 68 ms | 5.3x |
| AMD GPU FP16/BF16 | 16 | 214 | 24 ms | 39 ms | 11.9x |
| AMD GPU optimized | 32 | 386 | 18 ms | 31 ms | 21.4x |

## Interpretation

The benchmark template demonstrates expected measurement categories. Values must be replaced with measured results from a target AMD GPU system before formal publication.

## Profiling Notes

Use:

- `amd-smi monitor` for utilization and memory
- `rocprof` for kernel-level profiling
- PyTorch profiler for model-level timing
- CSV export for repeatable analysis
