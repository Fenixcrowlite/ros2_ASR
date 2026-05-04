# External Dataset Benchmark Suite

- suite_id: `external_dataset_suite_20260326T182245Z`
- generated_at: `2026-03-26T18:22:45.687500+00:00`
- benchmark_profiles: `12`
- direct_runs_completed: `12`
- api_runs_recorded: `0`

## Direct Runs

| Benchmark | Dataset | Acoustic Profile | Lang | Samples | Success | WER | CER | Accuracy | Latency ms | RTF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| fleurs_en_us_test_subset_whisper | fleurs_en_us_test_subset | crowdsourced_mobile | en-US | 2 | 2 | 0.1562 | 0.1344 | 0.0000 | 862.91 | 0.0894 |
| fleurs_fr_fr_test_subset_whisper | fleurs_fr_fr_test_subset | crowdsourced_mobile | fr-FR | 2 | 2 | 0.3934 | 0.1990 | 0.0000 | 699.44 | 0.0888 |
| fleurs_ja_jp_test_subset_whisper | fleurs_ja_jp_test_subset | crowdsourced_mobile | ja-JP | 2 | 2 | 1.0000 | 0.2631 | 0.0000 | 936.91 | 0.0556 |
| fleurs_sk_sk_test_subset_whisper | fleurs_sk_sk_test_subset | crowdsourced_mobile | sk-SK | 2 | 2 | 0.8571 | 0.1917 | 0.0000 | 631.87 | 0.1461 |
| librispeech_test_clean_subset_whisper | librispeech_test_clean_subset | clean_read | en-US | 2 | 2 | 0.0741 | 0.0389 | 0.0000 | 677.14 | 0.1250 |
| librispeech_test_other_subset_whisper | librispeech_test_other_subset | harder_read | en-US | 2 | 2 | 0.1111 | 0.0156 | 0.5000 | 544.60 | 0.2438 |
| mini_librispeech_dev_clean_2_subset_whisper | mini_librispeech_dev_clean_2_subset | clean_read | en-US | 2 | 2 | 0.0769 | 0.0323 | 0.5000 | 699.11 | 0.0637 |
| mls_german_test_subset_whisper | mls_german_test_subset | multilingual_audiobook | de-DE | 2 | 2 | 0.2083 | 0.0338 | 0.0000 | 833.90 | 0.0433 |
| mls_spanish_test_subset_whisper | mls_spanish_test_subset | multilingual_audiobook | es-ES | 2 | 2 | 0.1000 | 0.0304 | 0.0000 | 842.75 | 0.0601 |
| voxpopuli_de_test_subset_whisper | voxpopuli_de_test_subset | far_field_plenary | de-DE | 2 | 2 | 0.1542 | 0.0593 | 0.0000 | 734.27 | 0.0601 |
| voxpopuli_en_test_subset_whisper | voxpopuli_en_test_subset | far_field_plenary | en-US | 2 | 2 | 0.2546 | 0.0260 | 0.5000 | 705.23 | 0.0800 |
| voxpopuli_es_test_subset_whisper | voxpopuli_es_test_subset | far_field_plenary | es-ES | 2 | 2 | 0.2843 | 0.1582 | 0.0000 | 872.98 | 0.0533 |

## Acoustic Groups

- `clean_read`: WER `0.0755`, CER `0.0356`, accuracy `0.2500`, latency `688.12` ms, RTF `0.0943`
- `crowdsourced_mobile`: WER `0.6017`, CER `0.1970`, accuracy `0.0000`, latency `782.78` ms, RTF `0.0950`
- `far_field_plenary`: WER `0.2310`, CER `0.0811`, accuracy `0.1667`, latency `770.83` ms, RTF `0.0645`
- `harder_read`: WER `0.1111`, CER `0.0156`, accuracy `0.5000`, latency `544.60` ms, RTF `0.2438`
- `multilingual_audiobook`: WER `0.1542`, CER `0.0321`, accuracy `0.0000`, latency `838.32` ms, RTF `0.0517`
