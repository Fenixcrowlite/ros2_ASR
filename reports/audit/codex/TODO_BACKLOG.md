# TODO_BACKLOG

## Architecture and migration
1. Decide the fate of `asr_ros`.
- Either retire it from the primary workspace path or isolate it as an explicit compatibility package with separate docs/tests.

2. Finish wiki migration.
- Update deeper `docs/wiki/02_ROS2`, `06_Operations`, and `99_Maps` pages that still describe `/asr/set_backend`, `/asr/get_status`, and `/asr/text/plain` as primary interfaces.

3. Decide whether to retire or redesign `scripts/live_sample_eval.py`.
- It still targets legacy `core|ros_service|ros_action` comparison flows around `asr_ros`.
- Either isolate it as an explicit compatibility tool or port it to the modular `/asr/runtime/*` control plane.

4. Decide whether `asr_ros` should remain in the default workspace build graph.
- The package is now much more honest, but it still duplicates concepts already covered by the modular runtime.
- If it stays, it should be clearly ring-fenced as compatibility-only.

## Type and style debt
5. Make `mypy` a real gate.
- Current residual: 172 errors in 18 files.
- Highest-value targets: `asr_gateway/ros_client.py`, `asr_gateway/result_views.py`, `asr_runtime_nodes/*`, and test fake/stub modules.

6. Reduce `ruff` noise to a reviewable level.
- Current residual: 301 findings, mostly `E501`.
- Without cleanup, lint output remains too noisy to serve as a regression signal.

## Testing
7. Add credentialed cloud E2E environment.
- Needed for real `aws/google/azure` runtime and benchmark validation.

8. Add shell linting to CI.
- `bash -n` is not enough; project needs `shellcheck`.

9. Extend ROS integration coverage to live session lifecycle.
- Current ROS integration covers one-shot services well enough.
- Missing stronger regression tests for `start_session -> results -> stop_session` across segmented/provider-stream modes.

## Interface cleanup
10. Clarify or rename `cloud_credentials_available`.
- The field is truthful now, but the name is awkward for local providers where credentials are not applicable.

11. Unify provider validation semantics across UI and runtime.
- Distinguish more clearly between “profile structurally valid” and “provider operationally ready with secrets/network”.

## Dependencies
12. Resolve browser dependency warnings.
- `websockets` deprecation warnings remain in e2e runs.

13. Decide whether `make bench` should keep using legacy `asr_benchmark.runner`.
- Current CLI/release benchmark entry still points to the legacy benchmark package.
- Either migrate `make bench` / `scripts/run_benchmarks.sh` onto `asr_benchmark_core` or ring-fence the old path explicitly as compatibility-only.

14. Split `archviz` runtime profiles into modern vs compatibility/legacy scopes.
- `make arch` currently uses the broad `full` profile, which is useful for maximum coverage but expensive and noisy.
- Consider a faster default profile for the modular stack and a separate compatibility profile for `asr_ros` / legacy benchmark launches.

15. Add end-to-end API coverage for uploaded dataset bundles.
- Current fixes for manifest-relative audio, duplicate normalized filenames, and missing bundle-local audio are covered at unit level.
- Add gateway/UI import-path integration tests so bundle validation is exercised through the real control plane.
