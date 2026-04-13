# asr_benchmark_core

Benchmark orchestration core.

## Responsibilities
- Resolve benchmark/dataset/provider/metric profiles.
- Execute provider x sample matrix.
- Compute metrics via plugin engine.
- Persist reproducible run artifacts and summary.
- Generate deterministic noise-robustness variants for benchmark runs.

## Boundaries
- No GUI/API exposure (use `asr_benchmark_nodes` / `asr_gateway`).

## Noise Robustness Model
- Keep `clean_baseline` as the control condition.
- Use named severity tiers mapped to SNR: `light=30 dB`, `medium=20 dB`, `heavy=10 dB`, `extreme=0 dB`.
- Separate noise family from severity. The current synthetic families are `white`, `pink`, `brown`, `babble`, and `hum`.
- Keep augmentation deterministic through a fixed seed so repeated benchmark runs stay reproducible.

This keeps the project aligned with common ASR robustness practice: compare a clean reference against progressively harsher corruptions and vary both the spectral character of the noise and its SNR.

## Read This Package In This Order
1. `asr_benchmark_core/orchestrator.py`
2. `asr_benchmark_core/executor.py`
3. `asr_benchmark_core/noise.py`
4. `asr_benchmark_core/scenarios.py`

Read it in that order because the orchestrator owns the run plan, the executor owns one concrete sample/provider execution, and `noise.py` is only a supporting augmentation layer.
