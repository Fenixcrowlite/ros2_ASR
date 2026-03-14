# Testing Implementation Report

## What Was Found
- Test suite existed but was architecture-misaligned and partially broken at collection time.
- Legacy `web_gui` coverage and new `web_ui + asr_gateway` coverage were not separated.
- No structured contract/API/E2E layers were in place for the new ROS2-first ASR platform baseline.

## What Was Implemented
- Restored pytest bootstrap by adding repository root to `sys.path`.
- Added marker taxonomy for `unit/component/contract/api/gui/e2e/integration/regression/legacy`.
- Updated CI fast suite to exclude `legacy/e2e/slow/cloud/ros`.
- Added deterministic fake provider and fake gateway backend harness.
- Added temp project-root strategy for gateway/API/UI tests.
- Added new tests for:
  - config resolution and override precedence
  - secret refs and masking
  - metric engine including `sample_accuracy`
  - artifact store and run ID uniqueness
  - dataset manifest validation with duplicate detection
  - normalized result contract
  - provider manager
  - benchmark orchestrator artifact persistence
  - provider adapter contracts (`whisper`, `azure`)
  - gateway API contracts
  - gateway runtime/benchmark/results/logs/secrets endpoints
  - GUI shell/asset serving
  - browser E2E runtime and benchmark flows
  - CLI validation/import/export flows
  - artifact layout regression

## Testability Improvements Applied
- `ArtifactStore.build_run_id()` now adds a UUID suffix to avoid collisions.
- Dataset manifest loader now rejects duplicate `sample_id` values and malformed JSON lines explicitly.
- Metric plugin baseline now includes `sample_accuracy`, matching existing metric profiles.
- Runtime audio pipeline now has regression coverage for truthful stream metadata:
  - preprocess preserves effective output format on terminal chunks
  - VAD flush preserves segment sample-rate metadata instead of trusting the last empty marker
- Metric normalization now strips punctuation/symbol noise in WER/CER baseline comparisons, preventing false regressions such as `Zero.` vs `zero`.

## Coverage Status

### Fully Covered In Baseline
- Config merge/inheritance precedence
- Secret-ref resolution and masking
- Benchmark artifact persistence shape
- Provider adapter normalization contract
- Gateway HTTP contract and main operator flows
- GUI runtime/benchmark/results/diagnostics baseline flows
- CLI config validation / dataset import / report export
- Runtime audio metadata regression points that previously broke honest Whisper execution on file input

### Partially Covered
- ROS graph interactions
- lifecycle/action/service behavior across real launched nodes
- real cloud-provider networking failures
- advanced GUI human-behavior edge cases (reload/back-button/concurrent navigation)

### Future Work
- Dedicated `ros` suite for launch/service/action/topic assertions on the new runtime nodes
- real browser tests for provider setup and dataset import workflows
- extended failure matrix for quota/rate-limit/network-loss and corrupted artifacts
- nightly cloud validation with managed credentials
