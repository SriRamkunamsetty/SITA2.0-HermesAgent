# AMD GPU Workflow

```text
PyTorch Model
  -> ROCm Backend
  -> HIP Runtime
  -> ROCm Libraries
  -> AMD Instinct GPU
  -> HBM3 Memory
  -> Inference Output
```

## Optimization Points

- Keep model tensors GPU-resident.
- Use mixed precision where accuracy allows.
- Profile with ROCm tools.
- Monitor with `amd-smi`.
- Tune batch windows for latency and throughput.
