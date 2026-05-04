# Dataset Registry

This repository separates the stable baseline dataset registry from extension candidates used for broader thesis experiments.

## Baseline Active Registry

`datasets/registry/datasets.json` contains the current baseline active dataset registry. The validated baseline thesis evidence uses:

| dataset_id | source | language | samples | audio included | used in baseline benchmark |
|---|---|---|---:|---|---|
| `librispeech_test_clean_subset` | LibriSpeech test-clean | en-US | 10 | yes | yes |

Validate it with:

```bash
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .
```

## Optional Catalog And Extension Candidates

`datasets/registry/datasets_catalog.json` lists additional dataset manifests and imported audio that can be promoted into an extended benchmark registry after validation. These entries are not part of the baseline thesis interpretation until they are included in `datasets/registry/datasets_extended.json`.

The extended benchmark work promotes validated catalog datasets into:

```text
datasets/registry/datasets_extended.json
```

That registry is intended for multi-dataset, multilingual and domain-generalization experiments while preserving the existing baseline evidence package.

## Benchmark Scale

The baseline benchmark is thesis-scale and uses 10 clean LibriSpeech source utterances with derived SNR variants for robustness testing. Extended benchmark subsets may contain more datasets and languages, but they remain controlled thesis subsets rather than statistically representative large-scale ASR corpora.
