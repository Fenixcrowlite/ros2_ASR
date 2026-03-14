# GUI / Gateway Model

## Rule
GUI must not access runtime internals directly.
All control and data access passes through gateway API.

## Gateway responsibilities
- Validate profiles/config via ROS service bridge.
- Trigger runtime session start/stop/reconfigure.
- Trigger recognize-once calls.
- Trigger benchmark runs and fetch status.
- Register/list datasets.
- Expose artifact and secret-ref metadata endpoints.

## Baseline implementation
- ROS package: `asr_gateway`
- API app: `asr_gateway.api`
- Client bridge: `asr_gateway.ros_client`
- Web skeleton: `web_ui/frontend`

## GUI baseline pages
- dashboard
- runtime control
- providers
- profiles
- datasets
- benchmark
- results
- logs/diagnostics
- secrets/credentials metadata
