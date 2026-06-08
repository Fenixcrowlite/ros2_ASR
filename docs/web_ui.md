# Web UI

The browser UI is a local control center backed by the FastAPI gateway in
`ros2_ws/src/asr_gateway`. The frontend files live in `web_ui/frontend`.

## Start

```bash
make up
```

Default address:

```text
http://127.0.0.1:8088
```

Stop the managed process:

```bash
make down
```

Verify the served frontend, gateway endpoints, runtime controls, provider
validation responses, and one bundled sample transcription while the stack is
running:

```bash
make test-gateway-smoke
```

If the gateway is exposed through another host port, pass the public URL:

```bash
make test-gateway-smoke GATEWAY_URL=http://127.0.0.1:18088
```

Use `GATEWAY_SMOKE_ARGS=--skip-recognition` when you only want a lightweight
HTTP endpoint check without loading the local Whisper model.

Expose the UI on the LAN:

```bash
make up-lan
```

Useful variables:

```bash
make up GATEWAY_PORT=8090
make up GATEWAY_STACK=runtime
make up RUNTIME_PROFILE=huggingface_local_runtime PROVIDER_PROFILE=providers/huggingface_local
```

## Main Pages

- Dashboard: system state, recent runs, and quick status.
- Runtime: start and stop sessions, transcribe files, and inspect live output.
  Runtime reconfigure is available while the session is idle; stop the current
  session before applying changed provider/audio settings.
- Providers: inspect provider profiles, presets, and availability.
- Profiles: view and validate runtime, provider, dataset, and benchmark
  profiles.
- Datasets: list, validate, and import dataset manifests.
- Benchmark: launch configured benchmark profiles.
- Results: view run summaries, compare providers, and export reports.
- Logs: inspect project logs through gateway endpoints.
- Secrets: check provider credential status and configure local secret inputs.

## Boundary

Frontend code should call the gateway API wrappers in `web_ui/frontend/js/api.js`.
ROS calls, filesystem reads, credential inspection, and artifact parsing belong
behind `asr_gateway`.

## Backend Entry Point

The gateway console entry point is:

```text
asr_gateway_server
```

The `make up` flow is the preferred start path because it handles ROS build,
environment setup, and frontend serving together.

Expected public routes after `make up`:

- `/` and `/ui/` serve the browser UI.
- `/openapi.json` exposes the FastAPI schema.
- `/api/health`, `/api/dashboard`, `/api/runtime/*`, `/api/providers/*`,
  `/api/secrets/*`, `/api/datasets/*`, `/api/benchmark/*`,
  `/api/results/*`, `/api/diagnostics/*`, `/api/logs`, and `/api/artifacts`
  are exercised by `make test-gateway-smoke`.
