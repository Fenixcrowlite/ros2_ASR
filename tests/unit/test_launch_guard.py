from __future__ import annotations

from pathlib import Path

from asr_launch.launch_guard import detect_conflicting_managed_processes


def test_detect_conflicting_managed_processes_filters_workspace_nodes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    install_root = project_root / "ros2_ws" / "install"
    (project_root / "ros2_ws" / "src").mkdir(parents=True)
    (project_root / "scripts").mkdir(parents=True)
    for package in ("asr_runtime_nodes", "asr_gateway", "asr_benchmark_nodes"):
        (install_root / package).mkdir(parents=True)

    ps_output = "\n".join(
        [
            f"101 {install_root}/asr_runtime_nodes/lib/asr_runtime_nodes/audio_input_node --ros-args",
            f"102 {install_root}/asr_gateway/lib/asr_gateway/asr_gateway_server --ros-args",
            f"103 {install_root}/asr_benchmark_nodes/lib/asr_benchmark_nodes/benchmark_manager_node --ros-args",
            "104 /usr/bin/python3 unrelated_process.py",
        ]
    )

    conflicts = detect_conflicting_managed_processes(ps_output, project_root=project_root)

    assert [item["pid"] for item in conflicts] == [101, 102, 103]


def test_detect_conflicting_managed_processes_excludes_requested_pids(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    install_root = project_root / "ros2_ws" / "install"
    (project_root / "ros2_ws" / "src").mkdir(parents=True)
    (project_root / "scripts").mkdir(parents=True)
    (install_root / "asr_runtime_nodes").mkdir(parents=True)

    ps_output = (
        f"201 {install_root}/asr_runtime_nodes/lib/asr_runtime_nodes/asr_orchestrator_node --ros-args\n"
        f"202 {install_root}/asr_runtime_nodes/lib/asr_runtime_nodes/vad_segmenter_node --ros-args\n"
    )

    conflicts = detect_conflicting_managed_processes(
        ps_output,
        project_root=project_root,
        exclude_pids={201},
    )

    assert [item["pid"] for item in conflicts] == [202]
