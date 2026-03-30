# Concept Alignment Refactor

## Canonical conceptual chain

`input audio -> runtime or benchmark request -> provider profile resolution -> normalized ASR result -> metric evaluation -> artifact persistence -> gateway/UI projection`

## Practical consequences

- UI should not own metric semantics
- provider-specific quirks belong in provider adapters, not in page modules
- benchmark/report artifacts should be generated from canonical summaries, not from ad-hoc flat exports
- logs/diagnostics should expose source metadata and actionable context, not opaque tail text

## Repairs supporting this alignment

- canonical benchmark CLI wrapper added
- report generation aligned with canonical summary
- logs tab upgraded from raw text dump to structured diagnostic view
