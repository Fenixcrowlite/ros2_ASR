# MIGRATION_NOTES

## 2026-03-12 stabilization checkpoint

### Behavior changes
1. ROS node shutdown path changed.
- `asr_server_node`, `audio_capture_node`, `asr_text_output_node` now use shared safe shutdown helper.
- Known double-shutdown race (`rcl_shutdown already called`) is tolerated; unexpected shutdown errors are still surfaced.

2. AWS STS preflight execution changed.
- Web GUI auth preflight now tries boto3 STS first.
- If boto3 is unavailable, it falls back to `aws sts get-caller-identity`.
- SSO/token errors are normalized to actionable messages.
- Successful checks are cached briefly in-memory (default `120s`, env override: `WEB_GUI_AWS_STS_PREFLIGHT_TTL_SEC`).

3. Google credential validation became stricter.
- Existing path check is now supplemented with JSON readability/object check before job launch.

4. Colcon notifications are disabled by default in project runflows.
- `COLCON_EXTENSION_BLOCKLIST=colcon_core.event_handler.desktop_notification` is now injected in `Makefile` build/test targets and runtime env script.
- Intended to prevent unintended screen wakeups during background activity.

5. Colcon workspace operations are now serialized via lock wrapper.
- `Makefile` and runtime scripts call `scripts/with_colcon_lock.sh colcon ...`.
- This prevents nondeterministic failures when multiple scenarios start concurrently.

6. Web GUI now auto-restores non-secret draft form state.
- Browser localStorage keeps runtime/profile form values between restarts.
- Secret inputs are excluded from draft persistence by design.

7. Web GUI jobs panel now separates active and archived history.
- Active jobs remain in the primary jobs table.
- Inactive restored jobs from previous sessions are moved to a collapsed dropdown section.

### Existing hardening retained from previous checkpoint
- Browser-first AWS SSO login default.
- Strict SSO runtime profile requirements (`AWS_SSO_ACCOUNT_ID`, `AWS_SSO_ROLE_NAME`).
- Benchmark scenario strict normalization and manifest-first relative WAV resolution.
- Job stop wait-timeout persistence in job metadata.

### Operator action required
1. Ensure runtime environments include either boto3 or AWS CLI for AWS preflight.
2. If desktop notifications are needed, override `COLCON_EXTENSION_BLOCKLIST` explicitly per session.
3. Keep cloud credential files valid JSON (for Google) and pass complete auth tuples (Azure/AWS).
