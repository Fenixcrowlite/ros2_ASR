# scripts

Task-focused scripts:

- `run_web_ui.sh` launch new gateway-first web UI stack (`asr_launch` + `asr_gateway` + `web_ui`)
- `run_huggingface_smoke.py` instantiate a provider profile through the unified adapter and emit transcript + metrics JSON
- `import_dataset/` dataset ingestion helpers
- `validate_configs/` profile validation helpers
- `export_reports/` report/export helpers
- `maintenance/` cleanup and maintenance helpers

Recommended top-level entrypoints:

- `make up` build and start the full web UI stack
- `make up-runtime` build and start the minimal ROS2 runtime
- `make down` stop the managed web UI stack
- `make hf-smoke-local` run direct Hugging Face local smoke validation
- `make hf-smoke-api` run direct Hugging Face API smoke validation
- `make bench-hf` run the Hugging Face benchmark matrix
