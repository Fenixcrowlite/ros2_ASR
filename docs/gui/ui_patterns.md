# UI Patterns

## Page Types
- Overview page: dashboard/results overview.
- Control page: runtime/benchmark execution.
- Management page: providers/profiles/datasets/secrets.
- Diagnostic page: logs and issue feed.

## Card Pattern
- Header: title + status badge.
- Body: key fields or summary metrics.
- Footer: primary action + secondary link.

## Table Pattern
- Fixed columns for identity and state.
- Optional detail drawer for advanced metadata.
- Actions column with explicit verbs: `Open`, `Validate`, `Run`, `Export`.

## Form Pattern
- Sections by meaning (not by raw schema key order).
- Helper text for non-obvious terms.
- Basic section first, advanced collapsible panel.

## Validation Pattern
- On input blur: field-level checks.
- On submit: full payload checks.
- Results panel:
  - blocking errors
  - warnings
  - suggestions

## Status Badge Pattern
- `Healthy`, `Running`, `Idle`, `Degraded`, `Failed`, `Unknown`.
- Always include textual state.

## Empty State Pattern
- Explain what entity is missing.
- Show exact next action.
- Include one primary CTA.

## Error State Pattern
- Show context: component + action + error text.
- Add suggested fix sentence.
- Offer retry action if safe.

## Confirm Dialog Pattern
- Used for destructive or high-impact actions:
  - stop runtime
  - overwrite profile
  - run cancellation
- Must summarize impact briefly.

## Logs Pattern
- Filters: component, severity, time window, run/session id.
- Monospace viewer with line numbers optional.
- Avoid auto-scroll hijacking unless user enabled follow mode.

## Benchmark Builder Pattern
- Stepper with locked forward progression only when current step valid.
- Review step renders immutable run summary before launch.

## Comparison Pattern
- Multi-select runs.
- Metric-centric comparison table.
- Visual cue for best value (lower is better for WER/CER/latency).

## Explainability Pattern
- Use helper labels:
  - `What is runtime profile?`
  - `What is credential ref?`
  - `What is dataset manifest?`
- Keep short and context-local.
