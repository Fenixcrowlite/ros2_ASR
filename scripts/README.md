# scripts

Task-focused helpers for local development and benchmark runs.

- `setup_env.sh` creates the local Python environment.
- `run_web_ui.sh` starts the gateway-first web UI stack.
- `run_benchmarks.sh` and `run_benchmark_core.py` run benchmark profiles.
- `run_benchmark_suite.sh` exports schema-first benchmark metrics.
- `collect_metrics.py` builds derived CSV/JSON/plot outputs from run artifacts.
- `generate_report.py` writes Markdown summaries from benchmark JSON.
- `run_huggingface_smoke.py` runs direct Hugging Face provider smoke checks.
- `run_provider_smoke_tests.py` checks configured provider availability.
- `import_dataset/` contains dataset ingestion helpers.
- `validate_configs/` contains profile validation helpers.
- `export_reports/` contains report/export helpers.
- `maintenance/` contains cleanup and model setup helpers.

Recommended top-level entrypoints:

- `make up`
- `make up-runtime`
- `make down`
- `make bench`
- `make bench-suite`
- `make hf-smoke-local`
- `make hf-smoke-api`
- `make bench-hf`
