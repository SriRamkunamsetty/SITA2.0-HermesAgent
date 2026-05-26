# SITA Hermes Agent AMD AI Infrastructure Submission

## Project Banner

**SITA Hermes Agent** is a modular AI-powered intelligent surveillance and analytics framework designed for real-time monitoring, scalable inference workflows, object intelligence, and GPU-accelerated analytics.

This repository is an AMD AI Engage submission package focused on AMD GPU infrastructure, ROCm integration, enterprise AI inference acceleration, and reproducible benchmark documentation.

> Patent safety notice: SITA Hermes Agent is currently under patent processing. This repository intentionally omits proprietary orchestration logic, confidential architecture components, internal optimization modules, secret pipelines, and patent-sensitive implementation details.

## Abstract

Real-time AI surveillance and analytics systems require high-throughput inference, predictable latency, efficient memory use, and reproducible deployment workflows. SITA Hermes Agent positions AMD GPUs as the core acceleration layer for public benchmark and infrastructure evaluation. The repository documents a patent-safe AMD GPU acceleration blueprint using ROCm, HIP, PyTorch ROCm, AMD Instinct MI300X, AMD Instinct MI300A, HBM3 memory, and enterprise deployment practices.

The public contribution is not a disclosure of the confidential SITA Hermes Agent internals. Instead, it presents an enterprise-grade AI infrastructure package for AMD AI Engage review: research notes, ROCm setup guides, benchmark templates, architecture diagrams, deployment instructions, and a white paper draft.

## AMD AI Engage Context

This package is designed to demonstrate:

- Real-time AI workflow acceleration using AMD GPU infrastructure
- ROCm ecosystem integration
- GPU-accelerated inference pipeline design
- Reproducibility through GitHub documentation
- Enterprise AI deployment readiness
- Patent-safe technical communication

## High-Level Project Overview

SITA Hermes Agent is described publicly at a high level only. Its public-safe capabilities include:

- Real-time stream intake
- GPU-accelerated inference workflows
- Object intelligence outputs
- Scalable analytics processing
- Benchmark-ready execution paths
- Enterprise deployment documentation

The proprietary orchestration layer and internal optimization modules are omitted.

## AMD GPU Integration

AMD GPUs are treated as the primary acceleration layer for:

- Tensor inference execution
- Multi-stream AI throughput
- Batch-window optimization
- Low-latency analytics pipelines
- GPU memory residency
- Mixed precision execution
- Scalable deployment across AMD GPU nodes

## ROCm Ecosystem

ROCm provides the software stack for AMD GPU programming and AI framework execution. Relevant components include:

- HIP runtime and HIPCC compiler path
- PyTorch ROCm backend
- rocBLAS for dense linear algebra
- MIOpen for deep learning primitives
- RCCL for multi-GPU communication
- MIGraphX for inference optimization paths
- RPP, MIVisionX, rocDecode, and rocJPEG for media/computer vision workflows
- `rocminfo`, `amd-smi`, and `rocprof` for validation, monitoring, and profiling

## MI300X and MI300A Research Highlights

| Accelerator | Public Technical Relevance |
|---|---|
| AMD Instinct MI300X | CDNA 3 accelerator with up to 192 GB HBM3, 5.3 TB/s peak theoretical memory bandwidth, 304 compute units, 1,216 matrix cores, and strong fit for large-scale inference |
| AMD Instinct MI300A | Integrated CPU-GPU APU with 24 Zen 4 CPU cores, 228 CDNA 3 GPU compute units, 912 matrix cores, 128 GB HBM3, and unified package design for tightly coupled AI/HPC workflows |

## Benchmark Overview

Benchmark files are provided as enterprise-style templates. Replace template values with measured results from the final AMD GPU environment before formal submission.

| Mode | Streams | Avg FPS | p50 Latency | p95 Latency | GPU Utilization | Notes |
|---|---:|---:|---:|---:|---:|---|
| CPU baseline | 4 | 18 | 142 ms | 231 ms | N/A | Reference only |
| AMD GPU FP32 | 8 | 96 | 41 ms | 68 ms | 52% | ROCm inference enabled |
| AMD GPU FP16/BF16 | 16 | 214 | 24 ms | 39 ms | 71% | Mixed precision path |
| AMD GPU optimized | 32 | 386 | 18 ms | 31 ms | 86% | Tuned batching and queues |

## Repository Structure

```text
SITA-Hermes-Agent-AMD/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── docs/
├── benchmarks/
├── rocm_setup/
├── configs/
├── deployment/
├── screenshots/
├── diagrams/
└── results/
```

## Installation Guide

```bash
git clone https://github.com/<your-org>/SITA-Hermes-Agent-AMD.git
cd SITA-Hermes-Agent-AMD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ROCm Setup

Use AMD's official ROCm documentation as the source of truth for supported operating systems, GPU support, and package versions. High-level workflow:

1. Confirm the target AMD GPU is ROCm-supported.
2. Install a ROCm-supported Linux distribution.
3. Install AMD GPU drivers and ROCm packages.
4. Validate GPU access with `rocminfo`.
5. Validate monitoring with `amd-smi`.
6. Install PyTorch ROCm using official AMD/PyTorch guidance.
7. Run benchmark templates and capture evidence.

## Hardware Requirements

Recommended:

- AMD Instinct MI300X or MI300A
- ROCm-supported Linux server
- 128 GB or more system memory for large-scale experiments
- NVMe storage for video/sample datasets and benchmark logs
- Docker or compatible container runtime

Minimum documentation validation:

- Any ROCm-supported AMD GPU
- Linux environment
- Python 3.10+
- PyTorch ROCm package or ROCm PyTorch container

## Reproducibility Workflow

```text
Clone repository
  -> Install ROCm
  -> Validate AMD GPU visibility
  -> Install PyTorch ROCm
  -> Configure benchmark YAML
  -> Run benchmark workflow
  -> Capture FPS, latency, utilization, throughput, memory
  -> Add screenshots and logs
  -> Update results summaries
```

## Future Scope

- Verified MI300X benchmark execution
- Verified MI300A unified memory workflow evaluation
- ROCm profiler evidence package
- MIGraphX inference optimization experiments
- Multi-GPU inference scale-out evaluation
- Kubernetes deployment manifests for AMD GPU scheduling
- Sanitized dashboard screenshots

## References

See [docs/references.md](docs/references.md) for primary AMD and ROCm sources.
