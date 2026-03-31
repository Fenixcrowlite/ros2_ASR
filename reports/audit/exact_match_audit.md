# Exact Match Audit

Audit date: `2026-03-31`

## Canonical semantics

- Canonical metric key: `sample_accuracy`
- Canonical user-facing meaning: `Exact Match Rate`
- Canonical boolean per-sample support field: `quality_support.exact_match`
- Canonical definition:
  - `exact_match = reference_has_content and normalized_reference == normalized_hypothesis`
  - it is not derived from `cer == 0`
  - it is not valid when the normalized reference is empty

Primary implementation:

- [quality.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/quality.py)
- [plugins.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/plugins.py)
- [summary.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/summary.py)

## Findings

| Surface | Status | Finding | Resolution |
|---|---|---|---|
| Backend metric computation | correct | `sample_accuracy` already came from `support.exact_match` in the metric plugin. | No logic fix required. |
| Summary aggregation | correct | Aggregate `sample_accuracy` already used `exact_match` counts rather than `CER==0`. | Added regression tests to lock the behavior. |
| Frontend sample inspection reconstruction | fixed | `results.js` treated `normalized_reference == normalized_hypothesis` as exact match even when the normalized reference was empty, and it incorrectly fell back to hypothesis lengths for WER/CER denominators. | Patched the JS reconstruction to mirror backend semantics exactly. |
| Frontend/provider summary labels | fixed | Aggregate `sample_accuracy` was displayed as `Exact Match`, which is ambiguous because the value is a rate, not a boolean. | Renamed aggregate labels to `Exact Match Rate`. |
| Markdown/report labels | fixed | Canonical report scripts used `Accuracy`, which was underspecified. | Renamed to `Exact Match Rate`. |
| Test seed artifacts | fixed | `tests.utils.project.seed_benchmark_run` derived `sample_accuracy` from `wer/cer`, which could encode the wrong semantics in seeded benchmark artifacts. | Added an explicit override so test artifacts can model exact-match semantics independently. |

## Files changed for this audit

- [definitions.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/definitions.py)
- [results.js](/home/fenix/Desktop/ros2ws/web_ui/frontend/js/pages/results.js)
- [benchmark.js](/home/fenix/Desktop/ros2ws/web_ui/frontend/js/pages/benchmark.js)
- [generate_report.py](/home/fenix/Desktop/ros2ws/scripts/generate_report.py)
- [run_external_dataset_suite.py](/home/fenix/Desktop/ros2ws/scripts/run_external_dataset_suite.py)
- [project.py](/home/fenix/Desktop/ros2ws/tests/utils/project.py)
- [test_quality.py](/home/fenix/Desktop/ros2ws/tests/unit/test_quality.py)
- [test_metric_engine_baseline.py](/home/fenix/Desktop/ros2ws/tests/unit/test_metric_engine_baseline.py)
- [test_metric_summary.py](/home/fenix/Desktop/ros2ws/tests/unit/test_metric_summary.py)
- [test_gateway_result_views.py](/home/fenix/Desktop/ros2ws/tests/unit/test_gateway_result_views.py)
- [test_frontend_shell.py](/home/fenix/Desktop/ros2ws/tests/gui/test_frontend_shell.py)
- [test_cli_flows.py](/home/fenix/Desktop/ros2ws/tests/integration/test_cli_flows.py)

## Validation

Commands executed:

```bash
pytest -q tests/unit/test_quality.py tests/unit/test_metric_engine_baseline.py tests/unit/test_metric_summary.py tests/unit/test_gateway_result_views.py
pytest -q tests/gui/test_frontend_shell.py
pytest -q tests/integration/test_cli_flows.py::test_generate_report_cli_uses_corpus_wer_and_input_plot_directory tests/integration/test_cli_flows.py::test_generate_report_cli_accepts_canonical_summary_json
make test-unit
```

Observed results:

- backend exact-match semantics passed
- summary aggregation stayed independent from `CER==0`
- shipped frontend assets now contain `Exact Match Rate` for aggregate displays
- shipped frontend assets no longer contain the old hypothesis-length fallback
- full non-ROS/non-legacy unit suite passed after the patch set

## Residual note

Machine-readable metric keys remain unchanged as `sample_accuracy` to preserve artifact and API compatibility. The semantic cleanup in this audit is limited to correctness guarantees and user-facing presentation.
