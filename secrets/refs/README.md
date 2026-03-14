# Secret References

Each YAML file defines a credential reference contract used by provider profiles.

Supported patterns:
- env-based (`kind: env`)
- file-based (`kind: file`)
- none/local placeholders (`kind: none`)

Raw secret material should be placed under ignored provider folders (`secrets/aws`, `secrets/azure`, `secrets/google`, `secrets/local`) or injected via environment variables.

Preferred cloud refs in the current baseline:
- `google_service_account.yaml` -> `secrets/google/service-account.json`
- `aws_profile.yaml` -> native AWS env/profile contract
- `azure_speech_key.yaml` -> native Azure env contract
