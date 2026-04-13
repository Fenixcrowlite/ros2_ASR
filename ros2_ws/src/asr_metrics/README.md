# asr_metrics

Metric subsystem for benchmark evaluation.

## Responsibilities
- WER/CER quality metrics.
- Plugin-style metric engine.
- Legacy collector compatibility for previous benchmark scripts.

## Mental Model
- `engine.py` evaluates metrics for one normalized execution context.
- `definitions.py` defines what metrics exist and how they should be summarized.
- `summary.py` turns many sample-level rows into corpus-level sections used by reports and GUI.
- `semantics.py` marks the difference between legacy and canonical metric contracts.

## Read This Package In This Order
1. `asr_metrics/definitions.py`
2. `asr_metrics/engine.py`
3. `asr_metrics/quality.py`
4. `asr_metrics/summary.py`
5. `asr_metrics/semantics.py`
