# Configs And Profiles Refactor

## What changed

- benchmark CLI/operator flow now starts from benchmark profiles, not from `configs/default.yaml`
- report generation is aligned with canonical benchmark summaries
- legacy benchmark wrapper is explicitly documented as compatibility-only

## What should remain canonical

- provider behavior must be controlled through provider profiles and preset selection
- benchmark behavior must be controlled through benchmark + dataset + metric profiles
- gateway/runtime should only project profile state outward; they should not invent parallel config semantics

## Recommended future cleanup

1. Move legacy flat configs under `configs/legacy/`.
2. Rebase `live_sample_eval.py` on provider profiles or move it under a transitional/legacy label.
3. Reduce one-off web/demo YAMLs to documented operator presets with clear scope.
