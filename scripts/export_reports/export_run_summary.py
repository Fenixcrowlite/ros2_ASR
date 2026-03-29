#!/usr/bin/env python3
"""Export benchmark summary from run JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_imports() -> None:
    current = Path(__file__).resolve()
    project_root = current.parents[2]
    src_root = project_root / "ros2_ws" / "src"

    paths = [project_root]
    if src_root.is_dir():
        paths.extend(path for path in src_root.iterdir() if path.is_dir())

    for candidate in reversed(paths):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)


_bootstrap_imports()

from asr_reporting import export_markdown  # noqa: E402


def _json_metric_block(payload: dict[str, object], key: str) -> str:
    value = payload.get(key, {})
    return json.dumps(value, ensure_ascii=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export markdown summary")
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    summary_path = Path(args.summary_json)
    if not summary_path.exists():
        raise SystemExit(f"Summary JSON not found: {summary_path}")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Summary JSON is invalid: {exc}") from exc
    if not isinstance(summary, dict):
        raise SystemExit(f"Summary JSON root must be an object: {summary_path}")

    bullets = [
        f"run_id: {summary.get('run_id', 'unknown')}",
        f"benchmark_profile: {summary.get('benchmark_profile', '')}",
        f"dataset_id: {summary.get('dataset_id', '')}",
        f"execution_mode: {summary.get('execution_mode', 'batch')}",
        f"aggregate_scope: {summary.get('aggregate_scope', 'provider_only')}",
        f"providers: {', '.join(summary.get('providers', []))}",
        f"total_samples: {summary.get('total_samples', 0)}",
        f"successful_samples: {summary.get('successful_samples', 0)}",
        f"failed_samples: {summary.get('failed_samples', 0)}",
    ]
    if summary.get("quality_metrics"):
        bullets.append(f"overall_quality_metrics: {_json_metric_block(summary, 'quality_metrics')}")
    if summary.get("latency_metrics"):
        bullets.append(f"overall_latency_metrics: {_json_metric_block(summary, 'latency_metrics')}")
    if summary.get("reliability_metrics"):
        bullets.append(
            f"overall_reliability_metrics: {_json_metric_block(summary, 'reliability_metrics')}"
        )
    if summary.get("cost_metrics"):
        bullets.append(f"overall_cost_metrics: {_json_metric_block(summary, 'cost_metrics')}")
    for provider_summary in summary.get("provider_summaries", []):
        if not isinstance(provider_summary, dict):
            continue
        provider_name = (
            str(provider_summary.get("provider_profile", "") or "")
            or str(provider_summary.get("provider_id", "") or "")
            or str(provider_summary.get("provider_key", "") or "")
            or "unknown"
        )
        provider_preset = str(provider_summary.get("provider_preset", "") or "default")
        bullets.append(f"provider: {provider_name} (preset={provider_preset})")
        bullets.append(
            f"provider_quality_metrics: {_json_metric_block(provider_summary, 'quality_metrics')}"
        )
        bullets.append(
            f"provider_latency_metrics: {_json_metric_block(provider_summary, 'latency_metrics')}"
        )
        bullets.append(
            "provider_reliability_metrics: "
            + _json_metric_block(provider_summary, "reliability_metrics")
        )
        bullets.append(
            f"provider_cost_metrics: {_json_metric_block(provider_summary, 'cost_metrics')}"
        )
    path = export_markdown(args.output_md, f"Benchmark {summary.get('run_id', 'unknown')}", bullets)
    print(path)


if __name__ == "__main__":
    main()
