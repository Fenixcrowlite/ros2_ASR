# Test Data Strategy

## Layout
- `tests/fixtures/manifests/`
- `tests/fixtures/providers/`
- runtime-generated temp project roots under pytest temp directories

## Data Classes Used
- Valid dataset manifest fixture
- Duplicate-sample-id manifest fixture
- Fake cloud error payload fixture
- Repository sample WAV reused for deterministic audio-path tests

## Why Temp Project Roots
- Gateway/API/UI tests need `configs/`, `datasets/`, `secrets/`, `artifacts/`, `logs/`, and `web_ui/frontend/` together.
- Cloning a minimal project root into a temp directory avoids mutating repository state.
- This also makes artifact, dataset, and secret tests reproducible.

## Future Expansion
- Add explicit malformed audio fixtures
- Add multilingual/noisy mini datasets
- Add fake provider response corpus for quota/rate-limit/network-failure scenarios
- Add resource-usage snapshots for latency/resource regression tracking
