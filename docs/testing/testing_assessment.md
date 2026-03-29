# Testing Assessment

## Current State
- Repository already contains a meaningful but uneven test base.
- Existing coverage is concentrated in `tests/unit/` plus gateway/UI API flows.
- A single ROS-marked integration test still targets legacy `asr_ros` service flow.
- CI currently runs one broad pytest command and previously failed during collection because repository root was not on `PYTHONPATH`.

## Main Gaps Found
- Test structure did not match the new architecture baseline (`asr_config`, `asr_storage`, `asr_gateway`, benchmark packages, new `web_ui`).
- Legacy and current-platform tests were mixed without explicit markers or execution policy.
- No coherent contract-test layer for provider adapters, normalized results, dataset manifests, or gateway API responses.
- No browser-driven user-flow validation for the new GUI.
- No dedicated regression suite for benchmark artifact layout and reproducibility.
- CLI/manual engineering flows were undocumented and untested.

## High-Risk Areas
- Config resolution and override precedence.
- Provider adapter normalization and fallback behavior.
- Artifact persistence completeness and run/session identifier uniqueness.
- Gateway API contracts and GUI/backend coupling.
- Benchmark reproducibility across manifests, metric profiles, and stored summaries.

## Testability Constraints
- ROS runtime and gateway interface layers are still evolving; full ROS graph/system tests need tighter stabilization.
- Cloud providers cannot be required in CI, so deterministic fakes are necessary.
- GUI requires a real browser to validate flows meaningfully; static HTML checks alone are insufficient.

## Priorities Applied
1. Restore reliable pytest bootstrap and execution segmentation.
2. Cover critical architecture contracts: config, provider, normalized result, storage, benchmark artifacts, gateway API.
3. Add backend API and browser-driven GUI user-flow tests over deterministic fake backends.
4. Add CLI/manual-flow tests for engineering workflows.
5. Document fast vs extended execution policy.
