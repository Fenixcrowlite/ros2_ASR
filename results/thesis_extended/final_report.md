# Extended Multi-Dataset ASR Benchmark Report

## Goal

This report extends the baseline bachelor thesis evidence with a multi-dataset ASR benchmark across dataset families, languages and acoustic conditions.

## Baseline Versus Extended Evidence

The baseline evidence remains in `results/thesis_final/` and uses only `librispeech_test_clean_subset`. The extended evidence in `results/thesis_extended/` evaluates additional validated dataset subsets and must be interpreted as a separate extension layer.

## Plot Scope

Final extended plots exclude Hugging Face providers by thesis presentation choice. Hugging Face rows remain in CSV tables and raw artifacts for traceability, but they are not used as plotted series in `results/thesis_extended/plots/`.

## Datasets

| dataset_id | language | acoustic_profile | sample_count | source |
|---|---|---|---:|---|
| fleurs_en_us_test_subset | en-US | crowdsourced_mobile | 10 | google/fleurs en_us test |
| fleurs_fr_fr_test_subset | fr-FR | crowdsourced_mobile | 10 | google/fleurs fr_fr test |
| fleurs_ja_jp_test_subset | ja-JP | crowdsourced_mobile | 10 | google/fleurs ja_jp test |
| fleurs_sk_sk_test_subset | sk-SK | crowdsourced_mobile | 10 | google/fleurs sk_sk test |
| librispeech_test_clean_subset | en-US | clean_read | 10 | OpenSLR SLR12 test-clean |
| librispeech_test_other_subset | en-US | harder_read | 10 | OpenSLR SLR12 test-other |
| mini_librispeech_dev_clean_2_subset | en-US | clean_read | 10 | OpenSLR SLR31 dev-clean-2 |
| mls_german_test_subset | de-DE | multilingual_audiobook | 10 | facebook/multilingual_librispeech mls_german test |
| mls_spanish_test_subset | es-ES | multilingual_audiobook | 10 | facebook/multilingual_librispeech mls_spanish test |
| voxpopuli_de_test_subset | de-DE | far_field_plenary | 10 | facebook/voxpopuli de test |
| voxpopuli_en_test_subset | en-US | far_field_plenary | 10 | facebook/voxpopuli en test |
| voxpopuli_es_test_subset | es-ES | far_field_plenary | 10 | facebook/voxpopuli es test |

## Providers

| provider | local/cloud | credential status | benchmark status |
|---|---|---|---|
| aws_cloud | cloud | required if cloud run present | success |
| azure_cloud | cloud | required if cloud run present | success |
| google_cloud | cloud | required if cloud run present | success |
| huggingface_local | local | not required | success |
| vosk_local | local | not required | success |
| whisper_local | local | not required | success |

## Metric Family Rationale

The extended benchmark keeps metric families separate because no single provider is universally best across quality, latency, robustness, resources, deployment constraints, language coverage and reliability.

## Findings By Metric Family

Recognition quality is reported per provider, dataset, language and acoustic profile in `quality_table.csv`. Lower WER/CER/SER is better.

Performance and RTF are reported in `performance_table.csv`. RTF below 1.0 means faster-than-real-time processing.

Noise robustness is reported in `noise_robustness_table.csv` using synthetic white-noise SNR variants where available.

Resource usage is reported in `resource_table.csv`; cloud resource rows describe client-side benchmark process observations only.

Cost and deployment constraints are reported in `cost_deployment_table.csv`. Local providers have zero direct API cost, while hardware and maintenance are not monetized.

Dataset/domain generalization is reported in `domain_generalization_table.csv`, `provider_language_matrix.csv` and `provider_domain_matrix.csv`.

Reliability and error behavior are reported in `reliability_table.csv` with sanitized error summaries.

## ROS2/COCOHRIP Recommendation

Use local providers when offline reproducibility and controlled robot-lab execution are required. Use cloud providers only when connectivity, credentials, latency variability and direct API cost are acceptable. The extended benchmark should be read as scenario trade-offs, not as one universal winner.

## Limitations

- Each dataset subset is controlled thesis-scale evidence, not a large-scale ASR corpus.
- Synthetic white noise does not cover all real laboratory acoustic conditions.
- Cloud latency depends on network, region and provider configuration.
- Cloud runs are cost-controlled and may use fewer acoustic conditions than local runs.
- Language/model mismatch can dominate multilingual results.
- Provider failures are retained in reliability tables rather than hidden.

## Canonical Extended Artifacts

- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_mls_spanish_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset`
- `artifacts/benchmark_runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset`

## Final Conclusion

The extended benchmark supports a hybrid thesis conclusion: local ASR providers are preferable for reproducible offline ROS2 experiments, while cloud ASR providers are useful as optional connected baselines when their operational constraints are acceptable.
