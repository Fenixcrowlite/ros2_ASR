# asr_provider_azure

Modern Azure Speech adapter package for the provider-based runtime and
benchmark stack.

## Purpose

This package integrates Azure Speech through the common adapter API from
`asr_provider_base`, so Azure can be selected from profiles, benchmark plans,
and gateway UI flows without provider-specific branching in callers.

## Main Contents

- `asr_provider_azure/azure_provider.py`: `AzureProvider`, the modern adapter.

## Integration Notes

- Credentials are resolved through `asr_config` and `ProviderManager`.
- Runtime and benchmark code interact with this package only through the
  adapter contract and capability metadata.

## Relationship To Legacy Code

New code should prefer `asr_provider_azure`.
The legacy compatibility package is `asr_backend_azure`.

## Boundary

- No ROS node ownership.
- No HTTP API surface.
- No artifact/report generation.
