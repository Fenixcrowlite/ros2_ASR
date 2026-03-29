# External Dataset Subsets

This repository now includes reproducible tiny subsets extracted from large
public ASR corpora. They are intended for smoke tests, demos, gateway checks,
and cro
## Build And Validatess-corpus local benchmarks, not for statistically final research claims.


```bash
bash scripts/download_dataset_optional.sh
python scripts/run_external_dataset_suite.py --mode core
python scripts/run_external_dataset_suite.py --mode both --api-base-url http://127.0.0.1:8088
```

The download step rebuilds the local subset manifests, imported WAV files,
dataset profiles, benchmark profiles, and dataset registry entries in a
deterministic way.

## Included Subsets

| dataset_id | source corpus | lang | acoustic profile | source URL |
|---|---|---|---|---|
| `mini_librispeech_dev_clean_2_subset` | Mini LibriSpeech / SLR31 | `en-US` | `clean_read` | <https://www.openslr.org/31/> |
| `librispeech_test_clean_subset` | LibriSpeech / SLR12 | `en-US` | `clean_read` | <https://www.openslr.org/12/> |
| `librispeech_test_other_subset` | LibriSpeech / SLR12 | `en-US` | `harder_read` | <https://www.openslr.org/12/> |
| `fleurs_en_us_test_subset` | FLEURS | `en-US` | `crowdsourced_mobile` | <https://huggingface.co/datasets/google/fleurs> |
| `fleurs_fr_fr_test_subset` | FLEURS | `fr-FR` | `crowdsourced_mobile` | <https://huggingface.co/datasets/google/fleurs> |
| `fleurs_ja_jp_test_subset` | FLEURS | `ja-JP` | `crowdsourced_mobile` | <https://huggingface.co/datasets/google/fleurs> |
| `fleurs_sk_sk_test_subset` | FLEURS | `sk-SK` | `crowdsourced_mobile` | <https://huggingface.co/datasets/google/fleurs> |
| `voxpopuli_en_test_subset` | VoxPopuli | `en-US` | `far_field_plenary` | <https://huggingface.co/datasets/facebook/voxpopuli> |
| `voxpopuli_de_test_subset` | VoxPopuli | `de-DE` | `far_field_plenary` | <https://huggingface.co/datasets/facebook/voxpopuli> |
| `voxpopuli_es_test_subset` | VoxPopuli | `es-ES` | `far_field_plenary` | <https://huggingface.co/datasets/facebook/voxpopuli> |
| `mls_german_test_subset` | Multilingual LibriSpeech | `de-DE` | `multilingual_audiobook` | <https://huggingface.co/datasets/facebook/multilingual_librispeech> |
| `mls_spanish_test_subset` | Multilingual LibriSpeech | `es-ES` | `multilingual_audiobook` | <https://huggingface.co/datasets/facebook/multilingual_librispeech> |

Every subset currently keeps `2` local samples and has a paired benchmark
profile `benchmark/<dataset_id>_whisper`.

## Latest End-To-End Suite

Latest combined direct+API suite artifact:

- `results/external_dataset_suite_20260326T182557Z.md`
- `results/external_dataset_suite_20260326T182557Z.json`

That suite validated:

- `12` benchmark profiles
- `24/24` successful direct benchmark samples
- `24/24` successful live API benchmark samples
- no direct/API WER divergence beyond floating-point noise
