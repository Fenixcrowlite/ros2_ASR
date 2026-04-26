#!/usr/bin/env python3
"""Record live microphone sample and evaluate selected ASR interfaces/backends.

Pipeline:
1. Record microphone audio into WAV.
2. Run inference across selected interfaces:
   - core (direct backend call)
   - ros_service (/asr/set_backend + /asr/recognize_once)
   - ros_action (/asr/set_backend + /asr/transcribe)
3. Collect and save metrics artifacts (CSV/JSON/plots + summary).
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "ros2_ws" / "src"
for package_root in SRC_ROOT.iterdir():
    if package_root.is_dir():
        sys.path.insert(0, str(package_root))

from asr_core.config import load_runtime_config  # noqa: E402
from asr_core.factory import create_backend  # noqa: E402
from asr_core.language import normalize_language_code as core_normalize_language_code  # noqa: E402
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, WordTimestamp  # noqa: E402
from asr_metrics.collector import MetricsCollector  # noqa: E402
from asr_metrics.io import save_benchmark_csv, save_benchmark_json  # noqa: E402
from asr_metrics.models import BenchmarkRecord  # noqa: E402
from asr_metrics.plotting import generate_all_plots  # noqa: E402

KNOWN_BACKENDS = {"mock", "vosk", "whisper", "google", "aws", "azure"}
AUTO_LANGUAGE_VALUES = {"auto", "detect", "auto-detect"}


def parse_csv_values(raw: str) -> list[str]:
    """Parse comma-separated string into non-empty values."""
    return [item.strip() for item in raw.split(",") if item.strip()]


def prompt_text(prompt: str, *, default: str = "") -> str:
    """Read one input line with optional default fallback."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def prompt_choice(prompt: str, *, choices: set[str], default: str) -> str:
    """Prompt until one of expected values is entered."""
    while True:
        raw = prompt_text(prompt, default=default).strip().lower()
        if raw in choices:
            return raw
        allowed = ", ".join(sorted(choices))
        print(f"[live-sample] Invalid value '{raw}'. Allowed: {allowed}")


@dataclass(slots=True)
class RosLaunchHandle:
    """Background ros2 launch process + attached log file handle."""

    process: subprocess.Popen[str]
    log_file: Any
    command: list[str]


@dataclass(frozen=True, slots=True)
class BackendRunTarget:
    """One backend + model/region override run target."""

    backend: str
    model: str
    region: str


@dataclass(frozen=True, slots=True)
class InteractiveOverrides:
    """Interactive wizard output values."""

    interfaces: list[str]
    model_runs: str
    language_mode: str
    language: str
    reference_text: str


def record_microphone_wav(
    *,
    output_wav: Path,
    duration_sec: float,
    sample_rate: int,
    device: str,
) -> None:
    """Record mono int16 microphone audio to WAV file."""
    if duration_sec <= 0:
        raise ValueError("duration_sec must be > 0")

    try:
        import sounddevice as sd  # type: ignore
        import soundfile as sf  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Microphone recording requires python packages sounddevice + soundfile"
        ) from exc

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration_sec * sample_rate)
    print(f"[live-sample] Recording {duration_sec:.1f}s at {sample_rate} Hz into {output_wav} ...")
    recording = sd.rec(
        frames,
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device if device else None,
    )
    sd.wait()
    sf.write(str(output_wav), recording, sample_rate, subtype="PCM_16")
    print(f"[live-sample] Recording saved: {output_wav}")


def normalize_language_code(raw: str, fallback: str) -> str:
    """Normalize language code into BCP-47-like representation."""
    value = raw.strip().replace("_", "-")
    if not value:
        return fallback

    lowered = value.lower()
    if lowered in AUTO_LANGUAGE_VALUES:
        return fallback
    return core_normalize_language_code(value, fallback=fallback)


def detect_language(cfg: dict[str, Any], override: str) -> str:
    """Resolve language from CLI override or runtime config."""
    fallback = str(cfg.get("asr", {}).get("language", "en-US"))
    if override:
        return normalize_language_code(override, fallback)
    return normalize_language_code(fallback, fallback)


def auto_detect_language_from_wav(wav_path: Path, cfg: dict[str, Any]) -> str:
    """Detect speech language using faster-whisper and return normalized code."""
    fallback = detect_language(cfg, "")
    whisper_cfg = dict(cfg.get("backends", {}).get("whisper", {}))
    model_size = str(whisper_cfg.get("auto_detect_model_size") or "tiny")
    device = str(whisper_cfg.get("auto_detect_device") or "cpu")
    compute_type = str(whisper_cfg.get("auto_detect_compute_type") or "int8")

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(
            str(wav_path),
            language=None,
            task="transcribe",
            vad_filter=True,
            condition_on_previous_text=False,
            temperature=0.0,
            beam_size=1,
            best_of=1,
        )
        for _ in segments:
            # Force lazy generator execution so detection data is available.
            break
        detected_raw = str(getattr(info, "language", "")).strip().lower()
        probability = float(getattr(info, "language_probability", 0.0) or 0.0)
        if not detected_raw:
            raise RuntimeError("Whisper returned empty language code")
        resolved = normalize_language_code(detected_raw, fallback)
        print(
            "[live-sample] Auto language detected: "
            f"{detected_raw} (p={probability:.3f}) -> {resolved}"
        )
        return resolved
    except Exception as exc:
        raise RuntimeError(
            f"Auto language detection failed ({exc}). "
            f"Use --language-mode config/manual or install a working faster-whisper setup."
        ) from exc


def detect_backends(cfg: dict[str, Any], cli_backends: str) -> list[str]:
    """Resolve selected backend names."""
    if cli_backends.strip():
        return parse_csv_values(cli_backends)
    return [str(cfg.get("asr", {}).get("backend", "mock"))]


def detect_interfaces(cli_interfaces: str) -> list[str]:
    """Resolve selected interface names and validate values."""
    values = parse_csv_values(cli_interfaces) if cli_interfaces.strip() else ["core"]
    allowed = {"core", "ros_service", "ros_action"}
    unknown = [item for item in values if item not in allowed]
    if unknown:
        raise ValueError(f"Unknown interfaces: {', '.join(unknown)}")
    return values


def backend_model_region(cfg: dict[str, Any], backend_name: str) -> tuple[str, str]:
    """Resolve backend model/region hints used by SetAsrBackend service."""
    backend_cfg = dict(cfg.get("backends", {}).get(backend_name, {}))
    asr_cfg = dict(cfg.get("asr", {}))

    model = str(
        backend_cfg.get("model") or backend_cfg.get("model_size") or asr_cfg.get("model") or ""
    )
    region = str(backend_cfg.get("region") or asr_cfg.get("region") or "")
    if not region and backend_name in {"mock", "vosk", "whisper"}:
        region = "local"
    return model, region


def parse_backend_model_spec(raw: str) -> tuple[str, str, str]:
    """Parse token in format backend[:model][@region]."""
    token = raw.strip()
    if not token:
        raise ValueError("Empty backend/model token")

    backend_model = token
    region = ""
    if "@" in token:
        backend_model, region = token.split("@", 1)
        region = region.strip()

    backend_model = backend_model.strip()
    if ":" in backend_model:
        backend, model = backend_model.split(":", 1)
    else:
        backend, model = backend_model, ""
    return backend.strip(), model.strip(), region


def _validate_backend_name(cfg: dict[str, Any], backend: str) -> None:
    """Validate backend name against known and configured backends."""
    available = set(cfg.get("backends", {}).keys()) | KNOWN_BACKENDS
    if backend not in available:
        known = ", ".join(sorted(available))
        raise ValueError(f"Unknown backend '{backend}'. Known values: {known}")


def resolve_backend_targets(
    *,
    cfg: dict[str, Any],
    cli_backends: str,
    cli_model_runs: str,
) -> list[BackendRunTarget]:
    """Resolve backend/model targets from CLI values."""
    raw_tokens = parse_csv_values(cli_model_runs) if cli_model_runs.strip() else []
    if not raw_tokens:
        raw_tokens = detect_backends(cfg, cli_backends)

    targets: list[BackendRunTarget] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in raw_tokens:
        backend, model_override, region_override = parse_backend_model_spec(raw)
        _validate_backend_name(cfg, backend)
        default_model, default_region = backend_model_region(cfg, backend)
        model = model_override or default_model
        region = region_override or default_region
        key = (backend, model, region)
        if key in seen:
            continue
        seen.add(key)
        targets.append(BackendRunTarget(backend=backend, model=model, region=region))
    return targets


def backend_target_label(target: BackendRunTarget) -> str:
    """Build readable backend label used in records and plots."""
    if target.model and target.region and target.region != "local":
        return f"{target.backend}:{target.model}@{target.region}"
    if target.model:
        return f"{target.backend}:{target.model}"
    if target.region and target.region != "local":
        return f"{target.backend}@{target.region}"
    return target.backend


def override_backend_config(cfg: dict[str, Any], target: BackendRunTarget) -> dict[str, Any]:
    """Apply model/region overrides for direct core backend run."""
    backend_cfg = dict(cfg.get("backends", {}).get(target.backend, {}))
    if target.model:
        backend_cfg["model"] = target.model
        if target.backend == "whisper":
            backend_cfg["model_size"] = target.model
    if target.region and target.region != "local":
        backend_cfg["region"] = target.region
    return backend_cfg


def response_from_asr_result_msg(msg: Any) -> AsrResponse:
    """Convert ROS AsrResult message into core AsrResponse dataclass."""
    words = [
        WordTimestamp(
            word=str(item.word),
            start_sec=float(item.start_sec),
            end_sec=float(item.end_sec),
            confidence=float(item.confidence),
        )
        for item in list(msg.word_timestamps)
    ]
    return AsrResponse(
        text=str(msg.text),
        partials=list(msg.partials),
        confidence=float(msg.confidence),
        word_timestamps=words,
        language=str(msg.language),
        backend_info={
            "provider": str(msg.backend),
            "model": str(msg.model),
            "region": str(msg.region),
        },
        timings=AsrTimings(
            preprocess_ms=float(msg.preprocess_ms),
            inference_ms=float(msg.inference_ms),
            postprocess_ms=float(msg.postprocess_ms),
        ),
        audio_duration_sec=float(msg.audio_duration_sec),
        success=bool(msg.success),
        error_code=str(msg.error_code),
        error_message=str(msg.error_message),
    )


def make_error_response(
    *,
    backend: str,
    language: str,
    error_code: str,
    error_message: str,
) -> AsrResponse:
    """Build synthetic failed response for robust metrics rows."""
    return AsrResponse(
        success=False,
        error_code=error_code,
        error_message=error_message,
        language=language,
        backend_info={"provider": backend, "model": "", "region": ""},
    )


def start_ros_bringup(
    *,
    config_path: str,
    wav_path: str,
    sample_rate: int,
    log_path: Path,
) -> RosLaunchHandle:
    """Start background bringup launch in file mode for service/action evaluation."""
    cmd = [
        "ros2",
        "launch",
        "asr_ros",
        "bringup.launch.py",
        f"config:={config_path}",
        "input_mode:=file",
        "continuous:=false",
        f"wav_path:={wav_path}",
        f"sample_rate:={sample_rate}",
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )
    return RosLaunchHandle(process=process, log_file=log_file, command=cmd)


def stop_ros_bringup(handle: RosLaunchHandle) -> None:
    """Stop background launch process gracefully."""
    process = handle.process
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    handle.log_file.close()


class RosInterfaceInvoker:
    """ROS2 client wrapper for service/action-based live sample evaluation."""

    def __init__(self, timeout_sec: float) -> None:
        self.timeout_sec = timeout_sec
        self._rclpy: Any = None
        self._node: Any = None
        self._set_backend_client: Any = None
        self._recognize_client: Any = None
        self._action_client: Any = None
        self._SetAsrBackend: Any = None
        self._RecognizeOnce: Any = None
        self._Transcribe: Any = None

    def __enter__(self) -> RosInterfaceInvoker:
        try:
            import rclpy
            from asr_interfaces.action import Transcribe
            from asr_interfaces.srv import RecognizeOnce, SetAsrBackend
            from rclpy.action import ActionClient
        except Exception as exc:
            raise RuntimeError(
                "ROS interface mode requires sourced ROS2/install setup and asr_interfaces"
            ) from exc

        self._rclpy = rclpy
        self._SetAsrBackend = SetAsrBackend
        self._RecognizeOnce = RecognizeOnce
        self._Transcribe = Transcribe

        self._rclpy.init(args=None)
        self._node = self._rclpy.create_node("live_sample_eval_client")
        self._set_backend_client = self._node.create_client(SetAsrBackend, "/asr/set_backend")
        self._recognize_client = self._node.create_client(RecognizeOnce, "/asr/recognize_once")
        self._action_client = ActionClient(self._node, Transcribe, "/asr/transcribe")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._node is not None:
            self._node.destroy_node()
        if self._rclpy is not None and self._rclpy.ok():
            self._rclpy.shutdown()

    def _spin_future(self, future: Any, timeout_sec: float) -> Any:
        self._rclpy.spin_until_future_complete(self._node, future, timeout_sec=timeout_sec)
        if not future.done():
            raise TimeoutError("ROS future timed out")
        result = future.result()
        if result is None:
            exc = future.exception()
            if exc is None:
                raise RuntimeError("ROS future returned no result")
            raise RuntimeError(str(exc))
        return result

    def wait_ready(self, *, require_action: bool) -> None:
        if not self._set_backend_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise TimeoutError("Service /asr/set_backend is not available")
        if not self._recognize_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise TimeoutError("Service /asr/recognize_once is not available")
        if require_action and not self._action_client.wait_for_server(timeout_sec=self.timeout_sec):
            raise TimeoutError("Action /asr/transcribe is not available")

    def set_backend(self, *, backend: str, model: str, region: str) -> None:
        request = self._SetAsrBackend.Request()
        request.backend = backend
        request.model = model
        request.region = region
        response = self._spin_future(
            self._set_backend_client.call_async(request),
            timeout_sec=self.timeout_sec,
        )
        if not bool(response.success):
            raise RuntimeError(f"set_backend failed: {response.message}")

    def recognize_once(self, *, wav_path: str, language: str) -> AsrResponse:
        request = self._RecognizeOnce.Request()
        request.wav_path = wav_path
        request.language = language
        request.enable_word_timestamps = True
        response = self._spin_future(
            self._recognize_client.call_async(request),
            timeout_sec=self.timeout_sec,
        )
        return response_from_asr_result_msg(response.result)

    def transcribe_action(
        self,
        *,
        wav_path: str,
        language: str,
        streaming: bool,
        chunk_sec: float,
    ) -> AsrResponse:
        goal = self._Transcribe.Goal()
        goal.wav_path = wav_path
        goal.language = language
        goal.streaming = bool(streaming)
        goal.chunk_sec = float(chunk_sec)

        goal_future = self._action_client.send_goal_async(goal)
        goal_handle = self._spin_future(goal_future, timeout_sec=self.timeout_sec)
        if not bool(goal_handle.accepted):
            raise RuntimeError("/asr/transcribe goal rejected")

        wrapped_result = self._spin_future(
            goal_handle.get_result_async(),
            timeout_sec=self.timeout_sec,
        )
        return response_from_asr_result_msg(wrapped_result.result.result)


def collect_live_record(
    *,
    collector: MetricsCollector,
    backend_label: str,
    interface: str,
    wav_path: str,
    language: str,
    reference_text: str,
    response: AsrResponse,
) -> BenchmarkRecord:
    """Convert one interface result into benchmark-style record."""
    reference = reference_text.strip()
    effective_reference = reference if reference else response.text
    record = collector.record(
        backend=backend_label,
        scenario=f"live_{interface}",
        wav_path=wav_path,
        language=language,
        reference_text=effective_reference,
        response=response,
        request_id=str(uuid.uuid4()),
    )
    if not reference:
        record.wer = -1.0
        record.cer = -1.0
        record.transcript_ref = ""
    return record


def run_core_interface(
    *,
    cfg: dict[str, Any],
    target: BackendRunTarget,
    wav_path: str,
    language: str,
) -> AsrResponse:
    """Run direct backend recognize_once without ROS wrappers."""
    backend_cfg = override_backend_config(cfg, target)
    backend = create_backend(target.backend, config=backend_cfg)
    request = AsrRequest(wav_path=wav_path, language=language, enable_word_timestamps=True)
    response = backend.recognize_once(request)
    if target.model and not response.backend_info.get("model"):
        response.backend_info["model"] = target.model
    if target.region and not response.backend_info.get("region"):
        response.backend_info["region"] = target.region
    return response


def target_supports_streaming(cfg: dict[str, Any], target: BackendRunTarget) -> bool:
    """Return True when selected backend target advertises native streaming."""
    backend_cfg = override_backend_config(cfg, target)
    backend = create_backend(target.backend, config=backend_cfg)
    capabilities = getattr(backend, "capabilities", None)
    return bool(getattr(capabilities, "supports_streaming", False))


def validate_interface_plan(
    *,
    cfg: dict[str, Any],
    interfaces: list[str],
    targets: list[BackendRunTarget],
    action_streaming: bool,
) -> None:
    """Reject incompatible interface/backend combinations before any run starts."""
    if "ros_action" in interfaces and action_streaming:
        unsupported = [
            backend_target_label(target)
            for target in targets
            if not target_supports_streaming(cfg, target)
        ]
        if unsupported:
            joined = ", ".join(unsupported)
            raise ValueError(
                "ros_action with --action-streaming requires streaming-capable backends. "
                f"Unsupported targets: {joined}"
            )


def save_summary(records: list[BenchmarkRecord], output_path: Path) -> None:
    """Write compact markdown report for live sample run."""
    lines = [
        "# Live Sample Evaluation Summary",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Records: {len(records)}",
        "",
        "| Interface | Backend/Model | Language | Success | Text | "
        "WER | CER | Latency (ms) | RTF | Error |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for rec in records:
        interface = rec.scenario.replace("live_", "", 1)
        text = rec.text.replace("|", "/")[:80]
        language = rec.language.replace("|", "/")[:20]
        error = f"{rec.error_code}:{rec.error_message}" if rec.error_code else ""
        error = error.replace("|", "/")[:80]
        lines.append(
            "| "
            f"{interface} | {rec.backend} | {language} | {int(rec.success)} | {text} | "
            f"{rec.wer:.3f} | {rec.cer:.3f} | {rec.latency_ms:.1f} | {rec.rtf:.3f} | {error} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_interactive_configuration(
    *,
    args: argparse.Namespace,
    cfg: dict[str, Any],
    wav_path: Path,
) -> InteractiveOverrides:
    """Collect optional interactive overrides after audio recording."""
    print("[live-sample] Interactive mode: configure language and backend models.")
    print(f"[live-sample] Recorded sample: {wav_path}")

    language_mode_default = str(args.language_mode or "config").strip().lower()
    if language_mode_default not in {"manual", "auto", "config"}:
        language_mode_default = "config"
    language_mode = prompt_choice(
        "Language mode (manual/auto/config)",
        choices={"manual", "auto", "config"},
        default=language_mode_default,
    )

    language_default = detect_language(cfg, args.language)
    language_override = args.language
    if language_mode == "manual":
        language_override = prompt_text("Language code", default=language_default)
    elif language_mode == "config":
        language_override = ""
    else:
        language_override = ""

    interfaces_default = args.interfaces or "core"
    interfaces_raw = prompt_text(
        "Interfaces (core,ros_service,ros_action)",
        default=interfaces_default,
    )
    interfaces = detect_interfaces(interfaces_raw)

    model_runs_default = (
        args.model_runs.strip()
        or args.backends.strip()
        or str(cfg.get("asr", {}).get("backend", "mock"))
    )
    model_runs = prompt_text(
        "Backend/model runs backend[:model][@region], comma-separated",
        default=model_runs_default,
    )

    reference_text = prompt_text(
        "Reference text for WER/CER (optional)",
        default=args.reference_text,
    )

    return InteractiveOverrides(
        interfaces=interfaces,
        model_runs=model_runs,
        language_mode=language_mode,
        language=language_override,
        reference_text=reference_text,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser for live sample evaluator."""
    parser = argparse.ArgumentParser(
        description="Record microphone sample and evaluate selected ASR interfaces/backends"
    )
    parser.add_argument("--config", default="configs/default.yaml", help="Runtime YAML config path")
    parser.add_argument(
        "--interfaces",
        default="core",
        help="Comma-separated: core,ros_service,ros_action",
    )
    parser.add_argument(
        "--backends",
        default="",
        help="Comma-separated backend names (default from config asr.backend)",
    )
    parser.add_argument(
        "--model-runs",
        default="",
        help="Comma-separated backend[:model][@region] entries for multi-model runs",
    )
    parser.add_argument("--language", default="", help="Recognition language override")
    parser.add_argument(
        "--language-mode",
        default="config",
        choices=["manual", "auto", "config"],
        help="Language source: manual value, auto-detect from recorded WAV, or config default",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive wizard after recording sample (language/modes/models selection)",
    )
    parser.add_argument(
        "--reference-text",
        default="",
        help="Ground-truth phrase for WER/CER; if omitted WER/CER are set to -1",
    )
    parser.add_argument(
        "--record-sec", type=float, default=5.0, help="Microphone recording duration"
    )
    parser.add_argument("--sample-rate", type=int, default=16000, help="Recording sample rate")
    parser.add_argument("--device", default="", help="Optional sounddevice input device")
    parser.add_argument(
        "--output-dir",
        default="results/live_sample",
        help="Directory where artifacts are stored",
    )
    parser.add_argument(
        "--sample-name",
        default="live_sample",
        help="WAV basename for recorded sample",
    )
    parser.add_argument(
        "--use-wav",
        default="",
        help="Skip recording and use existing WAV path",
    )
    parser.add_argument(
        "--ros-auto-launch",
        action="store_true",
        help="Auto-start bringup.launch.py for ROS interfaces",
    )
    parser.add_argument(
        "--request-timeout-sec",
        type=float,
        default=25.0,
        help="Timeout for ROS service/action requests",
    )
    parser.add_argument(
        "--action-streaming",
        action="store_true",
        help="For ros_action interface set goal.streaming=true",
    )
    parser.add_argument(
        "--action-chunk-sec",
        type=float,
        default=0.8,
        help="Chunk size for ros_action streaming goal",
    )
    return parser


def main() -> int:
    """CLI entry point."""
    args = build_arg_parser().parse_args()
    cfg = load_runtime_config(args.config, "configs/commercial.yaml")

    interfaces = detect_interfaces(args.interfaces)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_dir) / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.use_wav:
        wav_path = Path(args.use_wav).resolve()
        if not wav_path.exists():
            raise FileNotFoundError(f"WAV file not found: {wav_path}")
    else:
        wav_path = run_dir / f"{args.sample_name}.wav"
        record_microphone_wav(
            output_wav=wav_path,
            duration_sec=args.record_sec,
            sample_rate=args.sample_rate,
            device=args.device,
        )

    if args.interactive:
        overrides = run_interactive_configuration(args=args, cfg=cfg, wav_path=wav_path)
        interfaces = overrides.interfaces
        args.model_runs = overrides.model_runs
        args.language_mode = overrides.language_mode
        args.language = overrides.language
        args.reference_text = overrides.reference_text

    targets = resolve_backend_targets(
        cfg=cfg,
        cli_backends=args.backends,
        cli_model_runs=args.model_runs,
    )
    if not targets:
        raise RuntimeError("No backend/model targets were selected")
    validate_interface_plan(
        cfg=cfg,
        interfaces=interfaces,
        targets=targets,
        action_streaming=bool(args.action_streaming),
    )

    language_mode = str(args.language_mode).strip().lower()
    if args.language and language_mode == "config":
        language_mode = "manual"
    if language_mode == "auto":
        language = auto_detect_language_from_wav(wav_path, cfg)
    elif language_mode == "manual":
        language = detect_language(cfg, args.language)
    else:
        language = detect_language(cfg, "")
    print(f"[live-sample] Effective language: {language} (mode={language_mode})")
    print(
        "[live-sample] Run targets: "
        + ", ".join(backend_target_label(target) for target in targets)
    )

    collector = MetricsCollector(pricing_per_minute=cfg.get("benchmark", {}).get("pricing", {}))
    records: list[BenchmarkRecord] = []

    launch_handle: RosLaunchHandle | None = None
    ros_invoker: RosInterfaceInvoker | None = None
    ros_interfaces_requested = any(item.startswith("ros_") for item in interfaces)

    try:
        if ros_interfaces_requested:
            if args.ros_auto_launch:
                if not shutil_which("ros2"):
                    raise RuntimeError("ros2 command is not available in PATH")
                launch_log_path = run_dir / "ros_launch.log"
                launch_handle = start_ros_bringup(
                    config_path=args.config,
                    wav_path=str(wav_path),
                    sample_rate=args.sample_rate,
                    log_path=launch_log_path,
                )
                print(f"[live-sample] Started ROS bringup: {' '.join(launch_handle.command)}")
                time.sleep(5.0)

            ros_invoker = RosInterfaceInvoker(timeout_sec=args.request_timeout_sec)
            ros_invoker.__enter__()
            ros_invoker.wait_ready(require_action="ros_action" in interfaces)

        for interface_name in interfaces:
            for target in targets:
                backend_label = backend_target_label(target)
                print(
                    "[live-sample] Running "
                    f"interface={interface_name} target={backend_label}"
                )
                try:
                    if interface_name == "core":
                        response = run_core_interface(
                            cfg=cfg,
                            target=target,
                            wav_path=str(wav_path),
                            language=language,
                        )
                    else:
                        if ros_invoker is None:
                            raise RuntimeError(
                                "ROS interface requested but ROS invoker is not ready"
                            )

                        ros_invoker.set_backend(
                            backend=target.backend,
                            model=target.model,
                            region=target.region,
                        )

                        if interface_name == "ros_service":
                            response = ros_invoker.recognize_once(
                                wav_path=str(wav_path),
                                language=language,
                            )
                        elif interface_name == "ros_action":
                            response = ros_invoker.transcribe_action(
                                wav_path=str(wav_path),
                                language=language,
                                streaming=bool(args.action_streaming),
                                chunk_sec=float(args.action_chunk_sec),
                            )
                        else:
                            raise ValueError(f"Unsupported interface: {interface_name}")
                except Exception as exc:
                    response = make_error_response(
                        backend=target.backend,
                        language=language,
                        error_code="interface_error",
                        error_message=str(exc),
                    )

                record = collect_live_record(
                    collector=collector,
                    backend_label=backend_label,
                    interface=interface_name,
                    wav_path=str(wav_path),
                    language=language,
                    reference_text=args.reference_text,
                    response=response,
                )
                records.append(record)
                print(
                    "[live-sample] -> "
                    f"success={record.success} text='{record.text[:80]}' "
                    f"latency_ms={record.latency_ms:.1f} error={record.error_code or '-'}"
                )
    finally:
        if ros_invoker is not None:
            ros_invoker.__exit__(None, None, None)
        if launch_handle is not None:
            stop_ros_bringup(launch_handle)

    if not records:
        raise RuntimeError("No records were produced")

    json_path = run_dir / "live_results.json"
    csv_path = run_dir / "live_results.csv"
    plots_dir = run_dir / "plots"
    summary_path = run_dir / "summary.md"

    save_benchmark_json(records, str(json_path))
    save_benchmark_csv(records, str(csv_path))
    generate_all_plots(records, str(plots_dir))
    save_summary(records, summary_path)

    print("[live-sample] Artifacts generated:")
    print(f"  WAV: {wav_path}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")
    print(f"  Summary: {summary_path}")
    print(f"  Plots: {plots_dir}")
    return 0


def shutil_which(binary: str) -> str | None:
    """Local wrapper to avoid global shutil import noise."""
    from shutil import which

    return which(binary)


if __name__ == "__main__":
    raise SystemExit(main())
