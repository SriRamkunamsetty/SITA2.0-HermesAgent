# ROCm Setup

ROCm is the AMD software stack for GPU programming and AI workload acceleration. Use official AMD documentation as the source of truth for supported distributions, GPU compatibility, package versions, and installation commands.

## Core Components

- HIP runtime
- HIPCC compiler
- ROCr runtime
- rocBLAS
- MIOpen
- RCCL
- MIGraphX
- RPP
- MIVisionX
- `rocminfo`
- `amd-smi`
- `rocprof`

## Validation Commands

```bash
rocminfo
amd-smi list
amd-smi monitor
```

## PyTorch ROCm Check

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("rocm visible through torch.cuda:", torch.cuda.is_available())
print("device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
PY
```

PyTorch commonly exposes ROCm-backed devices through the `torch.cuda` namespace.

## Recommended Evidence

- Screenshot of `rocminfo`
- Screenshot of `amd-smi monitor`
- Screenshot of PyTorch ROCm check
- ROCm version
- GPU model and memory capacity
- Benchmark logs
