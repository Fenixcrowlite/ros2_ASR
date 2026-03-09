"""Runtime architecture extractor based on ROS2 CLI inspection."""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.archviz.graph import GraphBuilder, dedupe_sorted, new_graph, normalize_node_name
from tools.archviz.static_extract import discover_launches


@dataclass
class LaunchEntry:
    """Executable launch descriptor for runtime probing."""

    package: str
    file: str
    path: str
    args: dict[str, str]
    declared_args: list[str]


def _run_cmd(cmd: list[str], timeout_sec: int = 10) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_sec,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out_stdout = exc.stdout
        if isinstance(timed_out_stdout, bytes):
            decoded_stdout = timed_out_stdout.decode("utf-8", errors="replace")
        else:
            decoded_stdout = timed_out_stdout or ""
        return 124, decoded_stdout, f"command timed out: {' '.join(cmd)}"


def _load_profiles_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"profiles": {}}

    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Optional fallback for regular YAML if PyYAML is available in environment.
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)  # noqa: S506
        return loaded if isinstance(loaded, dict) else {"profiles": {}}
    except Exception:
        return {"profiles": {}}


def _build_full_profile(ws: str) -> list[LaunchEntry]:
    launches = discover_launches(ws)

    preferred: list[tuple[str, str]] = [
        ("asr_ros", "demo.launch.py"),
        ("asr_ros", "bringup.launch.py"),
    ]
    preferred_keys = set(preferred)

    key_to_launch: dict[tuple[str, str], dict[str, Any]] = {
        (str(item.get("package", "")), str(item.get("file", ""))): item for item in launches
    }

    ordered: list[dict[str, Any]] = []
    for pref_key in preferred:
        item = key_to_launch.get(pref_key)
        if item is not None:
            ordered.append(item)

    for item in launches:
        key = (str(item.get("package", "")), str(item.get("file", "")))
        if key in preferred_keys:
            continue
        ordered.append(item)

    result: list[LaunchEntry] = []
    for item in ordered:
        args: dict[str, str] = {}
        declared_args = [str(arg) for arg in item.get("declared_args", [])]
        if "input_mode" in declared_args:
            args["input_mode"] = "file"

        result.append(
            LaunchEntry(
                package=str(item.get("package", "unknown")),
                file=str(item.get("file", "")),
                path=str(item.get("path", "")),
                args=args,
                declared_args=declared_args,
            )
        )
    return result


def _profile_launches(ws: str, profile: str, profile_file: Path) -> list[LaunchEntry]:
    discovered_full = _build_full_profile(ws)
    if profile == "full":
        return discovered_full

    data = _load_profiles_yaml(profile_file)
    requested = data.get("profiles", {}).get(profile, {}).get("launches", [])
    entries: list[LaunchEntry] = []
    for item in requested:
        if not isinstance(item, dict):
            continue
        entries.append(
            LaunchEntry(
                package=str(item.get("package", "unknown")),
                file=str(item.get("file", "")),
                path=str(item.get("path", "")),
                args={str(k): str(v) for k, v in dict(item.get("args", {})).items()},
                declared_args=[str(arg) for arg in item.get("declared_args", [])],
            )
        )

    return entries if entries else discovered_full


def _parse_list_with_type(output: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if " [" not in line or not line.endswith("]"):
            continue
        name, type_part = line.rsplit(" [", maxsplit=1)
        result.append((name.strip(), type_part[:-1].strip()))
    return result


def _parse_node_info(node_name: str, output: str) -> dict[str, list[tuple[str, str]]]:
    sections: dict[str, list[tuple[str, str]]] = {
        "publishers": [],
        "subscribers": [],
        "service_servers": [],
        "service_clients": [],
        "action_servers": [],
        "action_clients": [],
    }
    section_map = {
        "Publishers": "publishers",
        "Subscribers": "subscribers",
        "Service Servers": "service_servers",
        "Service Clients": "service_clients",
        "Action Servers": "action_servers",
        "Action Clients": "action_clients",
    }

    current_section = ""
    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.endswith(":"):
            title = stripped[:-1]
            current_section = section_map.get(title, "")
            continue

        if not current_section:
            continue

        if ":" not in stripped:
            continue
        left, right = stripped.split(":", maxsplit=1)
        name = left.strip()
        value_type = right.strip()
        if not name:
            continue
        sections[current_section].append((name, value_type or "unknown"))

    return sections


def _parse_topic_info_verbose(output: str) -> list[str]:
    nodes: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Node name:"):
            _, value = stripped.split(":", maxsplit=1)
            node_name = value.strip()
            if node_name:
                nodes.append(normalize_node_name(node_name))
    return dedupe_sorted(nodes)


def _collect_runtime_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "nodes": [],
        "topics": [],
        "services": [],
        "actions": [],
        "edges": [],
        "errors": [],
    }

    rc, stdout, stderr = _run_cmd(["ros2", "node", "list"], timeout_sec=10)
    if rc != 0:
        snapshot["errors"].append(f"ros2 node list failed: {stderr.strip()}")
        return snapshot

    runtime_nodes = [
        normalize_node_name(line.strip()) for line in stdout.splitlines() if line.strip()
    ]
    snapshot["nodes"].extend(
        {
            "id": node_name,
            "name": node_name.rsplit("/", maxsplit=1)[-1],
            "namespace": "/",
            "package": "unknown",
            "executable": "unknown",
        }
        for node_name in runtime_nodes
    )

    for node_name in runtime_nodes:
        rc, node_out, node_err = _run_cmd(["ros2", "node", "info", node_name], timeout_sec=10)
        if rc != 0:
            snapshot["errors"].append(f"ros2 node info {node_name} failed: {node_err.strip()}")
            continue
        parsed = _parse_node_info(node_name, node_out)

        for topic_name, topic_type in parsed["publishers"]:
            snapshot["topics"].append({"name": topic_name, "type": topic_type})
            snapshot["edges"].append(
                {
                    "kind": "topic",
                    "direction": "pub",
                    "node": node_name,
                    "name": topic_name,
                    "type": topic_type,
                }
            )

        for topic_name, topic_type in parsed["subscribers"]:
            snapshot["topics"].append({"name": topic_name, "type": topic_type})
            snapshot["edges"].append(
                {
                    "kind": "topic",
                    "direction": "sub",
                    "node": node_name,
                    "name": topic_name,
                    "type": topic_type,
                }
            )

        for srv_name, srv_type in parsed["service_servers"]:
            snapshot["services"].append({"name": srv_name, "type": srv_type})
            snapshot["edges"].append(
                {
                    "kind": "service",
                    "direction": "server",
                    "node": node_name,
                    "name": srv_name,
                    "type": srv_type,
                }
            )

        for srv_name, srv_type in parsed["service_clients"]:
            snapshot["services"].append({"name": srv_name, "type": srv_type})
            snapshot["edges"].append(
                {
                    "kind": "service",
                    "direction": "client",
                    "node": node_name,
                    "name": srv_name,
                    "type": srv_type,
                }
            )

        for action_name, action_type in parsed["action_servers"]:
            snapshot["actions"].append({"name": action_name, "type": action_type})
            snapshot["edges"].append(
                {
                    "kind": "action",
                    "direction": "server",
                    "node": node_name,
                    "name": action_name,
                    "type": action_type,
                }
            )

        for action_name, action_type in parsed["action_clients"]:
            snapshot["actions"].append({"name": action_name, "type": action_type})
            snapshot["edges"].append(
                {
                    "kind": "action",
                    "direction": "client",
                    "node": node_name,
                    "name": action_name,
                    "type": action_type,
                }
            )

    rc, topic_list_out, topic_list_err = _run_cmd(["ros2", "topic", "list", "-t"], timeout_sec=10)
    if rc != 0:
        snapshot["errors"].append(f"ros2 topic list -t failed: {topic_list_err.strip()}")
    else:
        for topic_name, topic_type in _parse_list_with_type(topic_list_out):
            snapshot["topics"].append({"name": topic_name, "type": topic_type})

            rc_info, topic_info_out, topic_info_err = _run_cmd(
                ["ros2", "topic", "info", "-v", topic_name], timeout_sec=10
            )
            if rc_info != 0:
                snapshot["errors"].append(
                    f"ros2 topic info -v {topic_name} failed: {topic_info_err.strip()}"
                )
                continue
            _parse_topic_info_verbose(topic_info_out)

    rc, srv_list_out, srv_list_err = _run_cmd(["ros2", "service", "list", "-t"], timeout_sec=10)
    if rc != 0:
        snapshot["errors"].append(f"ros2 service list -t failed: {srv_list_err.strip()}")
    else:
        for srv_name, srv_type in _parse_list_with_type(srv_list_out):
            snapshot["services"].append({"name": srv_name, "type": srv_type})

    return snapshot


def _launch_cmd(entry: LaunchEntry) -> list[str]:
    cmd = ["ros2", "launch", entry.package, entry.file]
    for key, value in sorted(entry.args.items()):
        cmd.append(f"{key}:={value}")
    return cmd


def _terminate_process(proc: subprocess.Popen[str]) -> tuple[str, str]:
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    stdout = proc.stdout.read() if proc.stdout is not None else ""
    stderr = proc.stderr.read() if proc.stderr is not None else ""
    return stdout, stderr


def extract_runtime_graph(
    ws: str,
    out_dir: str,
    profile: str = "full",
    timeout_sec: int = 20,
) -> dict[str, Any]:
    """Run launch profiles and inspect active graph using ROS2 CLI."""
    ws_path = Path(ws).resolve()
    graph = new_graph(source="runtime", workspace=str(ws_path))
    builder = GraphBuilder(graph)

    if not shutil_which("ros2"):
        builder.add_runtime_error("ros2 command not found in PATH")
        return graph

    profile_file = Path(__file__).resolve().parent / "profiles.yaml"
    entries = _profile_launches(str(ws_path), profile=profile, profile_file=profile_file)
    if not entries:
        builder.add_runtime_error(f"No launch entries for profile={profile}")
        return graph

    for entry in entries:
        cmd = _launch_cmd(entry)
        cmd_str = " ".join(shlex.quote(part) for part in cmd)
        snapshot_start = time.monotonic()

        proc: subprocess.Popen[str] | None = None
        launch_error = ""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(ws_path.parent),
                env=os.environ.copy(),
            )
            time.sleep(max(timeout_sec, 1))
            snapshot = _collect_runtime_snapshot()
        except Exception as exc:
            snapshot = {
                "nodes": [],
                "topics": [],
                "services": [],
                "actions": [],
                "edges": [],
                "errors": [f"launch failed: {exc}"],
            }
        finally:
            launch_stdout = ""
            launch_stderr = ""
            if proc is not None:
                launch_stdout, launch_stderr = _terminate_process(proc)
                if proc.returncode not in (0, None, 130):
                    launch_error = (
                        f"launch exited with code={proc.returncode}: {entry.package}/{entry.file}"
                    )

        duration_sec = round(time.monotonic() - snapshot_start, 3)

        for node in snapshot["nodes"]:
            builder.add_node(node, evidence=["runtime_cli"])
        for topic in snapshot["topics"]:
            builder.add_topic(topic, evidence=["runtime_cli"])
        for service in snapshot["services"]:
            builder.add_service(service, evidence=["runtime_cli"])
        for action in snapshot["actions"]:
            builder.add_action(action, evidence=["runtime_cli"])
        for edge in snapshot["edges"]:
            builder.add_edge(edge, evidence=["runtime_cli"])

        errors = [str(err) for err in snapshot.get("errors", []) if err]
        if launch_error:
            errors.append(launch_error)
        if launch_stderr.strip():
            errors.append(
                f"launch stderr ({entry.package}/{entry.file}): {launch_stderr.strip()[:1000]}"
            )

        for error in errors:
            builder.add_runtime_error(error)

        builder.add_snapshot(
            {
                "launch": {
                    "package": entry.package,
                    "file": entry.file,
                    "path": entry.path,
                    "args": entry.args,
                    "command": cmd_str,
                },
                "duration_sec": duration_sec,
                "errors": errors,
                "stdout_tail": launch_stdout.strip()[-1000:],
                "stderr_tail": launch_stderr.strip()[-1000:],
            }
        )

    runtime_errors_path = Path(out_dir) / "runtime_errors.md"
    runtime_errors_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Runtime Extraction Errors", ""]
    if graph["runtime_errors"]:
        lines.extend([f"- {err}" for err in graph["runtime_errors"]])
    else:
        lines.append("No runtime errors were recorded.")
    runtime_errors_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return graph


def shutil_which(binary: str) -> str | None:
    """Small wrapper to avoid importing full shutil in tests."""
    from shutil import which

    return which(binary)
