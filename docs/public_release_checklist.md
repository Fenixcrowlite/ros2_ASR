# Public Repository Release Checklist

Use this checklist before sharing the repository with a supervisor, reviewer, commission member, or external contributor.

## Repository visibility

The repository must be visible without authentication before it is shared externally.

- Confirm that the GitHub repository visibility is set to **Public**.
- Open the repository in a private browser window and verify that the README is visible.
- Confirm that the public HTTPS clone command works:

```bash
git clone https://github.com/Fenixcrowlite/ros2_ASR.git
```

## Static public-release check

Run the static repository checks before the slower clean-clone and runtime checks:

```bash
make public-release-check
```

This command calls `scripts/public_release_check.sh` and runs:

- `make docs-check`;
- the repository secret scan;
- dataset registry and asset portability validation;
- a check for accidentally tracked local credential files and private-key formats;
- a check that `configs/runtime.env.example` still contains empty values only;
- a warning when the local working tree contains unreviewed changes.

The static command does not replace a clean-clone build or provider-specific runtime checks.

## Documentation consistency

The static release check already runs:

```bash
make docs-check
```

Run it directly after editing setup guides, provider YAML profiles, credential-reference metadata, CI workflow paths, or helper scripts.

## Secret safety

The static release check already runs:

```bash
bash scripts/secret_scan.sh
```

Confirm manually that:

- `secrets/local/runtime.env` is not tracked;
- `secrets/google/service-account.json` is not tracked;
- AWS local configuration files remain outside the repository;
- `configs/runtime.env.example` contains only empty values;
- screenshots, logs, and exported reports do not contain account-specific values.

## Clean-clone setup

Test from a new directory or a clean machine:

```bash
git clone https://github.com/Fenixcrowlite/ros2_ASR.git
cd ros2_ASR
make setup
make docs-check
make build
make validate-datasets
make up
```

Open:

```text
http://127.0.0.1:8088
```

In a second terminal:

```bash
cd ros2_ASR
make test-gateway-smoke
```

Stop the stack:

```bash
make down
```

## Provider-specific checks

The default gateway smoke test proves the HTTP surface and one local Whisper transcription. It does not prove every configured backend.

For each backend that you plan to demonstrate, run its activation command from [ASR backend activation reference](asr_backends.md), then validate and test it using [Provider-specific CLI checks](provider_cli.md).

At minimum, verify:

- local Whisper on CPU preset `light`;
- Vosk after `make setup-vosk`, when Vosk is part of the demonstration;
- each cloud or hosted provider only when the corresponding account configuration is available.

## ROS 2 graph inspection

For a runtime demonstration, start the minimal runtime:

```bash
make up-runtime
```

In a second terminal:

```bash
make rqt
```

Confirm that the runtime graph matches the documented pipeline. Provider adapters are called inside the orchestrator and do not appear as separate ROS 2 nodes.

## Final cleanup

Before publishing a release commit:

```bash
make clean
make public-release-check
```

Review `git status` and confirm that only intentional source and documentation changes remain.
