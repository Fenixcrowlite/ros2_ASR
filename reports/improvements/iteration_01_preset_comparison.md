# Iteration 01: Whisper Preset Comparison

| Preset | Samples | Success | Mean WER | Mean CER | Mean Latency ms | Mean RTF | Mean CPU % | Mean RAM MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| light | 1 | 1 | 0.0000 | 0.0000 | 3055.12 | 0.3677 | 6.30 | 269.38 |
| balanced | 1 | 1 | 0.0000 | 0.0000 | 1701.72 | 0.2048 | 7.50 | 370.65 |
| accurate | 1 | 1 | 0.3333 | 0.0667 | 4382.00 | 0.5274 | 6.00 | 748.81 |

- Lowest latency preset: `balanced` at `1701.72` ms
- Lowest WER preset: `light` at `0.0000`
