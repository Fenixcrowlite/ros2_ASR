# AWS Backend

Файл: `ros2_ws/src/asr_backend_aws/asr_backend_aws/backend.py`.

## API

AWS Transcribe через job + временный S3 upload.

## Ключевые настройки

- `region`
- `s3_bucket`
- `media_format`
- `cleanup` (по умолчанию true)

## Cleanup policy

В `finally` удаляются:

- Transcribe job,
- S3 объект,

и ошибки cleanup не маскируют исходную ошибку.

## Связанные

- [[09_Quality_CI/AWS_Cleanup_Tests]]
