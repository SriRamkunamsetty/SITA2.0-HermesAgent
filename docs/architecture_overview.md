# Architecture Overview

This document describes the public, patent-safe infrastructure architecture.

## Public Pipeline

```text
Input Streams
  -> Frame Intake
  -> GPU-Ready Queue
  -> ROCm Inference Layer
  -> Object Intelligence Outputs
  -> Analytics Metadata
  -> Evidence and Reporting Layer
```

## AMD Acceleration Boundary

AMD GPUs accelerate tensor inference and selected analytics workloads. The repository discusses only public infrastructure components:

- AMD GPU hardware
- ROCm runtime
- PyTorch ROCm model execution
- HIP portability layer
- Monitoring and profiling tools
- Benchmark workflow

## Omitted Details

The following are not disclosed:

- Proprietary orchestration layer
- Secret scheduling logic
- Confidential architecture components
- Internal optimization modules
- Patent-sensitive workflow decisions

## Enterprise Deployment View

```text
GitHub Repository
  -> ROCm Environment
  -> AMD GPU Node
  -> Benchmark Execution
  -> Metrics Collection
  -> Review Evidence
```
