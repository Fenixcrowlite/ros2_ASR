# Remaining Issues

Generated at: `2026-03-31T12:24:00+00:00`

## No open audit-register risks remain

The items below are follow-up opportunities, not unresolved entries from the risk register.

## Follow-up technical opportunities

- [asr_metrics/system.py](ros2_ws/src/asr_metrics/asr_metrics/system.py)
  - CPU, RAM, and GPU metrics are still point-in-time samples rather than peak or stage-attributed profiles.
- [asr_gateway/api.py](ros2_ws/src/asr_gateway/asr_gateway/api.py)
  - gateway still exposes subprocess-heavy operational helpers; CI security scan intentionally focuses on canonical runtime/provider/metrics/benchmark packages instead of every tooling endpoint.
- live ROS transport introspection
  - current runtime telemetry proves delivery latency and sequence gaps, but not DDS-native queue depth.
- documentation surface outside root README
  - wiki pages and package READMEs still need a full canonical/legacy banner sweep to mirror the enforced workflow defaults everywhere.

## Why these remain open

- they are not blocking correctness or reproducibility of the canonical ASR platform
- they no longer represent the high-priority risks from the audit register
- each requires either broader documentation work or a deeper measurement model than the bounded remediation pass completed here
