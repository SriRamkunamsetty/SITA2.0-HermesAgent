# PyTorch ROCm Setup

PyTorch supports ROCm-backed AMD GPU execution. Follow official AMD and PyTorch guidance for version-specific installation.

## Validation Script

```bash
python - <<'PY'
import torch
print("PyTorch:", torch.__version__)
print("GPU available:", torch.cuda.is_available())
print("Device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("Device 0:", torch.cuda.get_device_name(0))
PY
```

## Important Note

PyTorch commonly uses the `torch.cuda` namespace even when execution is backed by ROCm/HIP.

## Recommended Container Path

Use AMD-published ROCm PyTorch Docker images when available for consistent dependency alignment.
