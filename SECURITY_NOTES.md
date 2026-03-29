# SECURITY_NOTES

## Security checks executed
- `bandit -q -r ros2_ws/src scripts tools web_ui`
- manual review of gateway bind defaults, secret handling, runtime launch scripts, and subprocess callsites used by tooling/control-plane code

## Result summary
- `bandit` exit code: non-zero because findings remain
- Findings:
  - Low: 32
  - Medium: 1
  - High: 0

## Dominant finding classes
- `B404` / `B603`:
  - legitimate subprocess usage in gateway, launch guards, metrics, tooling
- `B112` / `B110`:
  - broad exception handling patterns in some infrastructure code
- `B108`:
  - hardcoded `/tmp` in a test fixture under `tools/docsbot/tests`
- `B101`:
  - asserts in tests

## Mitigations applied in this audit
- Gateway and launch defaults now bind to `127.0.0.1` by default instead of `0.0.0.0`.
- Secret material remains separated through `credentials_ref` and `secrets/refs/*` instead of inline profile secrets.
- Runtime status no longer lies about cloud credential readiness.
- Cloud-facing one-shot requests now honor explicit provider profile selection instead of silently using a different active provider.
- Release and operator entry points now align with the actual runtime stack, reducing accidental exposure through outdated scripts and docs.
- `tools/archviz/static_extract.py` now relies on `defusedxml` instead of falling back to the stdlib XML parser.
- `asr_backend_aws/backend.py` now narrows AWS CLI cache parsing exceptions to explicit filesystem / JSON-decode failures.
- Uploaded dataset bundles now fail fast on duplicate normalized filenames and manifests that reference audio not present in the uploaded bundle.

## Interpretation
- No high-severity issue was found in the scanned scope.
- The remaining findings are mostly hygiene debt in infrastructure/tooling-heavy code, not confirmed exploitable defects.
- The most meaningful practical security improvement in this audit was changing the control plane to loopback-by-default.

## Recommended follow-up
1. Add a documented `.bandit` policy to distinguish accepted subprocess patterns from true regressions.
2. Review `try/except/pass` and `try/except/continue` findings in AWS backend and gateway observer cleanup paths.
3. Add `shellcheck` and a shell-security stage to CI.
4. Add negative tests for malformed or poisoned secret refs and environment-variable injection edges.
5. Add a small allowlist or documented rationale for `archviz` subprocess usage so `bandit` noise does not hide real tooling regressions.
