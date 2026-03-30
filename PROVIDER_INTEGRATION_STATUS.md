# Provider Integration Status

| Provider | Canonical Adapter | Backend Substrate | Auth Model | Batch | Streaming | Readiness | Notes |
|---|---|---|---|---|---|---|---|
| whisper | `asr_provider_whisper.WhisperProvider` | `asr_backend_whisper` | local none | yes | no | usable | Honest local baseline; empty non-silent transcript is degraded explicitly. |
| vosk | `asr_provider_vosk.VoskProvider` | `asr_backend_vosk` | local model path | yes | yes | usable | Requires real Vosk model directory. |
| google | `asr_provider_google.GoogleProvider` | `asr_backend_google` | service account JSON | yes | yes | conditionally usable | Real integration; credentials and network required. |
| aws | `asr_provider_aws.AwsProvider` | `asr_backend_aws` | AWS profile / keys / SSO | yes | yes | conditionally usable | Real integration; bucket/region/auth required. |
| azure | `asr_provider_azure.AzureProvider` | `asr_backend_azure` | speech key + region | yes | yes | conditionally usable | Real integration; credentials and network required. |
| mock | none in canonical provider layer | `asr_backend_mock` only | none | legacy only | legacy only | non-canonical | Keep for tests/compatibility, not as a benchmarked provider profile. |

## Provider Layer Assessment

Good:

- one adapter contract for runtime and benchmark paths
- preset merge logic centralized in `asr_provider_base.catalog`
- secret resolution centralized in `asr_config.secrets`

Weaknesses:

- cloud readiness remains environment-dependent
- adapter layer still sits on top of legacy backend substrate, so the codebase carries both abstractions at once
- provider capability preview in gateway falls back to heuristics when adapter instantiation fails

## Repair Performed

- provider profiles now truly control adapter class via the `adapter` field; the field is no longer decorative.
- default benchmark operator path now exercises these provider adapters through `BenchmarkOrchestrator`, not through the old backend-centric benchmark runner.
