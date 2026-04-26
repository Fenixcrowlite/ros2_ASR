# Release Packaging

## Команда

```bash
make dist
```

## Что внутри

- исходники,
- docs,
- scripts,
- sample data,
- результаты bench.

## Защита

- `scripts/secret_scan.sh` перед упаковкой.
- исключаются build/install/log/cache/.git/.venv/секреты.

## Связанные

- [[07_Tooling/Scripts_Catalog]]
- [[09_Quality_CI/CI_Pipeline]]
