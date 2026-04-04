# web_ui/backend

Backend for the new web UI is provided by ROS2 package `asr_gateway`:

- FastAPI app module: `asr_gateway.api`
- Entry point: `asr_gateway_server`
- Default address: `http://127.0.0.1:8088`

The backend is gateway-first and should be the single control path between GUI and ROS2 runtime/benchmark services/actions.

Detailed API/UX contract is documented in:
- `docs/gui/gui_backend_contract.md`
- `docs/gui/information_architecture.md`
