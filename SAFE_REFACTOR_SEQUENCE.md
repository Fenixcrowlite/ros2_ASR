# Safe Refactor Sequence

1. Keep canonical core stable:
   - `asr_provider_base`
   - `asr_runtime_nodes`
   - `asr_benchmark_core`
   - `asr_gateway`
2. Move remaining operator entrypoints to canonical profiles/artifacts.
3. Mark legacy packages/configs explicitly in-place.
4. Rebase transitional scripts (`live_sample_eval.py`, old demos) on canonical providers where feasible.
5. Only after the above, consider moving old packages under `legacy/`.
