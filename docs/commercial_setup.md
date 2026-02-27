# Commercial Backends Setup

Secrets must be stored in environment variables or local untracked config (`configs/commercial.yaml`).

## Google Cloud Speech-to-Text

1. Create service account with Speech permissions.
2. Download JSON key file locally.
3. Set:

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

Use IAM user/role with S3 + Transcribe access.

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...   # optional
export ASR_AWS_S3_BUCKET=your-bucket
export ASR_AWS_CLEANUP=true
```

Or configure profile:

```bash
export AWS_PROFILE=default
```

## Azure Speech

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
