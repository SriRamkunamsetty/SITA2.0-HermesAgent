# Ubuntu ROCm Installation

Use AMD's official ROCm installation guide for exact package commands and supported distributions.

## High-Level Steps

1. Install a ROCm-supported Ubuntu version.
2. Update system packages.
3. Install AMD GPU driver and ROCm packages.
4. Add user to required groups.
5. Reboot.
6. Validate with `rocminfo`.
7. Validate monitoring with `amd-smi`.

## Validation

```bash
rocminfo
amd-smi list
amd-smi monitor
```

## Evidence

Capture screenshots for:

- ROCm version
- GPU model
- HBM memory
- GPU utilization under benchmark load
