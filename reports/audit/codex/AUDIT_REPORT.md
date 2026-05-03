# AUDIT_REPORT

## Executive summary
- Audit baseline: 2026-03-25.
- Incremental update: 2026-03-26.
- Scope: full repository inventory, ROS2 package surface, scripts/docs/configs, static analysis, unit/ROS/colcon/runtime/release verification.
- Result: project is materially more stable and more honest about its actual architecture.
- Release-state evidence after fixes:
  - `pytest -q -m 'not ros and not cloud'`: PASS
  - `pytest -q -m ros tests/integration/test_ros_recognize_service.py`: PASS
  - `make test-colcon`: PASS
  - `bash scripts/release_check.sh`: PASS
  - `make report`: PASS
  - `make arch`: PASS
  - `make docsbot-detect && make docsbot-snapshot && make docsbot-generate && make docsbot-validate`: PASS
  - `bash scripts/secret_scan.sh`: PASS
  - `make dist`: PASS
  - runtime gateway smoke on `http://127.0.0.1:8088`: PASS
- Residual debt remains in `ruff`, `mypy`, cloud E2E, and legacy wiki coverage, but the operator path, release path, runtime control path, CLI helper surface, and documentation tooling path are now significantly cleaner and less misleading.

## Incremental audit update (2026-03-26)
- Dataset reproducibility and import integrity were tightened:
  - `asr_datasets/manifest.py` now resolves relative `audio_path` entries from the manifest location instead of the caller `cwd`
  - `asr_datasets/importer.py` now rejects duplicate uploaded filenames after basename normalization and rejects manifests that reference audio files not present in the uploaded bundle
- Runtime/gateway/tooling hardening was extended:
  - `asr_runtime_nodes/asr_orchestrator_node.py` and `audio_input_node.py` now use stricter numeric coercion and explicit active-provider guards in request/runtime paths
  - `asr_gateway/ros_client.py` now uses typed request builders and no longer swallows executor-shutdown failures silently
  - `asr_backend_aws/backend.py` now narrows cache-parse exception handling instead of catching arbitrary exceptions
- Architecture tooling safety improved:
  - `tools/archviz/static_extract.py` now requires `defusedxml` instead of falling back to the insecure stdlib XML parser
  - `tools/archviz/runtime_extract.py` now fails fast when another managed stack from the same workspace is already running, so `make arch` does not hang or mix unrelated runtime graph evidence
- Evidence gathered in this pass:
  - targeted `ruff` / `mypy` on changed modules: PASS
  - targeted `pytest` for datasets/runtime/gateway/archviz regressions: PASS
  - `make test-unit`: PASS
  - `make test-ros`: PASS
  - `make test-colcon`: PASS
  - `bash scripts/release_check.sh`: PASS
  - `make report`: PASS
  - `make arch-static`: PASS
  - `make arch` with an already-running managed stack: explicit fast failure with PID list, by design
  - `make docsbot-validate`: PASS
  - `find scripts -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n`: PASS

## Current architecture overview
- Primary runtime stack:
  - `ros2_ws/src/asr_runtime_nodes`
  - `ros2_ws/src/asr_launch`
  - `ros2_ws/src/asr_gateway`
  - `web_ui`
- Shared contracts:
  - `ros2_ws/src/asr_core`
  - `ros2_ws/src/asr_interfaces`
  - `ros2_ws/src/asr_config`
  - `ros2_ws/src/asr_storage`
- Provider layer:
  - `ros2_ws/src/asr_provider_base`
  - `ros2_ws/src/asr_provider_*`
- Benchmark/reporting layer:
  - `ros2_ws/src/asr_benchmark_core`
  - `ros2_ws/src/asr_benchmark_nodes`
  - `ros2_ws/src/asr_metrics`
  - `ros2_ws/src/asr_reporting`
- Compatibility surface still present:
  - `ros2_ws/src/asr_ros`
- Real user-facing control plane is now:
  - ROS services/topics under `/asr/runtime/*` and `/asr/status/*`
  - HTTP API under `asr_gateway`
  - browser UI served from `web_ui/frontend`

## What was checked
- Repository inventory:
  - root metadata: `README.md`, `Makefile`, `pyproject.toml`, `requirements.txt`
  - all ROS2 packages in `ros2_ws/src`
  - `scripts/`, `tests/`, `tools/`, `web_ui/`, `docs/`, `configs/`, `data/`, `results/`
- Architecture/runtime surface:
  - launch files in `ros2_ws/src/asr_launch/launch`
  - runtime services/topics in `asr_core/namespaces.py` and `asr_runtime_nodes`
  - gateway API + ROS bridge in `asr_gateway`
- Static analysis:
  - `ruff check . --statistics`
  - `mypy ros2_ws/src tests scripts tools/archviz`
  - `bandit -q -r ros2_ws/src scripts tools web_ui`
- Test/runtime/release:
  - unit suite
  - ROS integration suite
  - `colcon test`
  - benchmark flow
  - report generation
  - `release_check`
  - live gateway/runtime smoke

## Critical issues
1. `RecognizeOnce.srv` accepted `provider_profile`, but `asr_orchestrator_node` ignored it and always used the current runtime provider.
   - Impact: gateway/UI one-shot path could silently transcribe with the wrong backend/profile.
   - Evidence: code inspection in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py`.
   - Status: fixed and covered by unit + ROS integration tests.
2. Runtime status falsely reported `cloud_credentials_available=true` due to `not caps.requires_network or True`.
   - Impact: operator/gateway status lied about credential readiness.
   - Evidence: reproduced by code inspection in `_on_get_status`.
   - Status: fixed and covered by unit tests.
3. Whisper still exposed a fake provider-stream surface through buffered fallback code.
   - Impact: `provider_stream` looked supported in some layers even though the provider only produced a final batch result after the last chunk.
   - Evidence: reproduced by runtime logs and code paths in `asr_provider_whisper` / `asr_backend_whisper`.
   - Status: fixed by removing the fake streaming path and rejecting `provider_stream` for Whisper everywhere.
4. Runtime audio input allowed `audio.source=auto` and silently changed operator intent (`mic -> file`) when microphone capture failed.
   - Impact: manual and scripted runs could execute a different scenario than requested while appearing successful.
   - Evidence: code inspection in modern `audio_input_node` and legacy `asr_ros/audio_capture_node`.
   - Status: fixed by removing `auto` from supported runtime sources and surfacing explicit errors.
5. `source_runtime_env.sh` could silently source a stale top-level `install/setup.bash` instead of the real `ros2_ws/install` overlay.
   - Impact: `rqt`, CLI tools, and ROS imports could bind to the wrong workspace state.
   - Evidence: reproduced during environment diagnostics around `rqt`.
   - Status: fixed by making the default overlay deterministic (`ros2_ws/install` only).
6. Gateway preflight still accepted `audio_source=auto` after runtime/audio nodes had already moved to explicit `file|mic`.
   - Impact: API/UI and runtime could disagree on what was a valid start request.
   - Evidence: code inspection in `asr_gateway/api.py` plus live HTTP verification.
   - Status: fixed and covered by API tests + live gateway smoke.
7. Google backend silently retried `model=default` when the requested model was unsupported for a language.
   - Impact: benchmark/runtime results could come from a different model than the configuration claimed.
   - Evidence: code inspection in `asr_backend_google/backend.py` plus targeted unit reproduction.
   - Status: fixed by removing the retry path and surfacing `google_model_unsupported` explicitly.
8. Whisper backend could silently mutate requested CUDA execution into CPU execution through hidden fallback logic.
   - Impact: local performance/resource expectations were not trustworthy and results were not reproducible by configuration alone.
   - Evidence: code inspection in `asr_backend_whisper/backend.py` and legacy config surface review.
   - Status: fixed by removing CPU fallback and turning the removed setting into explicit validation failure.

## Major issues
1. User-facing docs and scripts still pointed at legacy `asr_ros` interfaces (`/asr/set_backend`, `/asr/get_status`, `/asr/text/plain`, `bringup.launch.py`, `demo.launch.py`) instead of the real modular runtime stack.
   - Status: fixed in `README.md`, `docs/run_guide.md`, `docs/newbie_guide.md`, `docs/interfaces.md`, and key wiki entry pages.
2. `run_demo.sh` and `open_live_test_terminals.sh` still launched the wrong stack.
   - Status: migrated to `asr_launch` runtime entry points.
3. Package-level `colcon test` failed with exit code `5` on multiple packages because they had no tests at all.
   - Status: fixed by adding smoke tests across packages.
4. Direct CLI helpers (`generate_report.py`, `generate_plots.py`, dataset import/export/validation scripts) depended on external `PYTHONPATH`.
   - Status: fixed by repo-local bootstrap.
5. Benchmark validation had missing guards, and after hardening it became too strict for minimal valid profiles.
   - Status: fixed with context-aware validation that rejects explicit bad values but still allows omitted optional sections.
6. Gateway default bind was `0.0.0.0`.
   - Status: changed to `127.0.0.1`; LAN exposure is now explicit opt-in.
7. GUI e2e tests used a fixed port and emitted port-collision thread warnings.
   - Status: fixed by allocating a free local port per test fixture.
8. ROS integration tests shared the default `ROS_DOMAIN_ID` and could consume retained messages from an already running stack.
   - Status: fixed by isolating ROS integration tests to a dedicated test domain.
9. `live_sample_eval.py` still accepted incompatible `ros_action --action-streaming` target sets and silently downgraded failed auto-language detection to config language.
   - Status: fixed by adding fail-fast preflight and removing auto-language fallback.
10. `open_live_test_terminals.sh` still allowed `INPUT_MODE=auto` and could open terminals for invalid `provider_stream` combinations.
   - Status: fixed by aligning script validation with real runtime/provider contracts.
11. `docsbot generate` silently reported success with `provider="mock"` whenever `OPENAI_API_KEY` was absent.
   - Status: fixed by making default `auto` mode template-only with explicit warnings; `mock` is now opt-in and `openai` fails fast without a key.
12. `scripts/secret_scan.sh` falsely flagged tracked synthetic Google credential fixtures as leaked secrets.
   - Status: fixed by narrowing the detection pattern and sanitizing fixture key material.
13. Several CLI helper scripts crashed with Python tracebacks on missing input paths.
   - Status: fixed by adding explicit input validation and user-facing error messages.
14. `run_demo.sh` detected managed-stack conflicts only after an unnecessary rebuild.
   - Status: fixed by adding a pre-launch managed-stack preflight.
15. Dataset manifests with relative `audio_path` values were resolved against the caller `cwd` instead of the manifest location.
   - Impact: benchmark runs were cwd-sensitive and dataset bundles were not reproducible across machines or invocation paths.
   - Evidence: code inspection and reproduction in `asr_datasets/manifest.py`.
   - Status: fixed and covered by unit regression tests.
16. Uploaded dataset bundles could silently collide on duplicate basenames and could carry manifests that referenced audio files not present in the uploaded set.
   - Impact: imported datasets could point at the wrong file or become partially broken while appearing accepted.
   - Evidence: code inspection and targeted regression reproduction in `asr_datasets/importer.py`.
   - Status: fixed and covered by unit tests.
17. `make arch` / `archviz all` could start runtime extraction while another managed stack from the same workspace was already running.
   - Impact: architecture generation could hang for a long time or capture a mixed runtime graph that did not belong to the launched profile.
   - Evidence: reproduced on 2026-03-26 with a live `full_stack_dev.launch.py` stack already active.
   - Status: fixed by fail-fast conflict detection and covered by unit tests plus CLI verification.

## Minor issues
1. `mypy` previously aborted immediately because `tests` was not a package and collided with `tests/utils`.
   - Status: fixed by adding `tests/__init__.py`, but large type debt remains.
2. Static docs/wiki still contain a broad legacy corpus around `asr_ros`.
   - Status: key entry points updated; full wiki migration deferred.
3. `ruff` debt remains heavy and dominated by long lines/import order.
4. Browser e2e still emits `websockets` deprecation warnings from dependencies, although the flaky port collision was removed.

## Risks not fixed
- `ruff` is still red:
  - 301 findings total, dominated by `E501` line length.
- `mypy` is still red:
  - 172 errors across 18 files.
- Full cloud E2E for `aws/google/azure` was not executed without live credentials and network.
- `shellcheck` was unavailable in this environment.
- Legacy `asr_ros` compatibility package still exists and preserves a second conceptual runtime surface.
- Many deep wiki pages still describe legacy flows despite updated entry pages.

## What was fixed
- Corrected `RecognizeOnce` provider override semantics in `asr_orchestrator_node`.
- Corrected `cloud_credentials_available` reporting in runtime status.
- Removed fake Whisper streaming support from:
  - `asr_provider_whisper`
  - `asr_backend_whisper`
  - GUI/runtime capability handling
- Removed hidden Whisper CUDA->CPU fallback from `asr_backend_whisper` and turned the legacy `allow_cpu_fallback` setting into explicit validation failure.
- Removed hidden Google `requested model -> default model` retry from `asr_backend_google`.
- Removed implicit `audio.source=auto` fallback behavior from:
  - modular `audio_input_node`
  - legacy `asr_ros/audio_capture_node`
  - related config validation and launch defaults
- Removed hidden fallback behavior from legacy `asr_ros/asr_server_node`:
  - no cloud backend failover path
  - no implicit streaming call for batch-only backends
  - explicit error response when streaming is unsupported
- Made `scripts/source_runtime_env.sh` deterministic:
  - no fallback to top-level `install/`
  - default overlay is `ros2_ws/install`
  - `--with-ros` no longer prepends `ros2_ws/src/*` into `PYTHONPATH`
- Hardened runtime/benchmark config validation:
  - stricter checks for real bad values
  - minimal valid benchmark profiles remain accepted
- Changed gateway and launch defaults from `0.0.0.0` to `127.0.0.1`.
- Strengthened `scripts/release_check.sh`:
  - now runs unit tests, ROS tests, `colcon test`, and benchmark flow.
- Fixed `make test-colcon` by removing unsupported `--symlink-install` from `colcon test`.
- Added package smoke tests so `colcon test` is a meaningful gate instead of an empty-package failure source.
- Added repo-local import bootstrap to Python CLI utilities.
- Hardened CLI helpers to reject missing input files/directories with explicit messages instead of tracebacks.
- Migrated `scripts/run_demo.sh` to `asr_launch/runtime_minimal.launch.py`.
- Added fast managed-stack conflict preflight to `scripts/run_demo.sh`.
- Migrated `scripts/open_live_test_terminals.sh` to current runtime flow with `/asr/runtime/start_session` and `/asr/runtime/results/final`.
- Added fail-fast guardrails to `scripts/open_live_test_terminals.sh` for:
  - `INPUT_MODE`
  - `PROCESSING_MODE`
  - non-streaming `provider_stream` targets
- Added fail-fast guardrails to `scripts/live_sample_eval.py` for:
  - unsupported `ros_action --action-streaming` combinations
  - failed `language-mode=auto` detection
- Corrected legacy scenario configs that previously requested `ros_action` streaming for Whisper.
- Removed stale `allow_cpu_fallback` usage from compatibility configs.
- Removed silent `MockProvider` fallback from default `docsbot` generation.
- Kept deterministic mock drafts only behind explicit `DOCSBOT_LLM_PROVIDER=mock`.
- Tuned `secret_scan.sh` to stay strict on real key material without false-failing on in-repo synthetic fixtures.
- Rewrote primary docs to match the actual runtime stack and service/topic names.
- Updated key wiki entry pages to mark `asr_ros` content as legacy.
- Removed GUI e2e fixed-port collisions by allocating a free port dynamically.
- Resolved dataset manifest audio paths relative to the manifest location instead of the caller `cwd`.
- Hardened dataset bundle import so uploaded manifests:
  - cannot alias duplicate basenames silently
  - cannot reference missing bundle-local audio files
- Hardened runtime request handling with explicit numeric coercion helpers in `audio_input_node` and `asr_orchestrator_node`.
- Hardened provider-stream runtime guards so missing provider state fails explicitly instead of cascading into `AttributeError`.
- Replaced tuple/setattr ROS request builders in `asr_gateway/ros_client.py` with explicit typed builders.
- Narrowed executor-shutdown cleanup handling in `asr_gateway/ros_client.py` and AWS cache parsing in `asr_backend_aws/backend.py`.
- Removed insecure XML parser fallback from `tools/archviz/static_extract.py`.
- Added managed-stack conflict preflight to `archviz runtime/all`, so `make arch` now refuses to run against an already-live stack from the same workspace.

## What tests were added
- Package smoke tests under:
  - `ros2_ws/src/*/test/test_smoke.py` for packages that previously had no test surface
- `tests/unit/test_config_validation.py`
  - runtime validation guards
  - benchmark validation guards
  - minimal benchmark-profile acceptance regression
- `tests/unit/test_gateway_server_main.py`
  - gateway defaults to loopback
- `tests/unit/test_launch_defaults.py`
  - launch defaults use `127.0.0.1`
- `tests/unit/test_runtime_orchestrator_state.py`
  - truthful cloud-credential status reporting
- `tests/unit/test_runtime_orchestrator_recognize_once.py`
  - provider-profile override honored
- `tests/unit/test_colcon_locking.py`
  - release gate coverage
  - runtime scripts target current launch stack
  - `colcon test` path no longer uses `--symlink-install`
- `tests/unit/test_google_backend_model_fallback.py`
  - unsupported Google model/lang pair now fails explicitly instead of retrying `default`
- `tests/unit/test_language_support.py`
  - Whisper provider rejects removed `allow_cpu_fallback` setting
- `tests/unit/test_live_sample_eval.py`
  - `ros_action --action-streaming` reject path
  - strict auto-language detection failure path
- `tests/component/test_provider_manager.py`
  - provider manager rejects Whisper profiles carrying removed CPU-fallback setting
- `tests/component/test_benchmark_orchestrator.py`
  - merged invalid streaming overrides are rejected inside benchmark core, not only at the gateway edge
- `tests/integration/test_cli_flows.py`
  - direct CLI bootstrap without external `PYTHONPATH`
  - explicit negative-path messages for missing import/report/export inputs
- `tools/docsbot/tests/test_orchestrator.py`
  - template-only docs generation when no API key is present
  - explicit OpenAI-mode failure without a key
  - mock provider only when explicitly requested
- `tests/integration/test_ros_recognize_service.py`
  - new runtime `/asr/runtime/recognize_once` override integration test
- `tests/unit/test_streaming_fallback.py`
  - explicit streaming contract regression
  - PCM-to-WAV utility coverage moved out of fake backend fallback
- `tests/unit/test_audio_input_node.py`
  - microphone-open failure is now explicit
- `tests/unit/test_legacy_asr_server_node.py`
  - legacy server returns explicit streaming-not-supported errors
- `tests/unit/test_legacy_audio_capture_node.py`
  - legacy compatibility node no longer falls back from `mic` to `file`
- `tests/integration/test_source_runtime_env.py`
  - deterministic `ASR_COLCON_INSTALL_PREFIX`
  - no source-tree `PYTHONPATH` injection in `--with-ros` mode
- `tests/unit/test_dataset_manifest.py`
  - relative manifest `audio_path` entries resolve from the manifest directory
- `tests/unit/test_dataset_importer.py`
  - duplicate normalized uploaded filenames are rejected
  - uploaded manifests cannot reference audio missing from the uploaded bundle
  - imported manifest audio paths are rewritten to the saved bundle paths deterministically
- `tests/unit/test_archviz.py`
  - managed-stack conflict detection is explicit and workspace-scoped
  - `archviz` CLI returns a non-zero exit code for runtime extraction conflicts

## What scenarios were validated
- `ruff check . --statistics`
  - FAIL, 301 findings recorded for backlog
- `mypy ros2_ws/src tests scripts tools/archviz`
  - FAIL, 172 errors recorded for backlog
- `bandit -q -r ros2_ws/src scripts tools web_ui`
  - FAIL with findings, but 0 high-severity issues
- `pytest -q tests/unit/test_runtime_orchestrator_recognize_once.py tests/unit/test_colcon_locking.py`
  - PASS
- `pytest -q tests/unit/test_streaming_fallback.py tests/unit/test_audio_input_node.py tests/unit/test_legacy_audio_capture_node.py tests/unit/test_runner.py tests/unit/test_config_validation.py tests/contract/test_provider_contract.py tests/integration/test_source_runtime_env.py`
  - PASS
- `pytest -q tests/api/test_gateway_api.py tests/unit/test_legacy_asr_server_node.py tests/unit/test_legacy_audio_capture_node.py tests/integration/test_source_runtime_env.py`
  - PASS
- `pytest -q tests/unit/test_config_validation.py tests/component/test_benchmark_orchestrator.py tests/regression/test_artifact_layout_regression.py`
  - PASS
- `pytest -q tests/api/test_gateway_api.py tests/e2e/test_web_ui_flows.py tests/unit/test_runtime_orchestrator_state.py tests/unit/test_gateway_ros_client.py tests/integration/test_runtime_topic_observability.py tests/integration/test_ros_recognize_service.py -k 'not cloud'`
  - PASS (`3` ROS tests skipped without sourced workspace, by design)
- `pytest -q tests/unit/test_google_backend_model_fallback.py tests/unit/test_language_support.py tests/unit/test_live_sample_eval.py tests/component/test_provider_manager.py tests/component/test_benchmark_orchestrator.py tests/unit/test_colcon_locking.py`
  - PASS
- `pytest -q tests/api/test_gateway_api.py tests/e2e/test_web_ui_flows.py tests/gui/test_frontend_shell.py tests/integration/test_cli_flows.py tests/unit/test_gateway_ros_client.py -k 'not cloud'`
  - PASS
- `source .venv/bin/activate && pytest -q tools/docsbot/tests tests/api/test_gateway_api.py tests/unit/test_gateway_secret_state.py`
  - PASS
- `pytest -q -m 'not ros and not cloud'`
  - PASS
- `pytest -q -m ros tests/integration/test_ros_recognize_service.py`
  - PASS
- `source scripts/source_runtime_env.sh --with-ros && pytest -q tests/integration/test_runtime_topic_observability.py tests/integration/test_ros_recognize_service.py -k 'runtime_recognize_once_service_honors_provider_override or runtime_final_results_are_retained_for_late_subscribers'`
  - PASS
- `make test-colcon`
  - PASS
- `bash scripts/release_check.sh`
  - PASS
- `pytest -q tests/unit/test_dataset_manifest.py tests/unit/test_dataset_importer.py tests/unit/test_runtime_orchestrator_stream_errors.py tests/unit/test_runtime_orchestrator_recognize_once.py tests/unit/test_archviz.py`
  - PASS
- `make arch-static`
  - PASS
- `make arch`
  - FAIL-FAST as designed when another managed stack from the same workspace is already running; explicit conflicting PIDs were reported immediately
- `make docsbot-detect && make docsbot-snapshot && make docsbot-generate && make docsbot-validate`
  - PASS (`provider=none`, explicit template-only warning, no synthetic mock output)
- `make docsbot-validate`
  - PASS
- `find scripts -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n`
  - PASS
- `bash scripts/secret_scan.sh`
  - PASS
- `ROS_DOMAIN_ID=73 bash scripts/run_live_sample_eval.sh --use-wav data/sample/vosk_test.wav --interfaces core --model-runs mock --output-dir /tmp/live_eval_core`
  - PASS
- `ROS_DOMAIN_ID=74 bash scripts/run_live_sample_eval.sh --use-wav data/sample/vosk_test.wav --interfaces ros_service --model-runs mock --ros-auto-launch --output-dir /tmp/live_eval_service`
  - PASS
- `ROS_DOMAIN_ID=75 bash scripts/run_live_sample_eval.sh --use-wav data/sample/vosk_test.wav --interfaces ros_action --model-runs mock --ros-auto-launch --output-dir /tmp/live_eval_action`
  - PASS
- `ROS_DOMAIN_ID=76 bash scripts/run_live_sample_eval.sh --use-wav data/sample/vosk_test.wav --interfaces ros_action --model-runs mock --ros-auto-launch --action-streaming --output-dir /tmp/live_eval_action_stream`
  - PASS
- `ROS_DOMAIN_ID=78 bash scripts/run_demo.sh` + `ros2 service call /asr/runtime/recognize_once ...`
  - PASS
- `bash scripts/run_demo.sh` while a managed full stack was already running
  - PASS (fast explicit preflight rejection before build)
- `make dist`
  - PASS (`dist/ros2_asr_release_20260325_162117.tar.gz`)
- `make report`
  - PASS
- live smoke:
  - restarted `full_stack_dev.launch.py` on `127.0.0.1:8088`
  - `GET /api/health`: PASS
  - `POST /api/runtime/start` with `providers/whisper_local + provider_stream`: `400` PASS
  - `POST /api/runtime/start` with `audio_source=auto`: `400` PASS (gateway preflight + runtime contract aligned)
  - `POST /api/runtime/start` with `whisper + segmented + file`: `200` PASS
  - `POST /api/runtime/stop`: PASS
  - `bash scripts/run_rqt.sh --check-env`: PASS
  - `bash scripts/open_live_test_terminals.sh ... auto ...`: explicit `ERROR` PASS
  - `ASR_PROCESSING_MODE=provider_stream bash scripts/open_live_test_terminals.sh ... whisper_local ...`: explicit `ERROR` PASS
  - `bash scripts/run_live_sample_eval.sh --interfaces ros_action --model-runs whisper:tiny --action-streaming ...`: explicit `ValueError` PASS

## Remaining recommendations
1. Finish the type-cleanup pass for `asr_gateway`, `asr_runtime_nodes`, and test fakes so `mypy` becomes a real gate instead of a report-only tool.
2. Reduce `ruff` debt or introduce targeted ignores; 258 line-length violations alone make the signal noisy.
3. Finish migration or retirement strategy for `asr_ros` so the repo has one clearly primary runtime contract.
4. Migrate the deeper wiki graph away from legacy `asr_ros` pages, not only the entry pages.
5. Add `shellcheck` to the environment and CI.
6. Add cloud-backed contract tests that can run in a controlled credentialed environment.
7. Consider renaming or clarifying `cloud_credentials_available` in the public interface, because for local providers the flag is effectively “not required / satisfied”.
