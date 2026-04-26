# AWS Cleanup Tests

## Что проверяется

- cleanup вызывается при success,
- cleanup вызывается при ошибке,
- cleanup не маскирует исходную ошибку.

## Контекст

AWS backend создаёт временный S3 object + Transcribe job.
Они должны удаляться в `finally` при `cleanup=true`.

## Файл тестов

`tests/unit/test_aws_backend_cleanup.py`

## Связанные

- [[04_Backends/AWS_Backend]]
