# Provider Integration Status

| Provider | Canonical Package | Status | Real Path | Notes |
|---|---|---|---|---|
| Whisper local | `asr_provider_whisper` | usable | runtime + benchmark + gateway | strongest local baseline |
| Vosk local | `asr_provider_vosk` | usable | runtime + benchmark + gateway | good low-resource/streaming baseline |
| Azure Speech | `asr_provider_azure` | partial-to-usable | runtime + benchmark + gateway | depends on valid key/region/env |
| Google STT | `asr_provider_google` | partial-to-usable | runtime + benchmark + gateway | depends on service-account setup |
| AWS Transcribe | `asr_provider_aws` | partial-to-usable | runtime + benchmark + gateway | auth flow and SSO handling are the main complexity |
| Mock backend | `asr_backend_mock` | test/smoke only | legacy/test path | never treat as research baseline |

## Integration verdict

- The provider abstraction is honest in the canonical path: profile -> preset merge -> secret resolution -> initialized adapter.
- The main remaining duplication problem is not inside provider setup; it is the coexistence of old `asr_backend_*` paths beside the canonical `asr_provider_*` path.
