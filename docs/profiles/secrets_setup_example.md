# Secrets Setup Example

1. Put secret refs in `secrets/refs/*.yaml`.
2. Put raw credential files under ignored folders (`secrets/google/`, `secrets/azure/`, `secrets/aws/`, `secrets/local/`).
3. Keep provider configs using `credentials_ref` only.
4. Use the provider-native auth source:
   - `google`: service-account JSON file
   - `aws`: `AWS_PROFILE` + shared AWS config / IAM Identity Center (SSO), or native AWS access keys / shared config; `AWS_S3_BUCKET` supplies the Transcribe media bucket
   - `azure`: `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION`
5. Use file refs only when the provider itself has a native file format.

## AWS note

When AWS uses IAM Identity Center / SSO, treat auth as two layers:
1. sign-in session
2. temporary role credentials

The GUI `Secrets` page shows both separately. A sign-in session may already be expired while existing role credentials still let runtime and benchmark calls continue for a while. The same page can start a native `aws sso login` flow through the gateway to refresh the session.

AWS provider startup requires `region` and `s3_bucket`. The provider profile maps
these from `AWS_REGION` and `AWS_S3_BUCKET`; `ASR_AWS_S3_BUCKET` and the older
`AWS_TRANSCRIBE_BUCKET` remain accepted as compatibility fallbacks.

## Azure note

Azure still uses native env vars:

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`
- optional `ASR_AZURE_ENDPOINT`

To keep GUI setup convenient without storing secrets in tracked YAML, the platform can inject these native env vars from the local ignored file `secrets/local/runtime.env`. The `Secrets` page writes and validates that file, while runtime/provider initialization keeps using the same env-based secret-ref model.

Never store raw credentials inline in tracked provider YAML.
