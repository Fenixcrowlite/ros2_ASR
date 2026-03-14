# Secrets Layout

- `refs/`: secret references used by provider profiles.
- `azure/`, `google/`, `aws/`, `local/`: local secret material (ignored by git).

Credentials must not be stored inline in provider YAML; use `credentials_ref` only.

Current native cloud layout:
- `google`: `secrets/google/service-account.json`
- `aws`: `AWS_PROFILE` or native AWS access-key envs / shared config
- `azure`: `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION`
