# HARDENING_REPORT

## Hardening changes
- Added unified ROS shutdown helper `asr_ros/shutdown.py` and wired all runtime nodes to it.
- Added `ExternalShutdownException` handling in ROS node entry points.
- AWS preflight in Web GUI switched to boto3-first STS validation with constrained timeouts and CLI fallback.
- Added short TTL cache for successful AWS STS preflight checks (configurable via `WEB_GUI_AWS_STS_PREFLIGHT_TTL_SEC`).
- Added AWS auth error normalization to return actionable SSO/token diagnostics.
- Added Google credentials JSON readability/shape check before launching cloud-targeted jobs.
- Disabled colcon desktop notifications by default in `Makefile` and runtime env bootstrap (`COLCON_EXTENSION_BLOCKLIST`).
- Added shared colcon lock wrapper `scripts/with_colcon_lock.sh` and wired all runtime/build/test scripts to it.
- Added Web GUI draft persistence for non-secret fields in `web_gui/static/app.js` (auto-save + restore at startup).
- Added split jobs view in Web GUI: inactive restored jobs are moved to collapsible dropdown, active jobs remain pinned in main table.
- Kept earlier hardening active: strict benchmark scenarios normalization, manifest-first dataset path resolution, job stop timeout persistence, cloud-target selection precedence.

## Failure modes closed
- ROS stop/Ctrl+C now avoids repeated `rcl_shutdown already called` tracebacks in bringup nodes.
- AWS SSO failures now return explicit operator guidance instead of opaque raw errors.
- Repeated AWS job starts no longer repeat identical STS checks every time within short TTL window.
- Invalid/corrupted Google credentials JSON is rejected before expensive runtime launch.
- Background build/test activity no longer sends desktop notifications that can wake the locked screen.
- Concurrent `colcon` flows no longer race each other on shared workspace directories.
- Operator restart of Web GUI no longer forces full re-entry of non-secret run configuration.
- Operator job table no longer gets polluted by inactive historical jobs from previous sessions.

## Added guardrails
- `safe_shutdown_node()` enforces context-aware destroy/shutdown ordering and suppresses only known double-shutdown race.
- AWS preflight runs against effective runtime env (`AWS_PROFILE`, `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE`) before job start.
- AWS error normalizer maps high-frequency auth failures (pending authorization expired, invalid grant, expired token, missing credentials).
- AWS preflight cache key ties to effective auth/env tuple (profile, region, key/token/config paths) for deterministic reuse.
- Colcon notification extension is explicitly blocklisted in automated flows.
- `with_colcon_lock.sh` serializes workspace-mutating `colcon` operations via `flock`.
- Web GUI draft autosave explicitly excludes secret inputs to avoid credential persistence in browser storage.
- Web GUI archived-jobs dropdown keeps inactive restored jobs accessible without crowding active operations.

## Invariants now enforced
- ROS node `main()` paths do not fail on already-shutdown context races.
- AWS cloud-targeted jobs must pass STS preflight (unless explicitly disabled).
- AWS preflight success can be reused for short TTL only; failed auth still fails fast immediately.
- Google cloud-targeted jobs require readable JSON credential object.
- Build/test flows should not emit colcon desktop notifications by default.
- Build/test/demo/bench colcon operations are lock-serialized when launched concurrently.
- Benchmark scenarios must be deterministic (`clean` or `snr<N>`) and dataset relative paths resolve manifest-first.
- Web GUI draft restore covers non-secret configuration fields across restarts.
- Inactive restored jobs are hidden from main table but remain available from collapsible archive list.
