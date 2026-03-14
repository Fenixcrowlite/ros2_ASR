# asr_config

Profile-driven configuration and secret-reference subsystem.

## Responsibilities
- Load and merge typed profile hierarchy.
- Apply deterministic override precedence.
- Generate resolved snapshots.
- Resolve secret refs through env/file mechanisms.

## Boundaries
- No provider inference.
- No direct ROS runtime control.
