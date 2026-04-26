# Repository Assessment: ROS2 ASR Platform Baseline Migration

## 1. Current Repository State (as-is)

### 1.1 Existing ROS2 packages (`ros2_ws/src`)
- `asr_interfaces` (msg/srv/action): minimal ASR result + metrics + recognize/set/get status.
- `asr_core`: provider-agnostic dataclasses, backend abstraction, registry/factory, config/audio/language utilities.
- `asr_ros`: runtime ROS2 nodes (`asr_server_node`, `audio_capture_node`, `asr_text_output_node`) + bringup/demo launch files.
- `asr_benchmark`: benchmark runner + ROS wrapper node + dataset CSV loader + noise scenarios.
- `asr_metrics`: WER/CER/system metrics collector, record model, IO/plotting.
- Legacy provider packages:
  - `asr_backend_mock`
  - `asr_backend_whisper`
  - `asr_backend_vosk`
  - `asr_backend_google`
  - `asr_backend_azure`
  - `asr_backend_aws`

### 1.2 Existing GUI/web parts
- At assessment time, `web_gui/` contained FastAPI backend + static frontend.
- That GUI executed scripts/commands and managed runtime configs, but acted as mixed control plane with some business logic.
- Current state after migration: `web_gui/` has been removed; `web_ui/` + `asr_gateway` is the only active browser control plane.

### 1.3 Existing benchmark/testing parts
- Benchmark logic exists in `asr_benchmark` + `asr_metrics`.
- Unit and integration tests exist under `tests/` and package-level `test/` folders.

### 1.4 Existing provider integrations
- Working local: `mock`, `whisper`, `vosk`.
- Working cloud (credential-dependent): `google`, `azure`, `aws`.
- Integrations are functionally useful, but tied to legacy naming (`asr_backend_*`) and old contract.

### 1.5 Existing configs/data/artifacts
- `configs/*.yaml` (flat profile set, partially mixed concerns).
- `data/sample`, `data/transcripts` for sample audio and manifests.
- `results/` for benchmark outputs.
- Historical `web_gui/runtime_configs`, `web_gui/logs`, `web_gui/uploads` mixed runtime artifacts with app internals.
- Current state after cleanup: historical browser artifacts are archived only under canonical roots (`logs/gui/legacy_web_gui`, `artifacts/runtime_sessions/legacy_web_gui`, `data/sample/generated_noise/legacy_web_gui`).

## 2. Main Architectural Gaps vs Target Requirements

1. Runtime and benchmark are partially separated, but still coupled through flat config/model conventions.
2. Provider model is good baseline but not explicit capability-first adapter contract package.
3. No strict profile taxonomy (`runtime/providers/benchmark/datasets/metrics/deployment`) with clear precedence chain.
4. No dedicated secret reference model (`ref -> env/file`) with masked handling as first-class API.
5. Artifact storage model was not centralized (`results/`, historical `web_gui/*`, and ad-hoc outputs coexisted).
6. GUI/backend boundary is weak; GUI still carries orchestration logic and command composition.
7. ROS2 interface layer is too narrow for full runtime/benchmark/gateway lifecycle orchestration.
8. Package naming and responsibility boundaries do not match target modular baseline.

## 3. Reuse / Rewrite / Deprecate Map

### 3.1 Reuse directly
- `asr_core.audio` WAV/PCM utility logic.
- `asr_core.language` language normalization helpers.
- `asr_metrics.quality` WER/CER algorithms.
- Large portions of provider implementations in `asr_backend_whisper`, `asr_backend_vosk`, `asr_backend_google`, `asr_backend_azure`, `asr_backend_aws`.
- Existing benchmark execution flow from `asr_benchmark.runner` as a baseline for `asr_benchmark_core`.

### 3.2 Rewrite/Refactor
- `asr_interfaces`: extend to full runtime+benchmark contracts.
- `asr_core`: keep shared primitives; move provider abstraction to dedicated `asr_provider_base`.
- `asr_ros`: replace with new runtime node package `asr_runtime_nodes` and clearer pipeline roles.
- Config loading: replace flat loader with profile-driven `asr_config` and deterministic override chain.
- Benchmark: split orchestration core and ROS nodes (`asr_benchmark_core`, `asr_benchmark_nodes`).
- Web backend: move to `asr_gateway` API layer oriented around ROS/service/action + storage facade.

### 3.3 Deprecate (with migration notes)
- `asr_ros` as primary runtime stack.
- `asr_benchmark` as primary benchmark package.
- `asr_backend_*` naming scheme (kept temporarily for compatibility wrappers).
- Flat `configs/*.yaml` usage as only source of truth.
- historical `web_gui/` as architecture control plane.

## 4. Target Structure (high-level)

### 4.1 Target ROS2 package set
- `asr_interfaces`
- `asr_core`
- `asr_runtime_nodes`
- `asr_provider_base`
- `asr_provider_whisper`
- `asr_provider_vosk`
- `asr_provider_azure`
- `asr_provider_google`
- `asr_provider_aws`
- `asr_config`
- `asr_storage`
- `asr_datasets`
- `asr_metrics`
- `asr_benchmark_core`
- `asr_benchmark_nodes`
- `asr_reporting`
- `asr_gateway`
- `asr_launch`

### 4.2 Target top-level directories
- `configs/{runtime,providers,benchmark,datasets,metrics,deployment,gui,resolved}`
- `secrets/{refs,azure,google,aws,local}`
- `models/{whisper,vosk,cache}`
- `datasets/{registry,raw,imported,manifests,processed,noise_assets}`
- `artifacts/{runtime_sessions,benchmark_runs,comparisons,exports,temp}`
- `logs/{runtime,benchmark,gateway,gui}`
- `docs/{architecture,interfaces,profiles,experiments}`
- `web_ui/{frontend,backend}`
- `scripts/{import_dataset,validate_configs,export_reports,maintenance}`

## 5. Migration Strategy (summary)

1. Create architecture docs + migration plan before major code moves.
2. Introduce new packages while keeping legacy packages buildable during transition.
3. Port provider logic into new `asr_provider_*` adapters; keep old provider packages as compatibility layer if needed.
4. Implement new runtime pipeline in `asr_runtime_nodes` with normalized result contract.
5. Implement profile/secrets/artifacts core (`asr_config`, `asr_storage`) and move new launch files to use it.
6. Build benchmark core/nodes around reproducible run manifests and artifact persistence.
7. Introduce `asr_gateway` backend API and `web_ui` skeleton; remove legacy `web_gui` after parity.
   Status: completed.
8. Update docs and launch recipes; record deprecated modules and sunset path.

## 6. Risks and Controls

- Risk: breaking existing scripts/tests tied to `asr_ros` and `asr_benchmark`.
  - Control: keep compatibility wrappers and explicit deprecation docs.
- Risk: interface changes breaking old ROS clients.
  - Control: preserve old fields where possible; add new contracts in parallel.
- Risk: cloud credential handling regression.
  - Control: implement explicit secret reference schema + masked logs + examples.
- Risk: benchmark reproducibility drift.
  - Control: immutable run manifest snapshots + deterministic run_id + stored resolved configs.

## 7. Baseline Definition for this implementation cycle

This cycle delivers:
- Architectural package/directory baseline.
- Runtime vertical slice (audio input -> preprocess -> VAD segmentation -> orchestrator -> normalized result).
- One local provider working (`whisper`) + one cloud provider working via adapter contract (`azure`).
- Benchmark baseline with dataset import/registry + WER/CER/latency + reproducible run artifacts.
- Gateway backend baseline and initial `web_ui` skeleton.
- Mandatory architecture/migration documentation set.
