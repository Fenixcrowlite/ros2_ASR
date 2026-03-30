# Broken Or Fake Paths

| Path / Surface | Problem | Observed Effect | State After Audit |
|---|---|---|---|
| `configs/providers/*.yaml::adapter` | Declared but ignored by provider creation | Profile looked extensible but runtime used only hardcoded registry | repaired |
| `configs/benchmark/*.yaml::execution_mode` | Declared but benchmark core seeded execution mode only from request overrides | Streaming benchmark profile setting could silently do nothing | repaired |
| `configs/deployment/dev_local.yaml::benchmark_defaults` | Present but not applied to benchmark profile resolution | Deployment defaults were decorative | repaired |
| `runtime_minimal.launch.py` | Hardcoded `input_mode`, `file_path`, `chunk_ms` | Runtime profile audio settings were shadowed | repaired |
| `asr_metrics.quality` empty-reference fallback | Helper fabricated denominator from hypothesis length | Pseudo-CER/WER on rows without valid reference | repaired semantically; invalid reference is now explicit |
| `configs/gui/default_gui.yaml` | Exists but gateway startup does not consume it | GUI profile creates false expectation of runtime effect | unresolved / legacy |
| `scripts/run_benchmarks.sh` | Previously invoked `asr_benchmark.runner` directly | Default operator bench path diverged from benchmark core | repaired |
| `scripts/generate_report.py` | Previously assumed only legacy flat benchmark JSON | `make report` could not explain canonical benchmark summaries | repaired |
| `asr_ros` runtime services | Still executable and discoverable | Users can confuse compatibility stack with canonical stack | retained as legacy |
| `asr_benchmark` package | Still executable and produces flat results | Duplicates benchmark surface with weaker architecture | retained as legacy |
| `configs/default.yaml` | Old backend-centric config still present | Parallel config system increases ambiguity | retained as legacy |
| `results/benchmark_results.*` | Compatibility export can be mistaken for source-of-truth artifacts | Users may ignore canonical run folders and summary pointer | acceptable compatibility shadow |
| `docs/arch/*.json` generated graphs | Contain both canonical and legacy paths | Architecture evidence is accurate but noisy | acceptable generated noise |
| `results/live_sample_smoke*` tracked outputs | Source tree contains sample result artifacts | Repo inventory is louder than necessary | documented as sample artifacts, not source |

## Practical Guidance

- Use `asr_launch`, `asr_runtime_nodes`, `asr_benchmark_core`, `asr_benchmark_nodes`, `asr_gateway`.
- Use `results/latest_benchmark_summary.json` or `artifacts/benchmark_runs/<run_id>/reports/summary.json` as the primary summary surface.
- Avoid new development against `asr_ros`, `asr_benchmark`, or `configs/default.yaml`.
- Treat `configs/gui/default_gui.yaml` as documentation-only until gateway bootstrap is wired to it.
