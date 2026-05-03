# Audit Phase 7: Cleanup Plan

## Low-risk / high-value completed

- moved `make bench` to canonical benchmark core
- aligned `make report` with canonical summary artifacts
- expanded report generator to support canonical summary schema
- repaired logs tab backend/frontend contract
- explicitly marked legacy benchmark wrapper paths

## Medium-risk cleanup recommended next

1. Move legacy flat benchmark configs under a dedicated `legacy/` subtree.
2. Mark `asr_ros` and `asr_backend_*` packages as compatibility generation in docs and package READMEs.
3. Rework `live_sample_eval.py` to consume provider profiles and canonical export helpers.

## High-risk cleanup deferred

- physical deletion of legacy ROS/runtime packages
- full migration of all wiki/generated docs to the canonical architecture
- collapsing all old backend wrappers in one pass
