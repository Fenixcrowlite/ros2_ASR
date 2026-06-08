# Datasets

Datasets are represented by registry files and JSONL manifests. The benchmark
core reads manifests through `asr_datasets` and never requires large audio
payloads to be tracked in source control.

## Layout

- `datasets/registry/datasets.json`: compact baseline registry.
- `datasets/registry/datasets_catalog.json`: catalog metadata for optional
  subsets.
- `datasets/manifests/*.jsonl`: checked-in manifest rows.
- `configs/datasets/*.yaml`: dataset profiles.
- `data/sample/`: tiny audio samples for smoke checks.

Ignored payload directories include:

- `datasets/raw/`
- `datasets/imported/`
- `datasets/processed/`
- `datasets/noise_assets/`

## Manifest Row

Each JSONL row should include:

```json
{"sample_id":"sample-001","audio_path":"data/sample/vosk_test.wav","transcript":"hello world","language":"en-US","duration_sec":1.0}
```

Required fields:

- `sample_id`
- `audio_path`
- `transcript`
- `language`
- `duration_sec`

## Validate

```bash
make validate-datasets
```

Direct command:

```bash
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .
```

## Import

Import helpers live under `scripts/import_dataset/` and the `asr_datasets`
package. Use ignored payload folders for local data, then keep only small
manifests and reproducible metadata under version control.

## Optional Public Subsets

The repository includes manifests for selected LibriSpeech, FLEURS, VoxPopuli,
and MLS subsets. Audio payloads are not tracked. Recreate local payloads when
needed:

```bash
bash scripts/download_dataset_optional.sh
```
