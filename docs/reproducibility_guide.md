# Reproducibility Guide

## Objective

Provide a repeatable public workflow that AMD AI Engage reviewers can inspect without access to proprietary SITA Hermes Agent internals.

## Workflow

1. Clone repository.
2. Install ROCm-supported AMD GPU environment.
3. Validate GPU visibility.
4. Install PyTorch ROCm.
5. Configure benchmark YAML.
6. Run benchmark workload.
7. Capture logs and screenshots.
8. Update benchmark result files.
9. Publish sanitized evidence.

## Required Evidence

- ROCm version
- GPU model
- GPU memory capacity
- `rocminfo` output
- `amd-smi` utilization output
- PyTorch ROCm validation output
- Benchmark summary tables
- Sanitized screenshots

## Redaction Requirements

Remove:

- Internal module names
- Secret orchestration logs
- Proprietary scheduling traces
- Private dataset references
- Patent-sensitive architecture details
