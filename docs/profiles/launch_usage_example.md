# Launch Usage Examples

Runtime minimal:
```bash
ros2 launch asr_launch runtime_minimal.launch.py runtime_profile:=default_runtime provider_profile:=providers/whisper_local
```

Runtime streaming:
```bash
ros2 launch asr_launch runtime_streaming.launch.py input_mode:=mic runtime_profile:=default_runtime
```

Gateway + runtime:
```bash
ros2 launch asr_launch gateway_with_runtime.launch.py gateway_host:=127.0.0.1 gateway_port:=8088
```

Full stack dev:
```bash
ros2 launch asr_launch full_stack_dev.launch.py gateway_host:=0.0.0.0 gateway_port:=8088
```

Shortcut via Makefile:
```bash
make web-gui
```
