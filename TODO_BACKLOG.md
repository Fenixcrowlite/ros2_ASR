# TODO_BACKLOG

## P0
1. Add ROS launch-cycle regression (`start/stop` repeated N times) in automated suite.
- Goal: enforce no shutdown tracebacks and no zombie processes under repeated operator stop/restart.

2. Add cloud auth contract tests for additional AWS STS/network exception permutations.
- Goal: guarantee stable actionable error mapping for SSO/token/network edge failures.

## P1
1. Add `shellcheck` stage to CI and fix reported shell issues.
- Goal: uniform shell safety enforcement across `scripts/*.sh` and web launcher scripts.

2. Introduce `.bandit` config with justified suppressions.
- Goal: reduce noise while keeping meaningful security signal in CI.

3. Expand backend coverage for dependency-heavy modules (`azure/vosk/whisper`).
- Goal: raise deterministic unit coverage without requiring cloud billing or heavy runtime dependencies.

4. Add operational runbook section for long demo sessions (AWS SSO refresh cadence + recovery flow).
- Goal: reduce demo-time auth failures and speed operator troubleshooting.

5. Add browser-level E2E tests for Web GUI draft persistence.
- Goal: verify restore flow + explicit non-persistence of secret fields under real DOM lifecycle.

## P2
1. Add structured preflight diagnostics endpoint for explicit cloud-auth health checks.
- Goal: separate diagnostics from job-start API and improve UX observability.

2. Add optional policy toggle to re-enable colcon desktop notifications for local developer preference.
- Goal: preserve current safe default while allowing explicit opt-in.

3. Add stress test that launches overlapping build/test/demo commands and asserts lock serialization.
- Goal: keep future changes from reintroducing colcon workspace race conditions.
