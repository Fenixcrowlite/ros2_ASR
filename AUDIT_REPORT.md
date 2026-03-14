# AUDIT_REPORT

## Executive summary
- Audit window: 2026-03-11 .. 2026-03-12.
- Scope executed: full repo inventory, static checks, unit/ROS/colcon tests, benchmark/report/release flows, cloud-auth log forensics, targeted fault injection, ROS stop-cycle runtime checks.
- Outcome: project reached a more stable checkpoint with hardened cloud auth, deterministic benchmark behavior, corrected ROS shutdown lifecycle, and reduced disruptive background side effects.

## Current architecture overview
- Core contract: `ros2_ws/src/asr_core/asr_core/{models.py,backend.py,factory.py}`.
- Backends: `mock/vosk/whisper/google/aws/azure` under `ros2_ws/src/asr_backend_*`.
- ROS runtime: `asr_server_node`, `audio_capture_node`, `asr_text_output_node` (`ros2_ws/src/asr_ros/asr_ros`).
- Benchmark/metrics: `ros2_ws/src/asr_benchmark`, `ros2_ws/src/asr_metrics`, `scripts/generate_report.py`.
- Web control plane: `web_gui/app/*` + `web_gui/static/*`; runtime artifacts in `web_gui/runtime_configs`, `web_gui/logs`, `web_gui/runtime_aws`.
- Entry points: ROS package console scripts, `web_gui/app/__main__.py`, top-level `scripts/*.sh`.

## What was checked
- Repo/package metadata: `README.md`, `Makefile`, `pyproject.toml`, `requirements.txt`, ROS `package.xml/setup.py/setup.cfg/CMakeLists.txt`.
- Runtime logs: `web_gui/logs/*.log`, `web_gui/logs/jobs_state.json`, `log/latest*`.
- Cloud auth path: `web_gui/app/main.py`, `aws_auth_store.py`, `config_builder.py`, frontend auth triggers.
- ROS shutdown behavior in node `main()` paths + stop behavior in launch runs.
- Benchmark reproducibility path: dataset resolution + scenarios normalization.
- Security/static quality: `ruff`, `mypy`, `bandit`.

## Critical issues
- None remaining in audited scope after remediation.

## Major issues
1. Repeated ROS stop traces showed `RCLError: failed to shutdown: rcl_shutdown already called` across bringup nodes.
2. AWS cloud auth preflight produced opaque errors for SSO edge failures and depended on CLI-only execution path.
3. Google credential validation only checked file existence, not JSON integrity.
4. Colcon desktop notifications were still emitted in build/test flows, causing unwanted desktop wakeups during background activity.
5. Concurrent `colcon` invocations (`build/test/demo/bench`) could race on shared `build/install/log` and cause non-deterministic failures.
6. Web GUI required repeated manual re-entry of non-secret runtime fields after restart, reducing demo/operator UX stability.
7. Historical inactive jobs from previous GUI sessions polluted the primary jobs table and reduced operator focus.
8. Repeated AWS job starts triggered identical STS preflight checks each time, adding avoidable latency.

## Minor issues
1. `JobManager.stop_job()` previously suppressed wait-timeout context (already fixed earlier in this audit series).
2. Historical logs contain pre-fix errors and can confuse operators if interpreted as current runtime status.

## Risks not fixed
- Real cloud E2E (`google/aws/azure`) still depends on live credentials/network and cannot be fully exercised in default CI.
- `bandit` findings remain mostly low-severity subprocess/test-pattern warnings in tooling-heavy modules.
- `shellcheck` was unavailable in this environment, so shell linting stayed manual.

## What was fixed
- ROS lifecycle hardening:
  - Added `ros2_ws/src/asr_ros/asr_ros/shutdown.py` (`safe_shutdown_node`).
  - Updated `asr_server_node.py`, `audio_capture_node.py`, `asr_text_output_node.py` to use context-safe shutdown and handle `ExternalShutdownException`.
- Cloud auth hardening (`web_gui/app/main.py`):
  - AWS STS preflight now uses boto3-first path with short network timeouts; CLI fallback remains when boto3 is unavailable.
  - Added normalization of common AWS SSO/token errors to actionable user-facing messages.
  - Added short in-memory cache for successful AWS STS preflight checks (default 120s, configurable).
  - Added Google credential JSON structure/readability validation (not only path existence).
- Screen wake/notification hardening:
  - Disabled colcon desktop notifications by default via `COLCON_EXTENSION_BLOCKLIST=colcon_core.event_handler.desktop_notification` in `Makefile` and `scripts/source_runtime_env.sh`.
- Colcon concurrency hardening:
  - Added `scripts/with_colcon_lock.sh` (shared `flock`-based lock wrapper).
  - Routed `colcon` calls in `Makefile`, `scripts/run_demo.sh`, `scripts/run_benchmarks.sh`, `scripts/open_live_test_terminals.sh` through lock wrapper.
- Web GUI operator UX hardening:
  - Added local draft persistence for non-secret form data in `web_gui/static/app.js` (`localStorage` snapshot + restore on startup).
  - Added split jobs view: active/current jobs stay in main table, inactive restored jobs move to collapsible dropdown.
  - Explicitly excluded secret inputs from draft persistence (`AWS access/secret/session`, `Azure key`, raw AWS auth text).
- Previously completed in same audit pass (retained):
  - manifest-first dataset relative path resolution;
  - strict benchmark scenario normalization/validation;
  - cloud target selection precedence for explicit GUI runs;
  - stop timeout observability in job manager;
  - safe `make clean` scope and coverage artifact ignore rules.

## What tests were added
- `tests/unit/test_ros_shutdown.py`:
  - normal destroy+shutdown path;
  - suppression of known double-shutdown runtime error;
  - propagation of unexpected runtime errors.
- `tests/unit/web_gui/test_main_runtime_auth.py`:
  - Google invalid-JSON credential file rejection;
  - AWS STS preflight fallback to CLI when boto3 path is unavailable;
  - AWS auth error normalization regression;
  - AWS STS preflight cache behavior (enabled/disabled TTL).
- Existing new tests from earlier audit steps remain active:
  - benchmark scenario normalization/invalid labels;
  - manifest-vs-cwd dataset resolution;
  - explicit cloud target auth selection;
  - job stop wait-timeout persistence.
- `tests/unit/test_colcon_locking.py`:
  - lock-wrapper executable presence;
  - Makefile/runtime scripts use lock-wrapper for all `colcon` build/test calls.
- `tests/unit/web_gui/test_job_manager.py`:
  - active restored jobs remain visible when `hide_inactive_restored=true` (only inactive restored are hidden).

## What scenarios were validated
- Static:
  - `make lint` (ruff + mypy): PASS.
  - `bandit -q -r ...`: PASS with findings (29 Low, 1 Medium, 0 High).
- Tests:
  - `make test-unit`: PASS.
  - `make test-ros`: PASS.
  - `make test-colcon`: PASS.
- Runtime/release:
  - `make build`: PASS.
  - `make bench`: PASS (`30/30 successful`).
  - `make report`: PASS.
  - `bash scripts/release_check.sh`: PASS.
- Fault-injection/runtime checks:
  - AWS/Google auth negative cases via unit/API tests: PASS.
  - Manual bringup interrupt check (`timeout --signal=INT ros2 launch ...`): no `rcl_shutdown already called` tracebacks after fix.
  - Verified colcon logs no longer emit `Sending desktop notification using 'notify2'` in latest runs.
  - Reproduced interference risk by overlapping ROS test targets (shared workspace race), then re-validated sequential and lock-protected flows: PASS.

## Remaining recommendations
1. Add a dedicated launch-cycle regression test (`N` start/stop loops) to enforce no shutdown tracebacks over time.
2. Add CI shell lint stage (`shellcheck`) once tool is available.
3. Add documented `.bandit` policy file with justified ignores for known-safe subprocess paths.
4. Extend cloud auth contract tests for additional boto3/STS network failure permutations.
5. Add frontend E2E/browser test to verify draft restore behavior and secret-field exclusion.
