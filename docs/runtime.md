# Runtime

The runtime pipeline is implemented in `ros2_ws/src/asr_runtime_nodes` and started through launch files in `ros2_ws/src/asr_launch`.

## Choose the correct launch mode

Use the full local stack when you want the browser UI, gateway API, and runtime together:

```bash
make up
```

Open:

```text
http://127.0.0.1:8088
```

Stop the managed stack with:

```bash
make down
```

Use the minimal ROS 2 runtime when you only need the runtime nodes and ROS topics:

```bash
make up-runtime
```

`make up-runtime` runs in the foreground. Stop it with `Ctrl+C`. It does not start the browser UI.

## Inspect the active ROS 2 graph

Keep the runtime running in one terminal. Open a second terminal:

```bash
cd ros2_ASR
make rqt
```

The expected runtime path is:

1. `audio_input_node` publishes audio chunks;
2. `audio_preprocess_node` converts transport audio into a consistent format;
3. `vad_segmenter_node` emits bounded speech segments;
4. `asr_orchestrator_node` calls the selected provider adapter;
5. normalized results and diagnostics are published.

The provider adapter is called inside the orchestrator. Whisper, Vosk, Hugging Face, Azure, Google, and AWS adapters therefore do not appear as separate ROS 2 nodes in `rqt_graph`.

## Default first-run behavior

The default runtime uses:

```text
RUNTIME_PROFILE=default_runtime
PROVIDER_PROFILE=providers/whisper_local
```

The default profile reads the bundled sample audio, converts it to 16 kHz mono, segments speech with energy-based VAD, and routes the segment through local Whisper.

The default Whisper preset is CPU-safe. The first transcription can take longer because the selected model may be downloaded and cached locally. Later runs reuse the cached model.

## Select another provider

Pass the provider profile explicitly. Hugging Face modes use dedicated runtime profiles because they expose provider-specific runtime settings.

```bash
make up-runtime PROVIDER_PROFILE=providers/vosk_local
make up-runtime RUNTIME_PROFILE=huggingface_local_runtime PROVIDER_PROFILE=providers/huggingface_local
make up RUNTIME_PROFILE=huggingface_api_runtime PROVIDER_PROFILE=providers/huggingface_api
make up PROVIDER_PROFILE=providers/azure_cloud
make up PROVIDER_PROFILE=providers/google_cloud
make up PROVIDER_PROFILE=providers/aws_cloud
```

Vosk requires downloaded models:

```bash
make setup-vosk
```

Hosted and cloud providers require local configuration values and sometimes provider-side resources. Read [Provider environment setup](provider_env.md), [ASR backend activation reference](asr_backends.md), and [Provider-specific CLI checks](provider_cli.md) before using them.

## Runtime profiles

Runtime profiles live under `configs/runtime/`. They control:

- audio source;
- sample rate and channel count;
- chunk size and replay rate;
- preprocessing behavior;
- VAD thresholds and segment duration limits;
- active provider profile;
- language and processing mode;
- session limits and startup behavior.

Provider profiles live under `configs/providers/` and are loaded by `asr_provider_base` through the adapter path declared in each YAML file.

## Direct lower-level launcher

The lower-level runtime script is available for debugging:

```bash
bash scripts/run_demo.sh
```

Prefer the `make` targets for normal use because they apply the expected build and environment steps.

## Common runtime problems

### Another managed ASR stack is already running

Stop the browser UI stack first:

```bash
make down
```

If a minimal foreground runtime is running, return to its terminal and press `Ctrl+C`.

### The browser UI does not open

Confirm that the full stack, not the minimal runtime, was started:

```bash
make up
```

Then open:

```text
http://127.0.0.1:8088
```

### Port 8088 is already used

Choose another port:

```bash
make up GATEWAY_PORT=8090
```

Open:

```text
http://127.0.0.1:8090
```
