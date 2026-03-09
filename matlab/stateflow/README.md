# Full-Project Stateflow Chart

This folder contains MATLAB automation to build a hierarchical Stateflow chart for the whole ASR project.

## File
- `build_project_stateflow_chart.m` - creates a Simulink model with one Stateflow chart and fills it with:
  - ROS2 packages, launches, nodes, interfaces, edges (from `docs/arch/merged_graph.json`)
  - Web GUI backend/frontend structure and API routes
  - Scripts, tooling (`archviz`, `docsbot`), assets (`configs`, `data`, `docs`, `tests`)
  - runtime flow and error-recovery states

## MATLAB usage
Run from repository root in MATLAB:

```matlab
addpath(fullfile(pwd, 'matlab', 'stateflow'));
build_project_stateflow_chart('ModelName', 'asr_project_full_stateflow');
```

Optional refresh of architecture graph before generation:

```matlab
build_project_stateflow_chart( ...
    'ModelName', 'asr_project_full_stateflow', ...
    'RefreshArchviz', true);
```

## Requirements
- Simulink
- Stateflow
- Existing `docs/arch/merged_graph.json` (or `RefreshArchviz=true`)
