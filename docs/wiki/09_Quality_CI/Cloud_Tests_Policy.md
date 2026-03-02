# Cloud Tests Policy

## Правило

Если ENV credentials не заданы, cloud-тесты должны `skip`, а не `fail`.

## Маркер

`@pytest.mark.cloud`

## Тесты

- Google
- AWS
- Azure

## Связанные

- [[04_Backends/Secrets_And_ENV]]
- [[06_Operations/Google_STT_Test_Playbook]]
