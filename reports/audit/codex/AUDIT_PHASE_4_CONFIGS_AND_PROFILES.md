# Audit Phase 4: Configs And Profiles

## Real config system

The real, scalable config system is profile-driven:

- runtime profiles
- provider profiles
- benchmark profiles
- dataset profiles
- metric profiles
- deployment profiles
- GUI profile

Resolution and validation live in `asr_config`.

## Config systems that still coexist

- profile-driven canonical system under `configs/<type>/...`
- older flat config flow:
  - `configs/default.yaml`
  - `configs/live_mic_whisper.yaml`
  - several web/demo helper YAMLs

## Findings

- provider selection and provider preset merge logic is centralized correctly in `ProviderManager` + `resolve_provider_execution`
- provider pricing metadata is correctly attached to provider presets and reused by benchmark summaries
- dataset profiles are simple and honest: mostly `manifest_path` + default language
- metric profiles are thin but useful; they define enabled metrics without leaking formulas into profiles
- deployment and GUI profiles exist, but their runtime effect is much narrower than their names suggest

## Repairs made

- `make bench` no longer bypasses benchmark profiles through `configs/default.yaml`
- report generation now accepts canonical benchmark summary JSON
- legacy benchmark wrapper is explicitly marked as compatibility-only

## Remaining config pathologies

- `live_sample_eval.py` still uses old backend-centric config expectations
- `configs/default.yaml` remains necessary only for legacy tooling
- `configs/web_latest_*` and similar one-off YAMLs are operational presets, not true architectural profiles
