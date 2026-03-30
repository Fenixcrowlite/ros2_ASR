# Broken Or Fake Paths

## Still present but not canonical

### `ros2_ws/src/asr_benchmark`

- Status: compatibility-only
- Problem: old backend-centric benchmark flow, flat artifact surface, separate config semantics
- Action: kept, but explicitly marked legacy; `make bench` no longer uses it

### `ros2_ws/src/asr_ros`

- Status: legacy runtime path
- Problem: duplicates responsibilities now owned by `asr_runtime_nodes`
- Action: not removed automatically; should be migrated to legacy namespace/documentation later

### `ros2_ws/src/asr_backend_*`

- Status: transitional compatibility layer
- Problem: duplicates provider-side integrations in `asr_provider_*`
- Action: still needed for old paths and `live_sample_eval.py`, but not the target architecture

### `scripts/live_sample_eval.py`

- Status: useful but architecturally off-path
- Problem: still tied to old backend/config model instead of the provider/profile benchmark core
- Action: keep as specialized operator tool, but treat as transitional

## Fake or test-only entities that must stay isolated

- `tests/utils/fakes.py`
- `asr_backend_mock`
- `FakeGatewayRosClient` / fake provider profiles in tests

These are acceptable only because they are cleanly kept in tests or explicitly named mock/fake.

## Broken-by-design behaviors found and addressed

- `make bench` previously looked like a modern benchmark entrypoint but actually routed through the legacy runner.
  Fixed.
- Logs tab previously merged raw tails without honest ordering/source metadata.
  Fixed.
- `generate_report.py` accepted only legacy flat JSON despite canonical benchmark summaries being the real source of truth.
  Fixed.

## Remaining misleading areas

- old docs/wiki pages still describe legacy benchmark/runtime surfaces as if they are primary
- generated architecture snapshots under `docs/arch` are useful evidence, but not authoritative design docs
