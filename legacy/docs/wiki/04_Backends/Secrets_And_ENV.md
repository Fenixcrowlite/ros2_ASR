# Secrets And ENV

## Политика

- ключи не коммитятся,
- используются ENV + локальный `configs/commercial.yaml`.

## Google

- `GOOGLE_APPLICATION_CREDENTIALS`
- optional `GOOGLE_CLOUD_PROJECT`

## AWS

- `AWS_PROFILE` или `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_S3_BUCKET` (`ASR_AWS_S3_BUCKET` and `AWS_TRANSCRIBE_BUCKET` remain accepted)

## Azure

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

## Связанные

- [[06_Operations/Google_STT_Test_Playbook]]
- [[../../commercial_setup]]
