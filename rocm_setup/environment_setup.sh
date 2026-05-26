#!/usr/bin/env bash
set -euo pipefail

echo "SITA Hermes Agent AMD environment setup"
echo "This script prepares a Python environment only."
echo "Install ROCm using official AMD documentation before running GPU benchmarks."

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Validating PyTorch import..."
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("torch.cuda.is_available:", torch.cuda.is_available())
PY

echo "Environment setup complete."
