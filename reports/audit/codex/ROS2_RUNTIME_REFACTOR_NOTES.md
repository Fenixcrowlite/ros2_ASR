# ROS2 Runtime Refactor Notes

## Stable target

- keep `asr_runtime_nodes` as the runtime control/data plane
- keep `asr_interfaces` as the transport contract
- keep `asr_launch` as canonical launch ownership

## Transitional areas

- `asr_ros` should be treated as legacy compatibility runtime code
- old benchmark node wrappers should not be promoted over `asr_benchmark_nodes`

## Practical rule

When new runtime behavior is added, it should land in:

- `asr_runtime_nodes`
- `asr_provider_*`
- `asr_gateway` only for operator projection/API glue

and not in the legacy node/backend wrappers.
