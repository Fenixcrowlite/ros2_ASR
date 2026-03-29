from __future__ import annotations

from pathlib import Path

from tools.archviz.cli import main
from tools.archviz.diff_graph import build_arch_diff
from tools.archviz.graph import new_graph
from tools.archviz.merge_graph import merge_graphs
from tools.archviz.render import render_mermaid
from tools.archviz.runtime_extract import (
    ManagedStackConflictError,
    _detect_conflicting_managed_processes,
)
from tools.archviz.static_extract import extract_static_graph


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_static_extractor_parses_launch_and_ast(tmp_path: Path) -> None:
    ws = tmp_path / "ros2_ws"
    pkg = ws / "src" / "demo_pkg"

    _write(
        pkg / "package.xml",
        """<?xml version=\"1.0\"?>
<package format=\"3\">
  <name>demo_pkg</name>
  <version>0.1.0</version>
  <description>demo</description>
  <maintainer email=\"maintainer@example.com\">demo</maintainer>
  <license>MIT</license>
  <depend>rclpy</depend>
</package>
""",
    )

    _write(
        pkg / "setup.py",
        """from setuptools import setup
setup(
    name=\"demo_pkg\",
    entry_points={\"console_scripts\": [\"demo_node = demo_pkg.demo_node:main\"]},
)
""",
    )

    _write(
        pkg / "launch" / "demo.launch.py",
        """from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

def generate_launch_description():
    arg = DeclareLaunchArgument(\"input_mode\", default_value=\"file\")
    return LaunchDescription([
        arg,
        Node(package=\"demo_pkg\", executable=\"demo_node\", name=\"demo_node\"),
    ])
""",
    )

    _write(
        pkg / "demo_pkg" / "demo_node.py",
        """from rclpy.node import Node
from std_msgs.msg import String
from example_interfaces.srv import Trigger

class DemoNode(Node):
    def __init__(self):
        super().__init__(\"demo_node\")
        self.pub = self.create_publisher(String, \"/demo/topic\", 10)
        self.sub = self.create_subscription(String, \"/demo/input\", self._cb, 10)
        self.srv = self.create_service(Trigger, \"/demo/srv\", self._srv)

    def _cb(self, _msg):
        return None

    def _srv(self, _req, _res):
        return _res
""",
    )

    graph = extract_static_graph(str(ws))

    node_ids = {item["id"] for item in graph["nodes"]}
    topic_names = {item["name"] for item in graph["topics"]}
    service_names = {item["name"] for item in graph["services"]}
    launch_files = {item["file"] for item in graph["launches"]}

    assert "/demo_node" in node_ids
    assert "/demo/topic" in topic_names
    assert "/demo/input" in topic_names
    assert "/demo/srv" in service_names
    assert "demo.launch.py" in launch_files


def test_merge_policy_marks_states() -> None:
    static_graph = new_graph("static", "/tmp/ws")
    static_graph["nodes"] = [{"id": "/a", "name": "a", "evidence": ["static_ast"]}]
    static_graph["topics"] = [
        {"name": "/t", "type": "std_msgs/msg/String", "evidence": ["static_ast"]}
    ]
    static_graph["services"] = [{"name": "/s", "type": "demo/srv/Do", "evidence": ["static_ast"]}]
    static_graph["edges"] = [
        {
            "kind": "topic",
            "direction": "pub",
            "node": "/a",
            "name": "/t",
            "type": "std_msgs/msg/String",
            "evidence": ["static_ast"],
        }
    ]

    runtime_graph = new_graph("runtime", "/tmp/ws")
    runtime_graph["nodes"] = [
        {"id": "/a", "name": "a", "evidence": ["runtime_cli"]},
        {"id": "/b", "name": "b", "evidence": ["runtime_cli"]},
    ]
    runtime_graph["topics"] = [
        {"name": "/t", "type": "std_msgs/msg/String", "evidence": ["runtime_cli"]},
        {"name": "/runtime_only", "type": "std_msgs/msg/Int32", "evidence": ["runtime_cli"]},
    ]

    merged = merge_graphs(static_graph, runtime_graph)

    node_state = {item["id"]: item["state"] for item in merged["nodes"]}
    topic_state = {item["name"]: item["state"] for item in merged["topics"]}

    assert node_state["/a"] == "both"
    assert node_state["/b"] == "observed_only"
    assert topic_state["/t"] == "both"
    assert topic_state["/runtime_only"] == "observed_only"


def test_diff_generator_reports_changes() -> None:
    previous = {
        "nodes": [{"id": "/a"}],
        "topics": [{"name": "/t", "type": "std_msgs/msg/String"}],
        "services": [{"name": "/s", "type": "demo/srv/Old"}],
        "edges": [
            {
                "kind": "topic",
                "direction": "pub",
                "node": "/a",
                "name": "/t",
                "type": "std_msgs/msg/String",
            }
        ],
        "runtime_errors": [],
    }
    current = {
        "nodes": [{"id": "/a"}, {"id": "/b"}],
        "topics": [{"name": "/t", "type": "std_msgs/msg/String"}],
        "services": [{"name": "/s", "type": "demo/srv/New"}],
        "edges": [
            {
                "kind": "topic",
                "direction": "sub",
                "node": "/b",
                "name": "/t",
                "type": "std_msgs/msg/String",
            }
        ],
        "runtime_errors": ["example runtime error"],
    }

    markdown = build_arch_diff(previous, current)

    assert "# Architecture Changelog" in markdown
    assert "/b" in markdown
    assert "service /s: demo/srv/Old -> demo/srv/New" in markdown
    assert "Connectivity" in markdown
    assert "runtime_errors.md" in markdown


def test_renderer_generates_mermaid_files(tmp_path: Path) -> None:
    merged_graph = {
        "nodes": [
            {"id": "/asr_server_node", "package": "asr_ros", "state": "both"},
            {"id": "/audio_capture_node", "package": "asr_ros", "state": "expected_only"},
        ],
        "topics": [
            {"name": "/asr/text", "state": "both"},
            {"name": "/asr/metrics", "state": "expected_only"},
        ],
        "services": [
            {
                "name": "/asr/recognize_once",
                "type": "asr_interfaces/srv/RecognizeOnce",
                "state": "both",
            }
        ],
        "actions": [],
        "edges": [
            {
                "kind": "topic",
                "direction": "pub",
                "node": "/asr_server_node",
                "name": "/asr/text",
                "type": "asr_interfaces/msg/AsrResult",
                "state": "both",
            },
            {
                "kind": "topic",
                "direction": "pub",
                "node": "/asr_server_node",
                "name": "/asr/metrics",
                "type": "asr_interfaces/msg/AsrMetrics",
                "state": "expected_only",
            },
            {
                "kind": "service",
                "direction": "server",
                "node": "/asr_server_node",
                "name": "/asr/recognize_once",
                "type": "asr_interfaces/srv/RecognizeOnce",
                "state": "both",
            },
        ],
    }

    files = render_mermaid(merged_graph, str(tmp_path))

    assert files["mindmap"].exists()
    assert files["flow"].exists()
    assert files["sequence"].exists()

    flow_text = files["flow"].read_text(encoding="utf-8")
    assert "flowchart LR" in flow_text
    assert "expectedOnly" in flow_text
    assert "-.->" in flow_text


def test_runtime_extractor_detects_conflicting_managed_stack() -> None:
    project_root = Path("/tmp/demo_project")
    ps_output = "\n".join(
        [
            "101 python something_else.py",
            (
                "202 /usr/bin/python3 "
                "/tmp/demo_project/ros2_ws/install/asr_runtime_nodes/lib/"
                "asr_runtime_nodes/asr_orchestrator_node"
            ),
            (
                "303 /usr/bin/python3 "
                "/tmp/other_project/ros2_ws/install/asr_runtime_nodes/lib/"
                "asr_runtime_nodes/asr_orchestrator_node"
            ),
        ]
    )

    conflicts = _detect_conflicting_managed_processes(
        project_root,
        ps_output=ps_output,
        exclude_pids={101},
    )

    assert conflicts == [
        (
            202,
            (
                "/usr/bin/python3 "
                "/tmp/demo_project/ros2_ws/install/asr_runtime_nodes/lib/"
                "asr_runtime_nodes/asr_orchestrator_node"
            ),
        )
    ]


def test_archviz_cli_returns_non_zero_for_managed_stack_conflict(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    def _raise_conflict(*_args, **_kwargs):
        raise ManagedStackConflictError("managed stack conflict")

    monkeypatch.setattr("tools.archviz.cli.extract_runtime_graph", _raise_conflict)

    exit_code = main(
        ["runtime", "--ws", str(tmp_path / "ros2_ws"), "--out", str(tmp_path / "out")]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "managed stack conflict" in captured.err
