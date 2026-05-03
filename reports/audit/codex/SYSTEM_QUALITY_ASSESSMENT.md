# System Quality Assessment

This assessment is based on the combined external benchmark suite in
`results/external_dataset_suite_20260326T182557Z.md` and
`results/external_dataset_suite_20260326T182557Z.json`.

## Scope

- corpora covered: Mini LibriSpeech, LibriSpeech, FLEURS, VoxPopuli,
  Multilingual LibriSpeech
- benchmark profiles: `12`
- direct benchmark samples: `24`
- live API benchmark samples: `24`
- provider under test: `providers/whisper_local`

## What Was Validated

- dataset import and manifest generation across `HF parquet`, `HF tar+tsv`,
  and `HF tar+transcripts` layouts
- dataset profile validation and benchmark profile validation
- manifest loading and path resolution
- direct `BenchmarkOrchestrator` path
- live `/api/datasets`, `/api/benchmark/run`, `/api/benchmark/status` path
- artifact generation and summary loading

## Quantitative Summary

- direct success rate: `24/24`
- live API success rate: `24/24`
- mean direct WER across the `12` profiles: `0.3059`
- mean direct CER across the `12` profiles: `0.0986`
- mean direct latency: `771.08 ms`
- mean direct RTF: `0.0950`
- max direct-vs-API WER delta: `0.000000015`
- max direct-vs-API latency delta: `257.68 ms`

## Strong Areas

- Control plane is now stable on this corpus set: after stack restart, all
  `12/12` API benchmark submissions completed successfully.
- Metric pipeline is consistent: direct and API WER values matched to
  floating-point noise for all `12` profiles.
- English clean/read speech quality is strong:
  - `librispeech_test_clean_subset_whisper`: WER `0.0741`
  - `mini_librispeech_dev_clean_2_subset_whisper`: WER `0.0769`
- Multilingual audiobook quality is acceptable:
  - group mean WER `0.1542`
  - group mean CER `0.0321`
- Runtime cost profile remains predictable:
  - all direct runs stayed below `1 s` mean latency
  - all direct runs stayed below `0.25` mean RTF

## Weak Areas

- Crowdsourced multilingual mobile speech is the weakest current regime:
  - group mean WER `0.6017`
  - `fleurs_ja_jp_test_subset_whisper`: WER `1.0000`
  - `fleurs_sk_sk_test_subset_whisper`: WER `0.8571`
  - `fleurs_fr_fr_test_subset_whisper`: WER `0.3934`
- Far-field plenary speech is usable but clearly worse than clean read speech:
  - group mean WER `0.2310`
  - group mean CER `0.0811`
- `sample_accuracy` is very strict and often `0.0` even when WER/CER are
  acceptable, so it should not be used alone for product quality conclusions.

## Engineering Judgment

- The project-level system is now operationally consistent on a broader and
  more realistic external corpus mix.
- The infrastructure, config resolution, manifests, benchmark manager, gateway
  action path, and artifact loading behave predictably on this suite.
- The main quality ceiling is not the control plane anymore; it is backend ASR
  accuracy on multilingual crowdsourced speech and some far-field speech.

## Remaining Limits

- Each imported subset contains only `2` samples, so the numbers are good for
  engineering validation and demo hardening, not for publication-grade model
  ranking.
- This pass exercised `whisper_local` only.
- Cloud providers were not included in this external suite because credentials
  were not supplied.
