"""Host resource probes (CPU/RAM/GPU) used during benchmark collection."""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from dataclasses import dataclass

import psutil


def collect_cpu_ram() -> tuple[float, float]:
    """Return `(cpu_percent, current_process_ram_mb)`."""
    cpu = psutil.cpu_percent(interval=0.05)
    mem = psutil.Process().memory_info().rss / (1024 * 1024)
    return float(cpu), float(mem)


def collect_cpu_ram_sample() -> tuple[float, float]:
    """Return a non-blocking `(cpu_percent, current_process_ram_mb)` sample."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.Process().memory_info().rss / (1024 * 1024)
    return float(cpu), float(mem)


def collect_gpu() -> tuple[float, float]:
    """Return `(gpu_util_percent, gpu_memory_mb)` from first NVIDIA GPU.

    Returns `(0.0, 0.0)` when `nvidia-smi` is unavailable.
    """
    util, mem = collect_gpu_optional()
    return float(util or 0.0), float(mem or 0.0)


def collect_gpu_optional() -> tuple[float | None, float | None]:
    """Return `(gpu_util_percent, gpu_memory_mb)` or `(None, None)` when unavailable."""
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return None, None
    try:
        out = subprocess.check_output(
            [
                nvidia_smi,
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None, None
    if not out:
        return None, None
    first = out.splitlines()[0]
    util_s, mem_s = [v.strip() for v in first.split(",")[:2]]
    try:
        return float(util_s), float(mem_s)
    except ValueError:
        return None, None


@dataclass(slots=True)
class ResourceSampleSummary:
    """Aggregated CPU/RAM/GPU samples collected over one request or run."""

    cpu_percent_mean: float | None = None
    cpu_percent_peak: float | None = None
    memory_mb_mean: float | None = None
    memory_mb_peak: float | None = None
    gpu_util_percent_mean: float | None = None
    gpu_util_percent_peak: float | None = None
    gpu_memory_mb_mean: float | None = None
    gpu_memory_mb_peak: float | None = None

    def as_metrics(self) -> dict[str, float | None]:
        """Flatten aggregate samples into metric-style key/value pairs."""
        return {
            "cpu_percent_mean": self.cpu_percent_mean,
            "cpu_percent_peak": self.cpu_percent_peak,
            "memory_mb_mean": self.memory_mb_mean,
            "memory_mb_peak": self.memory_mb_peak,
            "gpu_util_percent_mean": self.gpu_util_percent_mean,
            "gpu_util_percent_peak": self.gpu_util_percent_peak,
            "gpu_memory_mb_mean": self.gpu_memory_mb_mean,
            "gpu_memory_mb_peak": self.gpu_memory_mb_peak,
        }


class ResourceSampler:
    """Request-scoped sampler used by canonical benchmark/runtime metrics."""

    def __init__(
        self,
        *,
        cpu_ram_interval_sec: float = 0.1,
        gpu_interval_sec: float = 0.25,
    ) -> None:
        self.cpu_ram_interval_sec = max(float(cpu_ram_interval_sec), 0.02)
        self.gpu_interval_sec = max(float(gpu_interval_sec), self.cpu_ram_interval_sec)
        self._cpu_samples: list[float] = []
        self._memory_samples: list[float] = []
        self._gpu_util_samples: list[float] = []
        self._gpu_memory_samples: list[float] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @staticmethod
    def _mean(values: list[float]) -> float | None:
        if not values:
            return None
        return float(sum(values) / len(values))

    @staticmethod
    def _peak(values: list[float]) -> float | None:
        if not values:
            return None
        return float(max(values))

    def _record_cpu_ram(self) -> None:
        cpu_percent, memory_mb = collect_cpu_ram_sample()
        with self._lock:
            self._cpu_samples.append(float(cpu_percent))
            self._memory_samples.append(float(memory_mb))

    def _record_gpu(self) -> None:
        gpu_util, gpu_memory = collect_gpu_optional()
        if gpu_util is None and gpu_memory is None:
            return
        with self._lock:
            if gpu_util is not None:
                self._gpu_util_samples.append(float(gpu_util))
            if gpu_memory is not None:
                self._gpu_memory_samples.append(float(gpu_memory))

    def _run(self) -> None:
        psutil.cpu_percent(interval=None)
        next_gpu_at = time.perf_counter()
        while not self._stop_event.is_set():
            loop_started_at = time.perf_counter()
            self._record_cpu_ram()
            if loop_started_at >= next_gpu_at:
                self._record_gpu()
                next_gpu_at = loop_started_at + self.gpu_interval_sec
            remaining = self.cpu_ram_interval_sec - (time.perf_counter() - loop_started_at)
            if remaining > 0.0 and self._stop_event.wait(remaining):
                break

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="asr-resource-sampler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> ResourceSampleSummary:
        thread = self._thread
        self._stop_event.set()
        if thread is not None:
            thread.join(timeout=max(self.cpu_ram_interval_sec * 4.0, 0.5))
        self._thread = None
        with self._lock:
            return ResourceSampleSummary(
                cpu_percent_mean=self._mean(self._cpu_samples),
                cpu_percent_peak=self._peak(self._cpu_samples),
                memory_mb_mean=self._mean(self._memory_samples),
                memory_mb_peak=self._peak(self._memory_samples),
                gpu_util_percent_mean=self._mean(self._gpu_util_samples),
                gpu_util_percent_peak=self._peak(self._gpu_util_samples),
                gpu_memory_mb_mean=self._mean(self._gpu_memory_samples),
                gpu_memory_mb_peak=self._peak(self._gpu_memory_samples),
            )
