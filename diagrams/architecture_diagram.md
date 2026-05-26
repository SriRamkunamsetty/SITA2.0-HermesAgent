# Architecture Diagram

```text
┌──────────────────────────┐
│ Public Input Streams     │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Public Processing Layer  │
│ confidential internals   │
│ omitted                  │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ AMD ROCm Inference Layer │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ AMD Instinct GPU         │
│ MI300X / MI300A          │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Public Analytics Output  │
└──────────────────────────┘
```
