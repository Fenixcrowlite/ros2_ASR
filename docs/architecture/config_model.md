# Configuration Model

## Profile taxonomy
- `configs/runtime/*.yaml`
- `configs/providers/*.yaml`
- `configs/benchmark/*.yaml`
- `configs/datasets/*.yaml`
- `configs/metrics/*.yaml`
- `configs/deployment/*.yaml`
- `configs/gui/*.yaml`
- resolved snapshots: `configs/resolved/*.json`

## Merge/override precedence
1. base defaults (`_base.yaml`, if present)
2. deployment defaults
3. selected profile + inheritance
4. related profiles (provider/dataset/metric)
5. launch overrides
6. env overrides (`ASR_CFG__...`)
7. ROS parameter overrides
8. session temporary overrides

## Secret model
Provider profiles contain `credentials_ref` only.
Secret refs are stored in `secrets/refs/*.yaml` and resolved via:
- native file references where the provider already has a native file format,
- env/profile injection for providers that natively authenticate that way,
- optional compatibility env variables.

Current cloud baseline:
- `google` -> `credentials_ref` -> service-account JSON file
- `aws` -> `credentials_ref` -> native AWS profile/access-key envs
- `azure` -> `credentials_ref` -> native Azure Speech envs

Resolved secret values are masked before logging.
