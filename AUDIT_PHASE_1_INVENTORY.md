# Audit Phase 1 Inventory

Date: 2026-03-30

## Repository Scope

- Source workspace: `ros2_ws/src`
- Configuration root: `configs/`
- Data and manifests: `datasets/`, `data/`
- Gateway/UI: `web_ui/`, `ros2_ws/src/asr_gateway`
- Runtime artifacts: `artifacts/`, `logs/`, `results/`
- Docs and diagrams: `docs/`, `docs/arch/`

## Canonical Platform Modules

| Area | Canonical modules | Notes |
|---|---|---|
| Runtime | `asr_runtime_nodes`, `asr_provider_base`, `asr_provider_*`, `asr_storage` | New ROS2-first runtime path |
| Benchmark | `asr_benchmark_core`, `asr_benchmark_nodes`, `asr_metrics`, `asr_reporting`, `asr_datasets` | New reproducible benchmark path |
| Config and contracts | `asr_config`, `asr_interfaces`, `asr_core` | Shared schemas, config resolution, normalized models |
| Gateway/UI | `asr_gateway`, `web_ui` | HTTP control plane and browser UI |
| Launch | `asr_launch` | Canonical stack bring-up |

## Compatibility / Legacy Modules

| Module | Status | Reason |
|---|---|---|
| `asr_ros` | compatibility-only | Old monolithic runtime service/action node |
| `asr_benchmark` | compatibility-only | Old flat benchmark runner |
| `asr_backend_*` | internal compatibility substrate | Old backend abstraction retained under new provider adapters |
| `configs/default.yaml` | compatibility-only | Consumed by old backend-centric path, not by provider-profile runtime |
| `scripts/run_benchmark_core.py` | canonical operator bridge | Direct CLI wrapper over `BenchmarkOrchestrator` with compatibility export |
| `scripts/run_benchmarks.sh` | canonical operator wrapper | Builds/sources workspace and invokes `run_benchmark_core.py` |
| `scripts/generate_report.py` | bridge utility | Accepts canonical `summary.json` and legacy flat JSON inputs |

## Derived / Generated Areas

These are not source-of-truth modules and should stay operationally separate:

- `configs/resolved/`
- `artifacts/benchmark_runs/`
- `artifacts/runtime_sessions/`
- `logs/`
- `results/`
- `docs/arch/*.json`
- `ros2_ws/build`, `ros2_ws/install`, `ros2_ws/log`

## Entry Points

### Launch files

- Canonical runtime: `ros2_ws/src/asr_launch/launch/runtime_minimal.launch.py`
- Canonical runtime + gateway: `ros2_ws/src/asr_launch/launch/gateway_with_runtime.launch.py`
- Canonical full stack: `ros2_ws/src/asr_launch/launch/full_stack_dev.launch.py`
- Canonical benchmark ROS shell: `ros2_ws/src/asr_launch/launch/benchmark_matrix.launch.py`
- Compatibility launch files: `ros2_ws/src/asr_ros/launch/*.launch.py`, `ros2_ws/src/asr_benchmark/launch/benchmark.launch.py`

### Console scripts

- `asr_gateway_server`
- `audio_input_node`
- `audio_preprocess_node`
- `vad_segmenter_node`
- `asr_orchestrator_node`
- `benchmark_manager_node`
- Compatibility: `asr_benchmark_node`, `asr_benchmark_runner`, `asr_server_node`, `audio_capture_node`, `asr_text_output_node`

## High-Level Findings

1. The repository contains two simultaneous architectures: a newer modular provider-profile platform and an older backend-centric compatibility stack.
2. The new stack is functionally richer and more coherent, but legacy scripts and old benchmark/runtime surfaces still create ambiguity about what is canonical.
3. Config/profile coverage is good in shape, but some fields were decorative before repair:
   - provider `adapter`
   - benchmark `execution_mode`
   - deployment-scoped benchmark defaults
   - `runtime_minimal.launch.py` profile fidelity
4. Metric logic is substantially cleaner in the canonical benchmark path than in the old flat benchmark path.
5. The strongest source of architectural noise is not dead code inside modules, but coexistence of:
   - canonical platform path
   - compatibility runtime path
   - retained compatibility benchmark package/CLI
   - generated artifacts checked into the working tree as examples/reference outputs
6. The default operator benchmark flow is now aligned with the canonical benchmark core; the old flat runner remains only as an explicit compatibility path.

See also:

- `MODULE_CLASSIFICATION_MATRIX.csv`
- `AUDIT_PHASE_2_DATAFLOW.md`
- `BROKEN_OR_FAKE_PATHS.md`
