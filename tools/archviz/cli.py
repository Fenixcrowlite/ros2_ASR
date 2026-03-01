"""CLI for architecture extraction and Mermaid rendering."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.archviz.diff_graph import build_arch_diff, diff_graph_files
from tools.archviz.graph import read_json, write_json
from tools.archviz.merge_graph import merge_graphs
from tools.archviz.render import render_mermaid
from tools.archviz.runtime_extract import extract_runtime_graph
from tools.archviz.static_extract import extract_static_graph


def _default_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "static": out_dir / "static_graph.json",
        "runtime": out_dir / "runtime_graph.json",
        "merged": out_dir / "merged_graph.json",
        "merged_prev": out_dir / "merged_graph_prev.json",
        "changelog": out_dir / "CHANGELOG_ARCH.md",
    }


def cmd_static(args: argparse.Namespace) -> int:
    graph = extract_static_graph(args.ws)
    out_dir = Path(args.out)
    paths = _default_paths(out_dir)
    write_json(paths["static"], graph)
    print(f"[archviz] static graph written: {paths['static']}")
    return 0


def cmd_runtime(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    graph = extract_runtime_graph(
        ws=args.ws,
        out_dir=str(out_dir),
        profile=args.profile,
        timeout_sec=args.timeout_sec,
    )
    paths = _default_paths(out_dir)
    write_json(paths["runtime"], graph)
    print(f"[archviz] runtime graph written: {paths['runtime']}")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    static_graph = read_json(Path(args.static))
    runtime_graph = read_json(Path(args.runtime))
    merged = merge_graphs(static_graph, runtime_graph)
    write_json(Path(args.out), merged)
    print(f"[archviz] merged graph written: {args.out}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    graph = read_json(Path(args.input_path))
    files = render_mermaid(graph, args.out)
    for label, path in files.items():
        print(f"[archviz] rendered {label}: {path}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    prev_path = Path(args.a)
    curr_path = Path(args.b)
    if prev_path.exists():
        output = diff_graph_files(prev_path, curr_path)
    else:
        output = build_arch_diff({}, read_json(curr_path))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    print(f"[archviz] diff changelog written: {out_path}")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _default_paths(out_dir)

    static_graph = extract_static_graph(args.ws)
    write_json(paths["static"], static_graph)

    runtime_graph = extract_runtime_graph(
        ws=args.ws,
        out_dir=str(out_dir),
        profile=args.profile,
        timeout_sec=args.timeout_sec,
    )
    write_json(paths["runtime"], runtime_graph)

    if paths["merged"].exists():
        shutil.copy2(paths["merged"], paths["merged_prev"])

    merged_graph = merge_graphs(static_graph, runtime_graph)
    write_json(paths["merged"], merged_graph)

    render_mermaid(merged_graph, str(out_dir))

    if paths["merged_prev"].exists():
        diff_text = diff_graph_files(paths["merged_prev"], paths["merged"])
    else:
        diff_text = build_arch_diff({}, merged_graph)
    paths["changelog"].write_text(diff_text, encoding="utf-8")

    print(f"[archviz] static graph: {paths['static']}")
    print(f"[archviz] runtime graph: {paths['runtime']}")
    print(f"[archviz] merged graph: {paths['merged']}")
    print(f"[archviz] changelog: {paths['changelog']}")
    mermaid_files = ", ".join(
        str(out_dir / name) for name in ("mindmap.mmd", "flow.mmd", "seq_recognize_once.mmd")
    )
    print(f"[archviz] mermaid files: {mermaid_files}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archviz", description="ROS2 architecture visualizer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_static = sub.add_parser("static", help="Extract static architecture graph from source")
    p_static.add_argument("--ws", required=True, help="Workspace path (e.g. ros2_ws)")
    p_static.add_argument("--out", required=True, help="Output directory")
    p_static.set_defaults(func=cmd_static)

    p_runtime = sub.add_parser("runtime", help="Extract runtime architecture graph via ROS2 CLI")
    p_runtime.add_argument("--ws", required=True, help="Workspace path (e.g. ros2_ws)")
    p_runtime.add_argument("--out", required=True, help="Output directory")
    p_runtime.add_argument("--profile", default="full", help="Runtime launch profile name")
    p_runtime.add_argument("--timeout-sec", type=int, default=20, help="Capture timeout per launch")
    p_runtime.set_defaults(func=cmd_runtime)

    p_merge = sub.add_parser("merge", help="Merge static and runtime graphs")
    p_merge.add_argument("--static", required=True, help="Path to static_graph.json")
    p_merge.add_argument("--runtime", required=True, help="Path to runtime_graph.json")
    p_merge.add_argument("--out", required=True, help="Path to merged_graph.json")
    p_merge.set_defaults(func=cmd_merge)

    p_render = sub.add_parser("render", help="Render Mermaid diagrams from merged graph")
    p_render.add_argument(
        "--in", dest="input_path", required=True, help="Path to merged graph json"
    )
    p_render.add_argument("--out", required=True, help="Output directory")
    p_render.add_argument(
        "--format",
        default="mermaid",
        choices=["mermaid"],
        help="Render format (currently only mermaid)",
    )
    p_render.set_defaults(func=cmd_render)

    p_diff = sub.add_parser(
        "diff", help="Generate architecture changelog between two merged graphs"
    )
    p_diff.add_argument("--a", required=True, help="Previous merged graph")
    p_diff.add_argument("--b", required=True, help="Current merged graph")
    p_diff.add_argument("--out", required=True, help="Path to markdown changelog")
    p_diff.set_defaults(func=cmd_diff)

    p_all = sub.add_parser("all", help="Run static + runtime + merge + render + diff")
    p_all.add_argument("--ws", required=True, help="Workspace path (e.g. ros2_ws)")
    p_all.add_argument("--out", required=True, help="Output directory")
    p_all.add_argument("--profile", default="full", help="Runtime launch profile name")
    p_all.add_argument("--timeout-sec", type=int, default=20, help="Capture timeout per launch")
    p_all.set_defaults(func=cmd_all)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
