# FPS Results

## Purpose

This file records frames-per-second measurements for public AMD GPU inference evaluation.

## Template Results

| Scenario | Streams | Resolution | Precision | Avg FPS | Notes |
|---|---:|---|---|---:|---|
| CPU baseline | 4 | 1080p | FP32 | 18 | Reference baseline |
| AMD GPU baseline | 8 | 1080p | FP32 | 96 | ROCm inference enabled |
| AMD GPU mixed precision | 16 | 1080p | FP16/BF16 | 214 | Optimized tensor execution |
| AMD GPU optimized batch | 32 | 1080p | FP16/BF16 | 386 | Tuned batch-window configuration |

## Submission Note

Replace template values with measured results from AMD GPU hardware.
