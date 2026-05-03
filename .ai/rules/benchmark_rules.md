# Benchmark Rules

- Run dataset validation before final benchmark export.
- Preserve canonical benchmark artifacts under `artifacts/benchmark_runs/<run_id>/`.
- Final thesis tables must be regenerated from repository-present artifacts.
- Use `end_to_end_rtf` as the primary real-time factor.
- Treat `provider_compute_rtf` as a secondary provider-side metric.
- Treat `real_time_factor` as a deprecated compatibility alias.
- Exclude mock, fake, dummy, and synthetic providers from final benchmark result tables.
- Record skipped providers and exact skip reasons.

