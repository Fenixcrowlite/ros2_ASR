# Secrets Policy

- Never print secret values.
- Never write secrets into reports, manifests, configs, logs, or benchmark outputs.
- Credential reports may show only `available`, `missing`, or `invalid`.
- Sanitized errors must redact values from environment variables whose names contain `KEY`, `TOKEN`, `SECRET`, or `PASSWORD`.
- Cloud providers must not silently fall back to mock providers when credentials are missing.

