# Canonical Vs Legacy

Audit date: `2026-03-31`

## Decision

Default developer and CI workflows now target the canonical stack only.

Legacy packages remain in-tree for compatibility auditing, but they are no longer part of normal `make build`, `make test-unit`, `make test-ros`, `make test-colcon`, `scripts/run_demo.sh`, or `scripts/run_benchmarks.sh`.

Selected enforcement strategy: `C) exclude legacy from default build/test entrypoints`.

Reason:

- lowest-risk change that preserves the legacy code for manual compatibility review
- avoids destructive moves or `COLCON_IGNORE` files in the same pass
- keeps public canonical ROS interfaces stable while preventing accidental default use of `asr_ros` and `asr_benchmark`

## Classification Matrix: Packages

| Surface | Classification | Evidence | Default workflow status |
|---|---|---|---|
| `asr_runtime_nodes` | `CANONICAL` | Owns canonical runtime topics/services in `asr_orchestrator_node.py`, `audio_input_node.py`, `audio_preprocess_node.py`, `vad_segmenter_node.py` | Included |
| `asr_provider_whisper`, `asr_provider_vosk`, `asr_provider_google`, `asr_provider_aws`, `asr_provider_azure` | `CANONICAL` | Provider adapters used by orchestrator and benchmark core | Included |
| `asr_benchmark_core` | `CANONICAL` | Source-of-truth run planner/executor in `orchestrator.py` and `executor.py` | Included |
| `asr_benchmark_nodes` | `CANONICAL` | ROS benchmark action/service shell around benchmark core | Included |
| `asr_gateway` | `CANONICAL` | FastAPI/UI gateway and ROS bridge | Included |
| `asr_launch` | `CANONICAL` | Canonical launch entrypoints for runtime/gateway/benchmark stacks | Included |
| `asr_config` | `CANONICAL` | Profile resolution and snapshotting | Included |
| `asr_metrics` / `asr_observability` | `CANONICAL` | Canonical metrics and trace namespace | Included |
| `asr_storage` | `CANONICAL` | Artifact storage layout for runtime and benchmark runs | Included |
| `asr_datasets` | `CANONICAL` | Canonical dataset registry and JSONL manifest loader | Included |
| `asr_interfaces` | `CANONICAL` | Canonical ROS messages/services/actions | Included |
| `asr_core`, `asr_provider_base`, `asr_reporting`, `asr_backend_*` | `INTERNAL SUPPORT` | Shared utilities, provider manager, report helpers, backend implementation details | Included only as dependencies |
| `asr_ros` | `LEGACY` | `ros2_ws/src/asr_ros/README.md` explicitly marks it legacy; overlaps runtime services/actions/topics | Excluded by default |
| `asr_benchmark` | `LEGACY` | Duplicates benchmark path; legacy CSV manifest loader uses `Path.cwd()` fallback | Excluded by default |

## Classification Matrix: Launches and Scripts

| Surface | Classification | Evidence | Default workflow status |
|---|---|---|---|
| `ros2_ws/src/asr_launch/launch/runtime_minimal.launch.py` | `CANONICAL` | Used by `scripts/run_demo.sh` | Included |
| `ros2_ws/src/asr_launch/launch/runtime_streaming.launch.py` | `CANONICAL` | Used by runtime streaming/dev tooling | Included |
| `ros2_ws/src/asr_launch/launch/gateway_with_runtime.launch.py` | `CANONICAL` | Used by `scripts/run_web_ui.sh --stack runtime` | Included |
| `ros2_ws/src/asr_launch/launch/full_stack_dev.launch.py` | `CANONICAL` | Used by `scripts/run_web_ui.sh --stack full` | Included |
| `ros2_ws/src/asr_launch/launch/benchmark_single_provider.launch.py` | `CANONICAL` | Canonical benchmark launch | Included |
| `ros2_ws/src/asr_launch/launch/benchmark_matrix.launch.py` | `CANONICAL` | Canonical matrix benchmark launch | Included |
| `scripts/run_demo.sh` | `CANONICAL` | Now builds with `--packages-skip asr_ros asr_benchmark` and launches `asr_launch/runtime_minimal.launch.py` | Included |
| `scripts/run_benchmarks.sh` | `CANONICAL` | Now builds with `--packages-skip asr_ros asr_benchmark` and runs `run_benchmark_core.py` | Included |
| `scripts/run_web_ui.sh` | `CANONICAL` | Launches canonical `asr_launch/*` stacks only | Included |
| `ros2_ws/src/asr_ros/launch/bringup.launch.py`, `demo.launch.py`, `benchmark.launch.py` | `LEGACY` | Legacy package and contracts | Excluded from defaults |
| `docs/wiki/02_ROS2/*`, older interface docs | `UNKNOWN / NEEDS REVIEW` | Several pages still document legacy topics/actions without a canonical/legacy banner | Not a build surface, but documentation risk remains |

## Enforcement Implemented In This Pass

- `Makefile`
  - `build`, `test-ros`, and `test-colcon` now pass `--packages-skip asr_ros asr_benchmark`
  - `test-unit` now excludes `legacy`-marked tests
  - new explicit opt-in target: `make build-legacy`
- `scripts/run_demo.sh`
  - default `colcon build` now skips `asr_ros` and `asr_benchmark`
- `scripts/run_benchmarks.sh`
  - default `colcon build` now skips `asr_ros` and `asr_benchmark`
- tests
  - legacy runtime/benchmark tests are explicitly marked `pytest.mark.legacy`
  - canonical ROS test selection excludes the legacy `asr_ros` recognize-once integration test
- documentation
  - `README.md` now states that default developer flows are canonical-only
- CI
  - `.github/workflows/ci.yml` step names now explicitly call the default ROS build/test path canonical

## Verification

Executed after the enforcement patch:

- `make build`
  - result: success
  - evidence: `Summary: 24 packages finished`
  - implication: legacy packages `asr_ros` and `asr_benchmark` were not part of the default `colcon` graph
- `make test-unit`
  - result: success
  - implication: legacy-marked tests no longer ride along in the default fast suite
- `make test-ros`
  - result: success
  - implication: canonical ROS integration path still works after excluding legacy package builds and tests
- `make test-colcon`
  - result: success
  - implication: default ROS-aware colcon validation now runs against the canonical package set only

## Residual Risks

| Residual issue | Impact | Required follow-up |
|---|---|---|
| `PYTHONPATH` helper in `Makefile` still includes legacy source directories | A new canonical test could accidentally import legacy modules and still pass locally | Split canonical vs legacy Python source paths in a later patch set. |
| Legacy packages remain physically inside `ros2_ws/src` | Manual `colcon build` without project wrappers can still build them | Consider a later `build-all`/`legacy-only` workflow plus stronger contributor guidance, or eventually move legacy packages behind an explicit compatibility workspace. |
| Legacy docs still exist without full canonical banners | Human users can still follow the wrong launch/service docs | Audit `docs/wiki` and interface docs for canonical/legacy labeling. |

## Recommended Developer Workflow

- canonical default:
  - `make build`
  - `make test-unit`
  - `make test-ros`
  - `make test-colcon`
  - `bash scripts/run_demo.sh`
  - `bash scripts/run_benchmarks.sh`
- explicit legacy compatibility review:
  - `make build-legacy`
  - manual `pytest -m legacy`
  - manual `colcon ... --packages-select asr_ros asr_benchmark ...`
