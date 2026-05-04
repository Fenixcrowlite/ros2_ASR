# External Dataset Benchmark Suite

- suite_id: `external_dataset_suite_20260326T182209Z`
- generated_at: `2026-03-26T18:22:09.999703+00:00`
- benchmark_profiles: `12`
- direct_runs_completed: `12`
- api_runs_recorded: `0`

## Direct Runs

| Benchmark | Dataset | Acoustic Profile | Lang | Samples | Success | WER | CER | Accuracy | Latency ms | RTF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| fleurs_en_us_test_subset_whisper | fleurs_en_us_test_subset | crowdsourced_mobile | en-US | 2 | 2 | 0.1562 | 0.1344 | 0.0000 | 924.17 | 0.0947 |
| fleurs_fr_fr_test_subset_whisper | fleurs_fr_fr_test_subset | crowdsourced_mobile | fr-FR | 2 | 2 | 0.3934 | 0.1990 | 0.0000 | 705.67 | 0.0896 |
| fleurs_ja_jp_test_subset_whisper | fleurs_ja_jp_test_subset | crowdsourced_mobile | ja-JP | 2 | 2 | 1.0000 | 0.2631 | 0.0000 | 935.89 | 0.0553 |
| fleurs_sk_sk_test_subset_whisper | fleurs_sk_sk_test_subset |  | sk-SK | 2 | 2 | 0.8571 | 0.1917 | 0.0000 | 633.83 | 0.1465 |
| librispeech_test_clean_subset_whisper | librispeech_test_clean_subset | clean_read | en-US | 2 | 2 | 0.0741 | 0.0389 | 0.0000 | 693.68 | 0.1302 |
| librispeech_test_other_subset_whisper | librispeech_test_other_subset | harder_read | en-US | 2 | 2 | 0.1111 | 0.0156 | 0.5000 | 558.74 | 0.2497 |
| mini_librispeech_dev_clean_2_subset_whisper | mini_librispeech_dev_clean_2_subset |  | en-US | 2 | 2 | 0.0769 | 0.0323 | 0.5000 | 698.24 | 0.0636 |
| mls_german_test_subset_whisper | mls_german_test_subset | multilingual_audiobook | de-DE | 2 | 2 | 0.2083 | 0.0338 | 0.0000 | 863.05 | 0.0448 |
| mls_spanish_test_subset_whisper | mls_spanish_test_subset | multilingual_audiobook | es-ES | 2 | 2 | 0.1000 | 0.0304 | 0.0000 | 848.90 | 0.0606 |
| voxpopuli_de_test_subset_whisper | voxpopuli_de_test_subset | far_field_plenary | de-DE | 2 | 2 | 0.1542 | 0.0593 | 0.0000 | 756.37 | 0.0621 |
| voxpopuli_en_test_subset_whisper | voxpopuli_en_test_subset | far_field_plenary | en-US | 2 | 2 | 0.2546 | 0.0260 | 0.5000 | 720.23 | 0.0797 |
| voxpopuli_es_test_subset_whisper | voxpopuli_es_test_subset | far_field_plenary | es-ES | 2 | 2 | 0.2843 | 0.1582 | 0.0000 | 869.08 | 0.0530 |

## Acoustic Groups

- `clean_read`: WER `0.0741`, CER `0.0389`, accuracy `0.0000`, latency `693.68` ms, RTF `0.1302`
- `crowdsourced_mobile`: WER `0.5166`, CER `0.1988`, accuracy `0.0000`, latency `855.24` ms, RTF `0.0799`
- `far_field_plenary`: WER `0.2310`, CER `0.0811`, accuracy `0.1667`, latency `781.89` ms, RTF `0.0649`
- `harder_read`: WER `0.1111`, CER `0.0156`, accuracy `0.5000`, latency `558.74` ms, RTF `0.2497`
- `multilingual_audiobook`: WER `0.1542`, CER `0.0321`, accuracy `0.0000`, latency `855.98` ms, RTF `0.0527`
- `unknown`: WER `0.4670`, CER `0.1120`, accuracy `0.2500`, latency `666.04` ms, RTF `0.1051`
