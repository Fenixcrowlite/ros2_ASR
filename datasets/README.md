# Dataset Registry

Datasets are described by JSONL manifests and registry JSON files. A manifest
row must contain:

- `sample_id`
- `audio_path`
- `transcript`
- `language`
- `duration_sec`

## Public Baseline

`datasets/registry/datasets.json` is the compact baseline registry used for
small smoke and regression flows. It points to `datasets/manifests/sample_dataset.jsonl`,
which uses the tiny audio sample in `data/sample/`.

Validate it with:

```bash
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .
```

## Optional External Subsets

Additional public subset manifests for LibriSpeech, FLEURS, VoxPopuli, and MLS
are kept as reproducible metadata. Their audio payloads are not tracked.

Rebuild local payloads when needed:

```bash
bash scripts/download_dataset_optional.sh
```

Generated or downloaded data belongs under ignored directories such as
`datasets/imported/`, `datasets/raw/`, and `datasets/processed/`.
