# External Dataset Benchmark Suite

- suite_id: `external_dataset_suite_20260326T182557Z`
- generated_at: `2026-03-26T18:25:57.589349+00:00`
- benchmark_profiles: `12`
- direct_runs_completed: `12`
- api_runs_recorded: `12`

## Direct Runs

| Benchmark | Dataset | Acoustic Profile | Lang | Samples | Success | WER | CER | Accuracy | Latency ms | RTF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| fleurs_en_us_test_subset_whisper | fleurs_en_us_test_subset | crowdsourced_mobile | en-US | 2 | 2 | 0.1562 | 0.1344 | 0.0000 | 885.19 | 0.0921 |
| fleurs_fr_fr_test_subset_whisper | fleurs_fr_fr_test_subset | crowdsourced_mobile | fr-FR | 2 | 2 | 0.3934 | 0.1990 | 0.0000 | 730.26 | 0.0920 |
| fleurs_ja_jp_test_subset_whisper | fleurs_ja_jp_test_subset | crowdsourced_mobile | ja-JP | 2 | 2 | 1.0000 | 0.2631 | 0.0000 | 948.74 | 0.0558 |
| fleurs_sk_sk_test_subset_whisper | fleurs_sk_sk_test_subset | crowdsourced_mobile | sk-SK | 2 | 2 | 0.8571 | 0.1917 | 0.0000 | 654.97 | 0.1514 |
| librispeech_test_clean_subset_whisper | librispeech_test_clean_subset | clean_read | en-US | 2 | 2 | 0.0741 | 0.0389 | 0.0000 | 710.26 | 0.1350 |
| librispeech_test_other_subset_whisper | librispeech_test_other_subset | harder_read | en-US | 2 | 2 | 0.1111 | 0.0156 | 0.5000 | 554.83 | 0.2488 |
| mini_librispeech_dev_clean_2_subset_whisper | mini_librispeech_dev_clean_2_subset | clean_read | en-US | 2 | 2 | 0.0769 | 0.0323 | 0.5000 | 699.79 | 0.0637 |
| mls_german_test_subset_whisper | mls_german_test_subset | multilingual_audiobook | de-DE | 2 | 2 | 0.2083 | 0.0338 | 0.0000 | 879.29 | 0.0456 |
| mls_spanish_test_subset_whisper | mls_spanish_test_subset | multilingual_audiobook | es-ES | 2 | 2 | 0.1000 | 0.0304 | 0.0000 | 840.68 | 0.0598 |
| voxpopuli_de_test_subset_whisper | voxpopuli_de_test_subset | far_field_plenary | de-DE | 2 | 2 | 0.1542 | 0.0593 | 0.0000 | 745.84 | 0.0611 |
| voxpopuli_en_test_subset_whisper | voxpopuli_en_test_subset | far_field_plenary | en-US | 2 | 2 | 0.2546 | 0.0260 | 0.5000 | 722.87 | 0.0815 |
| voxpopuli_es_test_subset_whisper | voxpopuli_es_test_subset | far_field_plenary | es-ES | 2 | 2 | 0.2843 | 0.1582 | 0.0000 | 880.23 | 0.0537 |

## Acoustic Groups

- `clean_read`: WER `0.0755`, CER `0.0356`, accuracy `0.2500`, latency `705.03` ms, RTF `0.0994`
- `crowdsourced_mobile`: WER `0.6017`, CER `0.1970`, accuracy `0.0000`, latency `804.79` ms, RTF `0.0978`
- `far_field_plenary`: WER `0.2310`, CER `0.0811`, accuracy `0.1667`, latency `782.98` ms, RTF `0.0655`
- `harder_read`: WER `0.1111`, CER `0.0156`, accuracy `0.5000`, latency `554.83` ms, RTF `0.2488`
- `multilingual_audiobook`: WER `0.1542`, CER `0.0321`, accuracy `0.0000`, latency `859.99` ms, RTF `0.0527`

## API Runs

| Benchmark | State | Success Samples | Failed Samples | Mean WER | Mean Latency ms | Message |
|---|---|---:|---:|---:|---:|---|
| fleurs_en_us_test_subset_whisper | completed | 2 | 0 | 0.1562 | 627.51 | Benchmark completed |
| fleurs_fr_fr_test_subset_whisper | completed | 2 | 0 | 0.3934 | 694.52 | Benchmark completed |
| fleurs_ja_jp_test_subset_whisper | completed | 2 | 0 | 1.0000 | 945.86 | Benchmark completed |
| fleurs_sk_sk_test_subset_whisper | completed | 2 | 0 | 0.8571 | 666.26 | Benchmark completed |
| librispeech_test_clean_subset_whisper | completed | 2 | 0 | 0.0741 | 690.10 | Benchmark completed |
| librispeech_test_other_subset_whisper | completed | 2 | 0 | 0.1111 | 591.71 | Benchmark completed |
| mini_librispeech_dev_clean_2_subset_whisper | completed | 2 | 0 | 0.0769 | 714.22 | Benchmark completed |
| mls_german_test_subset_whisper | completed | 2 | 0 | 0.2083 | 878.48 | Benchmark completed |
| mls_spanish_test_subset_whisper | completed | 2 | 0 | 0.1000 | 865.64 | Benchmark completed |
| voxpopuli_de_test_subset_whisper | completed | 2 | 0 | 0.1542 | 750.81 | Benchmark completed |
| voxpopuli_en_test_subset_whisper | completed | 2 | 0 | 0.2546 | 738.39 | Benchmark completed |
| voxpopuli_es_test_subset_whisper | completed | 2 | 0 | 0.2843 | 882.33 | Benchmark completed |
