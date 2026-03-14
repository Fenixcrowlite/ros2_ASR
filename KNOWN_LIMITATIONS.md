# KNOWN_LIMITATIONS

1. Cloud E2E remains environment-dependent.
- Полный интеграционный прогон `google/aws/azure` требует валидных аккаунтов, биллинга и сети; в дефолтном CI это не выполняется.

2. AWS preflight requires boto3 or AWS CLI availability.
- Preflight использует boto3 STS путь, а при отсутствии boto3 переключается на `aws sts get-caller-identity`.
- Если в окружении нет ни boto3, ни AWS CLI, AWS job start будет отклонен fail-fast.

3. Historical logs still contain pre-fix failures.
- Старые файлы в `web_gui/logs/` включают legacy tracebacks и SSO ошибки, которые уже закрыты текущими правками.

4. Bandit warnings are not fully eliminated.
- Большинство оставшихся finding — low-severity subprocess/test-patterns в tooling-коде.

5. Shell script linting is still partial.
- `shellcheck` отсутствовал в среде, поэтому автоматическая shell static-lint стадия не была запущена.

6. Coverage remains uneven for dependency-heavy backends.
- Aggregate non-ROS coverage приемлемая, но модули `azure/vosk/whisper` требуют дополнительных mock-heavy тестов для плотного покрытия.

7. Frontend browser E2E coverage is still limited.
- Web GUI draft persistence и UI-state синхронизация проверены runtime-smoke, но без полноценного headless browser suite.

8. AWS STS preflight cache is short-term and in-memory only.
- Кэш (по умолчанию 120 секунд) ускоряет повторные старты, но может кратковременно не заметить только что истекший токен до следующей полной preflight-проверки.
