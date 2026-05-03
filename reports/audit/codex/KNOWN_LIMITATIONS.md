# KNOWN_LIMITATIONS

1. Full cloud E2E was not executed.
- `aws`, `google`, and `azure` provider paths still require live credentials, network, and billing-enabled accounts to be fully validated end-to-end.

2. Static debt remains significant.
- `ruff check . --statistics` reports 301 findings.
- `mypy ros2_ws/src tests scripts tools/archviz` reports 172 errors in 18 files.

3. The repository still carries two runtime concepts.
- The modular runtime stack is primary.
- `asr_ros` still exists as a compatibility surface and can still confuse future contributors if not explicitly retired or isolated.

4. Wiki migration is incomplete.
- Entry pages now warn about the modular runtime, but many deeper `docs/wiki` pages still document legacy `asr_ros` flows.

5. Shell linting is incomplete.
- `shellcheck` was not available in this environment, so shell script review stayed manual plus `bash -n`.

6. Browser e2e dependency warnings remain.
- The flaky fixed-port issue was removed, but `websockets` deprecation warnings still appear through third-party dependencies.

7. Security findings are reduced but not zero.
- `bandit` still reports 32 low and 1 medium finding, mostly around legitimate subprocess usage and test-code patterns.

8. `cloud_credentials_available` remains a legacy-named field.
- For local providers it effectively means “credentials not required / runtime ready”.
- The field is now truthful, but the name is still semantically awkward.

9. `scripts/live_sample_eval.py` is still a compatibility-oriented tool.
- It intentionally exercises legacy `core|ros_service|ros_action` paths, including `asr_ros`.
- It is no longer the primary runtime demonstration path.
- It now fails fast on unsupported combinations, but the tool itself still belongs to the legacy surface.

10. `make arch` still needs a clean managed-stack state.
- `archviz runtime/all` now refuses to run when another managed stack from the same workspace is already alive, which is the correct safety behavior.
- Full runtime architecture extraction is still relatively expensive because the `full` profile launches multiple stacks sequentially.
