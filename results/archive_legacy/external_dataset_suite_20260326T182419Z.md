# External Dataset Benchmark Suite

- suite_id: `external_dataset_suite_20260326T182419Z`
- generated_at: `2026-03-26T18:24:19.205569+00:00`
- benchmark_profiles: `12`
- direct_runs_completed: `12`
- api_runs_recorded: `12`

## Direct Runs

| Benchmark | Dataset | Acoustic Profile | Lang | Samples | Success | WER | CER | Accuracy | Latency ms | RTF |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| fleurs_en_us_test_subset_whisper | fleurs_en_us_test_subset | crowdsourced_mobile | en-US | 2 | 2 | 0.1562 | 0.1344 | 0.0000 | 878.54 | 0.0920 |
| fleurs_fr_fr_test_subset_whisper | fleurs_fr_fr_test_subset | crowdsourced_mobile | fr-FR | 2 | 2 | 0.3934 | 0.1990 | 0.0000 | 698.34 | 0.0884 |
| fleurs_ja_jp_test_subset_whisper | fleurs_ja_jp_test_subset | crowdsourced_mobile | ja-JP | 2 | 2 | 1.0000 | 0.2631 | 0.0000 | 964.08 | 0.0570 |
| fleurs_sk_sk_test_subset_whisper | fleurs_sk_sk_test_subset | crowdsourced_mobile | sk-SK | 2 | 2 | 0.8571 | 0.1917 | 0.0000 | 623.84 | 0.1441 |
| librispeech_test_clean_subset_whisper | librispeech_test_clean_subset | clean_read | en-US | 2 | 2 | 0.0741 | 0.0389 | 0.0000 | 672.14 | 0.1249 |
| librispeech_test_other_subset_whisper | librispeech_test_other_subset | harder_read | en-US | 2 | 2 | 0.1111 | 0.0156 | 0.5000 | 536.78 | 0.2404 |
| mini_librispeech_dev_clean_2_subset_whisper | mini_librispeech_dev_clean_2_subset | clean_read | en-US | 2 | 2 | 0.0769 | 0.0323 | 0.5000 | 713.80 | 0.0650 |
| mls_german_test_subset_whisper | mls_german_test_subset | multilingual_audiobook | de-DE | 2 | 2 | 0.2083 | 0.0338 | 0.0000 | 853.29 | 0.0443 |
| mls_spanish_test_subset_whisper | mls_spanish_test_subset | multilingual_audiobook | es-ES | 2 | 2 | 0.1000 | 0.0304 | 0.0000 | 827.69 | 0.0589 |
| voxpopuli_de_test_subset_whisper | voxpopuli_de_test_subset | far_field_plenary | de-DE | 2 | 2 | 0.1542 | 0.0593 | 0.0000 | 754.67 | 0.0621 |
| voxpopuli_en_test_subset_whisper | voxpopuli_en_test_subset | far_field_plenary | en-US | 2 | 2 | 0.2546 | 0.0260 | 0.5000 | 738.17 | 0.0837 |
| voxpopuli_es_test_subset_whisper | voxpopuli_es_test_subset | far_field_plenary | es-ES | 2 | 2 | 0.2843 | 0.1582 | 0.0000 | 857.24 | 0.0523 |

## Acoustic Groups

- `clean_read`: WER `0.0755`, CER `0.0356`, accuracy `0.2500`, latency `692.97` ms, RTF `0.0949`
- `crowdsourced_mobile`: WER `0.6017`, CER `0.1970`, accuracy `0.0000`, latency `791.20` ms, RTF `0.0954`
- `far_field_plenary`: WER `0.2310`, CER `0.0811`, accuracy `0.1667`, latency `783.36` ms, RTF `0.0660`
- `harder_read`: WER `0.1111`, CER `0.0156`, accuracy `0.5000`, latency `536.78` ms, RTF `0.2404`
- `multilingual_audiobook`: WER `0.1542`, CER `0.0321`, accuracy `0.0000`, latency `840.49` ms, RTF `0.0516`

## API Runs

| Benchmark | State | Success Samples | Failed Samples | Message |
|---|---|---:|---:|---|
| fleurs_en_us_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| fleurs_fr_fr_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| fleurs_ja_jp_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| fleurs_sk_sk_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| librispeech_test_clean_subset_whisper | completed | 0 | 0 | Benchmark completed |
| librispeech_test_other_subset_whisper | completed | 0 | 0 | Benchmark completed |
| mini_librispeech_dev_clean_2_subset_whisper | completed | 0 | 0 | Benchmark completed |
| mls_german_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| mls_spanish_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| voxpopuli_de_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| voxpopuli_en_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
| voxpopuli_es_test_subset_whisper | completed | 0 | 0 | Benchmark completed |
