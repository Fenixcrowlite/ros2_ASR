# Scripts Catalog

## Runtime scripts

- `scripts/setup_env.sh`
- `scripts/run_demo.sh`
- `scripts/open_live_test_terminals.sh`
- `scripts/live_sample_eval.py`
- `scripts/run_live_sample_eval.sh`
- `scripts/run_web_ui.sh`
- [[07_Tooling/Scripts/Setup_Env_Script]]
- [[07_Tooling/Scripts/Run_Demo_Script]]
- [[07_Tooling/Scripts/Open_Live_Test_Terminals_Script]]
- [[07_Tooling/Scripts/Live_Sample_Eval_Script]]
- [[07_Tooling/Web_GUI_Control_Center]]

Notes:

- `run_demo.sh` и `open_live_test_terminals.sh` теперь работают через `asr_launch`
  и current runtime services.
- `live_sample_eval.py` остается compatibility tool, потому что проверяет также
  legacy `core|ros_service|ros_action` paths.

## Benchmark/report

- `scripts/run_benchmarks.sh`
- `scripts/generate_report.py`
- `scripts/generate_plots.py`
- `scripts/export_reports/export_run_summary.py`
- [[07_Tooling/Scripts/Run_Benchmarks_Script]]
- [[07_Tooling/Scripts/Generate_Report_Script]]

## Release

- `scripts/release_check.sh`
- `scripts/secret_scan.sh`
- `scripts/make_dist.sh`
- [[07_Tooling/Scripts/Release_Check_Script]]
- [[07_Tooling/Scripts/Secret_Scan_Script]]
- [[07_Tooling/Scripts/Make_Dist_Script]]

## Archviz launcher

- `scripts/archviz`
- root launcher `./archviz`

## Связанные

- [[10_Archviz/Archviz_Index]]
- [[06_Operations/Release_Packaging]]
