# Docker Setup

Use ROCm-compatible Docker images for reproducible AMD GPU execution.

## Recommended Approach

1. Install ROCm host drivers.
2. Install Docker.
3. Use AMD ROCm PyTorch images where available.
4. Mount benchmark configs and output folders.
5. Capture logs and screenshots.

## Example Command

```bash
docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  -v "$PWD":/workspace \
  rocm/pytorch:latest \
  python -c "import torch; print(torch.cuda.is_available())"
```

## Patent Safety

Do not mount private source directories, confidential datasets, or internal workflow logs into public benchmark containers.
