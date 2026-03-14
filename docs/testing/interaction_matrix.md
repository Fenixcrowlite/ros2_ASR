# Interaction Matrix

## Provider × Capability
- `whisper` × streaming
- `whisper` × timestamps
- `whisper` × fallback-to-mock on backend failure
- `azure` × credentials validation
- `azure` × unsupported streaming

## Config × Override Source
- base defaults × selected profile
- deployment defaults × selected profile
- selected profile × launch overrides
- env overrides × ROS/session overrides

## Benchmark × Storage
- benchmark profile × metric profiles
- benchmark run × artifact layout completeness
- comparison export × persisted run summaries

## Gateway × GUI
- runtime start/stop/recognize × live runtime page updates
- benchmark queue/run completion × results/history visibility
- diagnostics issues × logs/diagnostics page visibility
- secret refs × providers/secrets UX

## User Action × State
- start runtime when idle
- start runtime when already active
- stop runtime when active
- benchmark run followed by results navigation
- navigation to diagnostics after failed/missing secret state

## Pruning Strategy
- Real cloud/network interactions are excluded from fast baseline.
- Full ROS graph combinations are reserved for `ros`-marked expansion.
- Impossible combinations are documented rather than force-tested artificially.
