# asr_provider_base

Provider adapter contract and registry.

## Responsibilities
- Define provider lifecycle API.
- Define capabilities model.
- Centralize provider discovery/creation.
- Provide profile+secret driven provider construction (`ProviderManager`).

## Boundaries
- No ROS node behavior.
- No benchmark orchestration.
