# Config Test Matrix

## Runtime Profiles
- Valid runtime profile with required blocks: `audio`, `preprocess`, `vad`, `orchestrator`
- Missing required key
- Invalid `audio.sample_rate_hz <= 0`
- Inheritance across parent/child profiles
- Circular inheritance
- Launch override + env override + ROS/session override precedence

## Provider Profiles
- Valid local provider profile
- Valid cloud provider profile with secret ref
- Missing `provider_id`
- Non-object `settings`
- Missing/invalid `credentials_ref`
- GUI-linked secret ref compatibility

## Benchmark Profiles
- Valid dataset/provider/metric references
- Missing dataset profile
- Empty provider list
- Unknown metric profile entries
- Dataset profile with missing manifest path

## Dataset Profiles
- Valid manifest path
- Missing manifest path
- Manifest path pointing to broken manifest

## Secret Refs
- `env` kind with all required vars
- `env` kind with missing required vars
- `file` kind using `env_fallback`
- `file` kind with unreadable/missing file
- Masked handling verification

## Execution Notes
- Fast suite validates these through `unit`, `component`, `contract`, and `api` tests.
- ROS launch parameter overrides remain future work for dedicated `ros`-marked system tests.
