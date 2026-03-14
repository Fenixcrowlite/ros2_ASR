# Secrets Setup Example

1. Put secret refs in `secrets/refs/*.yaml`.
2. Put raw credential files under ignored folders (`secrets/google/`, `secrets/azure/`, `secrets/aws/`, `secrets/local/`).
3. Keep provider configs using `credentials_ref` only.
4. Use the provider-native auth source:
   - `google`: service-account JSON file
   - `aws`: `AWS_PROFILE` or native AWS access keys / shared config
   - `azure`: `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION`
5. Use file refs only when the provider itself has a native file format.

Never store raw credentials inline in tracked provider YAML.
