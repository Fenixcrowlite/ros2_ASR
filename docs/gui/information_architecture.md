# Information Architecture

## IA Goals
- Reduce cognitive load for both demo operator and engineer/researcher.
- Keep architecture-safe boundaries: GUI -> gateway -> ROS2/services/actions.
- Provide clear task order and dependency visibility.

## Core Domain Entities
- Runtime session
- Runtime profile
- Provider profile
- Credentials reference
- Dataset profile
- Dataset registry entry
- Benchmark profile
- Metric profile
- Benchmark run
- Result artifacts
- Diagnostics event

## Entity Relationship (practical)
- Runtime session uses: runtime profile + provider profile.
- Provider profile may require: credentials reference.
- Benchmark run uses: benchmark profile + dataset profile + provider set + metric profiles.
- Dataset profile points to: dataset manifest; dataset registry stores registered dataset entries.
- Results page reads: benchmark run artifacts and runtime session snapshots.

## Primary User Tasks
- Operator tasks (high frequency):
  - Check system state.
  - Start/stop runtime quickly.
  - Run simple recognition.
  - Trigger benchmark preset.
  - See immediate results and warnings.
- Engineer/research tasks:
  - Manage profiles and provider capabilities.
  - Configure credentials refs safely.
  - Import datasets and validate manifests.
  - Run benchmark matrix and compare runs.
  - Inspect diagnostics/logs and fix issues.

## Top-Level Navigation
- Dashboard
- Runtime
- Providers
- Profiles
- Datasets
- Benchmark
- Results
- Logs & Diagnostics
- Secrets

## Click-Depth Strategy
- 1 click:
  - System health
  - Runtime start/stop
  - Benchmark run trigger
  - Latest runs
- 2 clicks:
  - Provider profile validation/test
  - Dataset detail with manifest preview
  - Run detail page
- 3 clicks:
  - Advanced profile editing/export
  - Multi-run comparison and exports

## Progressive Disclosure
- By default show:
  - Status, selected profile/provider, errors, quick actions.
- Hide behind "Advanced":
  - Raw JSON/YAML payload previews.
  - Extended metadata and custom fields.
  - Low-level tuning fields.

## Page-Level IA

### Dashboard
- System status summary
- Runtime status summary
- Benchmark status summary
- Alerts + suggested actions
- Quick actions

### Runtime
- Control panel
- Live status panel
- Live transcription feed
- Session details + event timeline

### Providers
- Provider catalog with capability badges
- Provider profiles list + linked credentials
- Validate/test controls

### Profiles
- Profile-type switcher
- Summary cards
- Guided editor (basic)
- Advanced raw editor

### Datasets
- Registry table
- Import wizard panel
- Dataset details and sample preview

### Benchmark
- Step-based run builder:
  1) dataset
  2) providers
  3) scenario
  4) metrics
  5) review and run
- Run progress and history list

### Results
- Overview cards
- Run detail explorer
- Comparison table/plots
- Export actions

### Logs & Diagnostics
- Health overview
- Issues feed (errors/warnings)
- Filterable logs
- Suggested fixes

### Secrets
- Credential refs table
- Create/update ref form
- Link refs to provider profiles
- Safe validation status

## Confirmation and Safety Rules
- Explicit confirmation for destructive actions:
  - profile overwrite
  - stop runtime
  - run cancellation
- Never display secret values after save.
- File path actions are validated server-side.

## Responsive Layout Rules
- Desktop: sidebar + two-column content where helpful.
- Tablet/mobile: top nav drawer + single-column sections.
- Keep critical actions visible without horizontal scrolling.
