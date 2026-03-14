# SECURITY_NOTES

## Security checks executed
- `bandit -q -r web_gui ros2_ws/src scripts tools -x '*/build/*,*/install/*,*/log/*,*/.venv/*'`

## Result summary
- Exit code: non-zero (expected when findings exist).
- Severity: 29 Low, 1 Medium, 0 High.
- Dominant classes:
  - `B404/B603`: subprocess usage in orchestrator/tooling code.
  - `B101`: asserts in test files.
  - `B108`: hardcoded `/tmp` path in test fixture.
  - `B105`: secret-like env-var names in mapping constants.

## Interpretation
- High-severity issues were not found.
- Most findings are known/acceptable for infrastructure modules that legitimately spawn vetted external commands (`ros2`, `aws`, tooling CLIs).

## Mitigations applied in this audit cycle
- Cloud auth validation tightened before launching long jobs.
- AWS preflight uses runtime env and emits normalized actionable errors for SSO/token failures.
- AWS STS preflight success is cached briefly in-memory (TTL, default 120s) to reduce repeated calls; cache key binds to effective auth/env tuple.
- Google credential files are validated as readable JSON objects pre-launch.
- ROS shutdown race handling prevents noisy crash traces on stop.
- Colcon desktop notifications are blocklisted by default to reduce background side effects.
- Web GUI draft persistence excludes secret fields from browser storage.

## Recommended follow-up
1. Add `.bandit` policy with explicit documented suppressions for known-safe subprocess paths.
2. Add command-origin documentation for each subprocess callsite (trusted builder vs user payload).
3. Add security-focused tests for malformed credential files and auth-profile poisoning attempts.
