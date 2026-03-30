# Audit Phase 4 Configs / Profiles / Providers

## Canonical Config/Profile System

Canonical profile families:

- `runtime`
- `providers`
- `benchmark`
- `datasets`
- `metrics`
- `deployment`
- `gui`

Canonical loader:

- `ros2_ws/src/asr_config/asr_config/loader.py`

## Findings

### 1. Profile structure is good, but some fields were decorative

Before repair:

- provider `adapter` field was not used
- benchmark `execution_mode` could be declared in YAML but ignored by benchmark core
- deployment-scoped defaults such as `benchmark_defaults` existed but were not applied to target profiles

After repair:

- provider `adapter` is honored by `ProviderManager`
- benchmark `execution_mode` is seeded from profile and can still be overridden safely
- deployment-scoped defaults now participate in runtime/benchmark resolution

### 2. Runtime profiles are canonical

`configs/runtime/default_runtime.yaml` is the real runtime source of truth for:

- audio source and file path
- preprocessing policy
- VAD parameters
- orchestrator provider profile and processing mode
- session constraints

The `runtime_minimal.launch.py` path now respects that profile instead of shadowing it with hardcoded audio settings.

### 3. Provider profiles are canonical

`configs/providers/*.yaml` now genuinely control:

- provider family via `provider_id`
- concrete adapter implementation via `adapter`
- preset metadata and preset-specific settings merges
- credential reference file

### 4. Benchmark profiles are canonical

`configs/benchmark/*.yaml` now genuinely control:

- dataset profile selection
- provider profile selection
- metric profile selection
- execution mode
- artifact save toggles
- streaming/noise/batch controls

### 5. GUI profile is still decorative

`configs/gui/default_gui.yaml` is present but gateway bootstrap does not read:

- `gateway.host`
- `gateway.port`
- `gateway.enable_cors`
- `frontend.title`

This is still a live config pathology.

### 6. Legacy config path still exists

`configs/default.yaml` remains relevant only for:

- `asr_ros`
- old `asr_benchmark.runner`
- old backend-centric scripts

It is not the canonical runtime or benchmark control path anymore.

## Provider/Auth Findings

- `whisper_local` and `vosk_local` are honest local profiles.
- `google_cloud`, `aws_cloud`, `azure_cloud` are honest cloud profiles but remain credential- and network-dependent.
- There is no canonical `mock` provider profile in the provider-adapter world, which is good for honesty. Mock remains a legacy backend/testing aid.

## Repairs Performed

1. Applied scoped deployment defaults during profile resolution.
2. Activated provider `adapter` field.
3. Activated benchmark profile `execution_mode`.
4. Activated benchmark save flags for raw/normalized output persistence.
5. Added a benchmark-core CLI so operator benchmark execution now consumes canonical benchmark/provider/dataset profiles by default.

## Remaining Problems

- GUI profile still has no bootstrap effect.
- Legacy config path remains in compatibility packages and the old direct `asr_benchmark.runner` path.
- The repo still exposes both profile-driven and old backend-driven configuration mental models.

See also:

- `AUDIT_PROFILES_MATRIX.csv`
- `PROVIDER_INTEGRATION_STATUS.md`
- `CONFIGS_AND_PROFILES_REFACTOR.md`
