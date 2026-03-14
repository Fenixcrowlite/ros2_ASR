# Commercial Backends Setup

Primary model in this project: `provider profile -> credentials_ref -> native provider auth source`.

## Google Cloud Speech-to-Text

1. Create service account with Speech permissions.
2. Put the JSON key under `secrets/google/service-account.json`.
3. Reference it via `secrets/refs/google_service_account.yaml`.

Optional env alternative:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/service-account.json
export GOOGLE_CLOUD_PROJECT=your-project-id
```

Optional:

```bash
export ASR_GOOGLE_MODEL=latest_long
export ASR_GOOGLE_REGION=global
export ASR_GOOGLE_ENDPOINT=speech.googleapis.com
```

If `ASR_GOOGLE_ENDPOINT` is unset, backend uses the default global Google endpoint.

## AWS Transcribe

Use native AWS auth:

- `AWS_PROFILE`
- or `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- optional `AWS_SESSION_TOKEN`
- optional `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE`

Provider settings such as bucket stay in `configs/providers/aws_cloud.yaml`.

If you use AWS SSO, you still need a live login token:

```bash
aws sso login --profile ros2ws
```

## Azure Speech

Use native Azure auth:

```bash
export AZURE_SPEECH_KEY=...
export AZURE_SPEECH_REGION=eastus
```

Optional:

```bash
export ASR_AZURE_ENDPOINT=https://<region>.api.cognitive.microsoft.com/
```

## Cloud Tests

Cloud tests are skipped by default unless credentials are available.

```bash
pytest -m cloud -q
```
