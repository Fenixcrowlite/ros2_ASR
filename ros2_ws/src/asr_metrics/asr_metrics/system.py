from __future__ import annotations

import shutil
import subprocess

import psutil


def collect_cpu_ram() -> tuple[float, float]:
    cpu = psutil.cpu_percent(interval=0.05)
    mem = psutil.Process().memory_info().rss / (1024 * 1024)
    return float(cpu), float(mem)


def collect_gpu() -> tuple[float, float]:
    if shutil.which("nvidia-smi") is None:
        return 0.0, 0.0
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return 0.0, 0.0
    if not out:
        return 0.0, 0.0
    first = out.splitlines()[0]
    util_s, mem_s = [v.strip() for v in first.split(",")[:2]]
    try:
        return float(util_s), float(mem_s)
    except ValueError:
        return 0.0, 0.0
