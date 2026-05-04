from __future__ import annotations

import importlib
import json
import time
import wave
from io import BytesIO
from pathlib import Path

import pytest
from tests.utils.asgi_client import SyncAsgiClient
from tests.utils.fakes import FakeGatewayRosClient, FakeProviderAdapter, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def _write_provider_profile(configs_root: Path, profile_name: str, provider_id: str) -> None:
    profile_path = configs_root / "providers" / f"{profile_name}.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        f"provider_id: {provider_id}\nsettings: {{}}\n",
        encoding="utf-8",
    )


def _make_client(repo_root: Path, tmp_path: Path, monkeypatch):
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_seed_a", wer=0.0, cer=0.0)
    seed_benchmark_run(project_root, "bench_seed_b", wer=0.2, cer=0.1)

    fake_ros = FakeGatewayRosClient(project_root=project_root)
    import asr_gateway.ros_client as ros_client_module

    monkeypatch.setenv("ASR_PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(ros_client_module, "GatewayRosClient", lambda timeout_sec=5.0: fake_ros)
    import asr_gateway.api as gateway_api

    gateway_api = importlib.reload(gateway_api)
    monkeypatch.setattr(
        gateway_api, "ProviderManager", build_stub_provider_manager(str(project_root / "configs"))
    )
    monkeypatch.setattr(
        gateway_api,
        "create_provider",
        lambda provider_id, configs_root=None: build_stub_provider_manager(
            str(project_root / "configs")
        )().create_from_profile(
            {
                "azure": "providers/azure_cloud",
                "aws": "providers/aws_cloud",
                "google": "providers/google_cloud",
                "huggingface_local": "providers/huggingface_local",
                "huggingface_api": "providers/huggingface_api",
            }.get(provider_id, "providers/whisper_local")
        ),
    )
    monkeypatch.setattr(
        gateway_api,
        "list_providers",
        lambda *args, **kwargs: ["whisper", "azure", "aws"],
    )
    gateway_api._RUNTIME_EVENTS.clear()
    gateway_api._RUNTIME_RESULTS.clear()
    gateway_api._BENCHMARK_JOBS.clear()
    client = SyncAsgiClient(gateway_api.app)
    return gateway_api, fake_ros, client, project_root


def test_runtime_api_round_trip(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "provider_preset": "accurate",
            "provider_settings": {"beam_size": 5},
            "processing_mode": "segmented",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    live = client.get("/api/runtime/live").json()
    assert live["status"]["session_state"] == "active"
    assert live["recent_events"][0]["event"] == "runtime_start"
    assert live["status"]["model"] == "accurate"
    assert live["status"]["processing_mode"] == "segmented"
    assert live["status"]["streaming_mode"] == "none"

    recognize = client.post(
        "/api/runtime/recognize_once",
        json={
            "wav_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "session_id": session_id,
            "provider_profile": "providers/whisper_local",
            "provider_preset": "light",
            "provider_settings": {"compute_type": "int8"},
        },
    )
    assert recognize.status_code == 200
    assert "recognized from vosk_test.wav" in recognize.json()["text"]
    assert recognize.json()["provider_preset"] == "light"

    live_after = client.get("/api/runtime/live").json()
    assert live_after["recent_results"][0]["request_id"] == "req_demo"
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["runtime_live"]["recent_results"][0]["request_id"] == "req_demo"

    stop = client.post("/api/runtime/stop", json={"session_id": session_id})
    assert stop.status_code == 200
    assert client.get("/api/runtime/status").json()["session_state"] == "idle"


def test_runtime_samples_catalog_and_upload(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    catalog = client.get("/api/runtime/samples")
    assert catalog.status_code == 200
    payload = catalog.json()
    assert payload["default_sample"] == "data/sample/vosk_test.wav"
    assert any(item["path"] == "data/sample/vosk_test.wav" for item in payload["samples"])
    assert any(item["path"] == "data/sample/audio_tester.wav" for item in payload["skipped"])

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)

    upload = client.post(
        "/api/runtime/upload_sample",
        files={"file": ("drag_test.wav", wav_buffer.getvalue(), "audio/wav")},
    )
    assert upload.status_code == 200
    upload_payload = upload.json()
    assert upload_payload["saved"] is True
    assert upload_payload["sample_path"].startswith("data/sample/uploads/drag_test")
    assert (project_root / upload_payload["sample_path"]).exists()
    assert any(
        item["path"] == upload_payload["sample_path"]
        for item in upload_payload["catalog"]["samples"]
    )


def test_runtime_upload_sample_rejects_oversized_file(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)
    monkeypatch.setattr(gateway_api, "MAX_RUNTIME_SAMPLE_BYTES", 32)

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 16)

    response = client.post(
        "/api/runtime/upload_sample",
        files={"file": ("too_big.wav", wav_buffer.getvalue(), "audio/wav")},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_runtime_noise_generation_and_preflight(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    preflight = client.get("/api/diagnostics/preflight")
    assert preflight.status_code == 200
    preflight_payload = preflight.json()
    assert "ok" in preflight_payload
    assert "checks" in preflight_payload
    assert "modules" in preflight_payload["checks"]
    assert "microphone" in preflight_payload["checks"]
    assert "ros" in preflight_payload["checks"]
    assert "runtime_google_cloud_speech" in preflight_payload["checks"]["ros"]
    assert "runtime_azure_speech" in preflight_payload["checks"]["ros"]

    noise = client.post(
        "/api/runtime/generate_noise",
        json={
            "source_wav": "data/sample/vosk_test.wav",
            "snr_levels": [20.0, 10.0],
        },
    )
    assert noise.status_code == 200
    noise_payload = noise.json()
    assert len(noise_payload["generated"]) == 2
    for row in noise_payload["generated"]:
        assert row["path"].startswith("data/sample/generated_noise/")
        assert (project_root / row["path"]).exists()
    assert any(
        item["path"] == noise_payload["generated"][0]["path"]
        for item in noise_payload["catalog"]["samples"]
    )


def test_benchmark_preview_audio_supports_clean_and_noise_variants(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    clean = client.get(
        "/api/benchmark/preview_audio",
        params={
            "dataset_profile": "sample_dataset",
            "sample_id": "sample_vosk_numbers",
            "start_sec": 0.0,
            "duration_sec": 0.2,
            "noise_level": "clean",
        },
    )
    assert clean.status_code == 200
    assert clean.headers["content-type"].startswith("audio/wav")
    assert "content-disposition" not in {key.lower(): value for key, value in clean.headers.items()}
    with wave.open(BytesIO(clean.content), "rb") as wav_file:
        duration_sec = wav_file.getnframes() / float(wav_file.getframerate())
    assert duration_sec == pytest.approx(0.2, abs=0.03)

    noisy = client.get(
        "/api/benchmark/preview_audio",
        params={
            "dataset_profile": "sample_dataset",
            "sample_id": "sample_vosk_numbers",
            "start_sec": 0.0,
            "duration_sec": 0.2,
            "noise_level": "light",
            "noise_mode": "pink",
        },
    )
    assert noisy.status_code == 200
    assert noisy.headers["content-type"].startswith("audio/wav")
    assert noisy.headers["x-asr-benchmark-preview-noise-level"] == "light"
    assert noisy.headers["x-asr-benchmark-preview-noise-mode"] == "pink"
    assert noisy.content != clean.content

    custom = client.get(
        "/api/benchmark/preview_audio",
        params={
            "dataset_profile": "sample_dataset",
            "sample_id": "sample_vosk_numbers",
            "start_sec": 0.0,
            "duration_sec": 0.2,
            "noise_level": "custom",
            "noise_mode": "pink",
            "snr_db": 17.5,
        },
    )
    assert custom.status_code == 200
    assert custom.headers["content-type"].startswith("audio/wav")
    assert custom.headers["x-asr-benchmark-preview-noise-level"] == "custom"
    assert custom.headers["x-asr-benchmark-preview-noise-mode"] == "pink"
    assert custom.headers["x-asr-benchmark-preview-snr-db"] == "17.5"
    assert custom.content != clean.content

    fleurs = client.get(
        "/api/benchmark/preview_audio",
        params={
            "dataset_profile": "fleurs_en_us_test_subset",
            "sample_id": "fleurs_en_us_12741024238657315067",
            "start_sec": 0.0,
            "duration_sec": 0.2,
            "noise_level": "clean",
        },
    )
    assert fleurs.status_code == 200
    assert fleurs.headers["content-type"].startswith("audio/wav")


def test_runtime_api_rejects_double_start(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    first = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )
    second = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already active" in second.json()["detail"]


def test_runtime_api_marks_completed_file_session_from_audio_status(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)
    fake_ros.runtime_started = True
    fake_ros.session_id = "session_demo"
    fake_ros.audio_source = "file"

    def completed_snapshot() -> dict[str, object]:
        active_session = {
            "session_id": "session_demo",
            "state": "ready",
            "provider_id": "whisper_local",
            "profile_id": "default_runtime",
            "processing_mode": "segmented",
            "status_message": "ready source=file mode=segmented",
            "updated_at": "2026-03-25T00:00:00+00:00",
        }
        return {
            "observer_error": "",
            "recent_results": [],
            "recent_partials": [],
            "node_statuses": [
                {
                    "node_name": "audio_input_node",
                    "health": "ok",
                    "ready": True,
                    "status_message": "completed source=file session=session_demo",
                    "time": "2026-03-25T00:00:00+00:00",
                    "last_error_code": "",
                    "last_error_message": "",
                }
            ],
            "session_statuses": [active_session],
            "active_session": active_session,
        }

    monkeypatch.setattr(type(fake_ros), "runtime_snapshot", lambda self: completed_snapshot())

    status = client.get("/api/runtime/status")
    assert status.status_code == 200
    assert status.json()["session_state"] == "completed"

    live = client.get("/api/runtime/live")
    assert live.status_code == 200
    payload = live.json()
    assert payload["status"]["session_state"] == "completed"
    assert payload["active_session"]["state"] == "completed"
    assert payload["session_statuses"][0]["state"] == "completed"


def test_runtime_snapshot_shape_is_sanitized_before_gateway_responses(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)
    fake_ros.runtime_started = True
    fake_ros.session_id = "session_demo"
    fake_ros.audio_source = "file"

    def malformed_snapshot() -> dict[str, object]:
        return {
            "observer_error": ["observer", "warning"],
            "recent_results": ["invalid", {"request_id": "req_keep", "type": "final"}],
            "recent_partials": None,
            "node_statuses": [{"node_name": "audio_input_node", "status_message": 123}, "bad"],
            "session_statuses": ["bad", {"session_id": "session_demo", "state": "active"}],
            "active_session": "invalid",
        }

    monkeypatch.setattr(type(fake_ros), "runtime_snapshot", lambda self: malformed_snapshot())

    status = client.get("/api/runtime/status")
    assert status.status_code == 200
    assert status.json()["observer_error"] == "['observer', 'warning']"
    assert status.json()["session_id"] == "session_demo"

    live = client.get("/api/runtime/live")
    assert live.status_code == 200
    live_payload = live.json()
    assert live_payload["active_session"] == {}
    assert live_payload["recent_results"] == [{"request_id": "req_keep", "type": "final"}]
    assert live_payload["session_statuses"] == [{"session_id": "session_demo", "state": "active"}]

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["runtime_live"]["active_session"] == {}


def test_benchmark_history_status_compare_and_export(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    run = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "sample_dataset",
            "providers": ["providers/azure_cloud"],
            "scenario": "noise_robustness",
            "provider_overrides": {
                "providers/azure_cloud": {
                    "provider_preset": "standard",
                    "provider_settings": {"region": "eastus"},
                }
            },
            "benchmark_settings": {
                "execution_mode": "streaming",
                "streaming": {"chunk_ms": 250},
                "noise": {"mode": "white", "levels": ["clean", "light"], "custom_snr_db": [17.5, 5]},
            },
            "run_id": "bench_live_run",
        },
    )
    assert run.status_code == 200

    deadline = time.time() + 5.0
    status_payload = {}
    while time.time() < deadline:
        status = client.get("/api/benchmark/status/bench_live_run")
        status_payload = status.json() if status.status_code == 200 else {}
        if status.status_code == 200 and status_payload.get("state") == "completed" and status_payload.get("result", {}).get("summary", {}).get("provider_summaries"):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("benchmark run did not complete in time")

    assert "provider_summaries" in status_payload["result"]["summary"]
    assert status_payload["result"]["summary"]["provider_summaries"]
    assert "provider_noise_summaries" in status_payload["result"]["summary"]
    assert "sample_error_summary" in status_payload["result"]["summary"]
    assert "available_analysis_sections" in status_payload["result"]["summary"]

    history = client.get("/api/benchmark/history").json()
    live_row = next(row for row in history["runs"] if row["run_id"] == "bench_live_run")
    assert live_row["scenario"] == "noise_robustness"
    assert live_row["execution_mode"] == "streaming"
    assert "wer" in live_row["quality_metrics"]
    assert "real_time_factor" in live_row["latency_metrics"]
    assert "success_rate" in live_row["reliability_metrics"]
    assert "estimated_cost_usd" in live_row["cost_metrics"]
    assert live_row["provider_summaries"]
    run_manifest = json.loads(
        (project_root / "artifacts" / "benchmark_runs" / "bench_live_run" / "manifest" / "run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert run_manifest["benchmark_settings"]["noise"]["custom_snr_db"] == [17.5, 5.0]

    compare = client.post(
        "/api/results/compare", json={"run_ids": ["bench_seed_a", "bench_seed_b"]}
    )
    assert compare.status_code == 200
    assert compare.json()["table"]
    assert compare.json()["chart_series"]

    export = client.post(
        "/api/results/export",
        json={
            "run_ids": ["bench_seed_a", "bench_seed_b"],
            "formats": ["json", "csv", "md"],
            "name": "compare_demo",
        },
    )
    assert export.status_code == 200
    outputs = export.json()["outputs"]
    assert (project_root / "artifacts" / "exports" / "compare_demo").exists()
    assert outputs["json"].endswith("comparison.json")


def test_results_row_audio_replay_supports_clean_and_noise_preview(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    detail = client.get("/api/results/runs/bench_seed_a")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert "analysis" in detail_payload
    assert detail_payload["analysis"]["provider_rankings"]
    assert "section_availability" in detail_payload["analysis"]
    row = detail.json()["results_head"][0]
    assert row["row_index"] == 0
    assert row["replay"]["has_clean_audio"] is True

    rows = client.get(
        "/api/results/runs/bench_seed_a/rows",
        params={"page": 1, "page_size": 10, "provider": "providers/whisper_local", "sort": "wer"},
    )
    assert rows.status_code == 200
    rows_payload = rows.json()
    assert rows_payload["total"] == 1
    assert rows_payload["items"][0]["provider_profile"] == "providers/whisper_local"
    assert "clean" in rows_payload["available_filters"]["noise"]

    clean = client.get(
        "/api/results/runs/bench_seed_a/rows/0/audio",
        params={"source": "clean", "start_sec": 0.0, "duration_sec": 0.2},
    )
    assert clean.status_code == 200
    assert clean.headers["content-type"].startswith("audio/wav")
    assert "content-disposition" not in {key.lower(): value for key, value in clean.headers.items()}
    with wave.open(BytesIO(clean.content), "rb") as wav_file:
        duration_sec = wav_file.getnframes() / float(wav_file.getframerate())
    assert duration_sec == pytest.approx(0.2, abs=0.03)

    noisy = client.get(
        "/api/results/runs/bench_seed_a/rows/0/audio",
        params={
            "source": "clean",
            "start_sec": 0.0,
            "duration_sec": 0.2,
            "noise_mode": "pink",
            "snr_db": 15.0,
        },
    )
    assert noisy.status_code == 200
    assert noisy.headers["content-type"].startswith("audio/wav")
    assert noisy.headers["x-asr-replay-noise-mode"] == "pink"
    assert noisy.content != clean.content


def test_benchmark_run_rejects_empty_normalized_references(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    manifest_path = project_root / "datasets" / "manifests" / "bad_quality_dataset.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "sample_id": "sample_bad_ref",
                "audio_path": "data/sample/vosk_test.wav",
                "transcript": "!!!",
                "language": "en-US",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (project_root / "configs" / "datasets" / "bad_quality_dataset.yaml").write_text(
        "dataset_id: bad_quality_dataset\nmanifest_path: datasets/manifests/bad_quality_dataset.jsonl\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "bad_quality_dataset",
            "providers": ["providers/azure_cloud"],
            "run_id": "bench_bad_ref",
        },
    )

    assert response.status_code == 400
    assert "non-empty normalized reference transcripts" in response.json()["detail"]


def test_benchmark_history_and_status_reconcile_completed_artifacts_over_timeout_state(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    gateway_api._BENCHMARK_JOBS["bench_seed_a"] = {
        "run_id": "bench_seed_a",
        "state": "failed",
        "message": "Timed out waiting for benchmark result",
        "created_at": "2026-03-30T13:00:00+00:00",
        "started_at": "2026-03-30T13:00:01+00:00",
        "completed_at": "2026-03-30T13:03:01+00:00",
    }

    status = client.get("/api/benchmark/status/bench_seed_a")
    assert status.status_code == 200
    assert status.json()["state"] == "completed"
    assert status.json()["message"] == "Recovered from stored artifacts after gateway timeout"
    assert status.json()["result"]["summary"]["run_id"] == "bench_seed_a"

    history = client.get("/api/benchmark/history")
    assert history.status_code == 200
    row = next(item for item in history.json()["runs"] if item["run_id"] == "bench_seed_a")
    assert row["state"] == "completed"
    assert row["message"] == "Recovered from stored artifacts after gateway timeout"


def test_benchmark_run_rejects_parallel_active_run(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    gateway_api._BENCHMARK_JOBS["bench_active"] = {
        "run_id": "bench_active",
        "state": "running",
        "started_at": "2026-03-30T13:00:00+00:00",
    }

    response = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "sample_dataset",
            "providers": ["providers/azure_cloud"],
            "run_id": "bench_parallel_attempt",
        },
    )

    assert response.status_code == 409
    assert "Another benchmark run is already active: bench_active" in response.json()["detail"]


def test_datasets_secrets_logs_and_results_endpoints(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    datasets = client.get("/api/datasets")
    assert datasets.status_code == 200
    assert "sample_dataset" in datasets.json()["dataset_ids"]
    assert "fleurs_en_us_test_subset" in datasets.json()["dataset_ids"]

    extended_detail = client.get("/api/datasets/fleurs_en_us_test_subset")
    assert extended_detail.status_code == 200
    extended_payload = extended_detail.json()
    assert extended_payload["dataset_id"] == "fleurs_en_us_test_subset"
    assert extended_payload["sample_count"] >= 1
    assert extended_payload["preview"][0]["sample_id"].startswith("fleurs_en_us_")

    manifest_check = client.post(
        "/api/datasets/validate_manifest",
        json={
            "manifest_path": str(project_root / "datasets" / "manifests" / "sample_dataset.jsonl"),
            "check_audio_files": False,
        },
    )
    assert manifest_check.status_code == 200
    assert manifest_check.json()["sample_count"] >= 1

    secrets = client.get("/api/secrets/refs")
    assert secrets.status_code == 200
    refs = secrets.json()["refs"]
    azure = next(item for item in refs if item["name"] == "azure_speech_key")
    assert azure["validation"]["masked"] is True
    assert azure["validation"]["kind"] == "env"
    assert "AZURE_SPEECH_KEY" in azure["validation"]["env"]
    assert isinstance(azure["validation"]["valid"], bool)
    assert "runtime_ready" in (azure["validation"].get("auth") or {})

    logs = client.get("/api/logs?component=runtime&severity=all&limit=10")
    assert logs.status_code == 200
    logs_payload = logs.json()
    assert logs_payload["entry_count"] == len(logs_payload["entries"])
    assert logs_payload["files"]
    assert any("sample error" in item["message"] for item in logs_payload["entries"])
    assert all("source" in item for item in logs_payload["entries"])

    diagnostics = client.get("/api/diagnostics/issues")
    assert diagnostics.status_code == 200
    diag_payload = diagnostics.json()
    assert "counts" in diag_payload
    assert isinstance(diag_payload["counts"].get("warning", 0), int)


def test_datasets_validate_manifest_rejects_path_outside_project(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)
    manifest_path = tmp_path / "outside_manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "sample_id": "outside",
                "audio_path": "sample.wav",
                "transcript": "hello",
                "language": "en-US",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/datasets/validate_manifest",
        json={
            "manifest_path": str(manifest_path),
            "check_audio_files": False,
        },
    )

    assert response.status_code == 400
    assert "Unsafe manifest_path" in response.json()["detail"]


def test_azure_env_save_updates_secret_validation_and_local_env(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    save = client.post(
        "/api/secrets/azure_env",
        json={
            "ref_name": "azure_speech_key",
            "speech_key": "azure-test-key",
            "region": "eastus",
            "endpoint": "https://eastus.api.cognitive.microsoft.com/",
        },
    )
    assert save.status_code == 200
    payload = save.json()
    assert payload["validation"]["valid"] is True
    assert payload["validation"]["auth"]["runtime_ready"] is True
    assert payload["validation"]["auth"]["status"] == "ready"
    assert payload["validation"]["auth"]["region"] == "eastus"
    assert payload["validation"]["auth"]["speech_key_source"] == "local_env_file"

    env_file = project_root / "secrets" / "local" / "runtime.env"
    assert env_file.exists()
    env_text = env_file.read_text(encoding="utf-8")
    assert "AZURE_SPEECH_KEY=azure-test-key" in env_text
    assert "AZURE_SPEECH_REGION=eastus" in env_text

    status = client.get("/api/secrets/azure_env")
    assert status.status_code == 200
    assert status.json()["auth"]["runtime_ready"] is True

    clear = client.post(
        "/api/secrets/azure_env",
        json={
            "ref_name": "azure_speech_key",
            "clear_speech_key": True,
            "clear_region": True,
            "clear_endpoint": True,
        },
    )
    assert clear.status_code == 200
    assert clear.json()["validation"]["valid"] is False


def test_azure_env_save_accepts_full_endpoint_url_without_region(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    save = client.post(
        "/api/secrets/azure_env",
        json={
            "ref_name": "azure_speech_key",
            "speech_key": "azure-test-key",
            "clear_region": True,
            "endpoint": "https://example.invalid",
        },
    )
    assert save.status_code == 200
    payload = save.json()
    assert payload["validation"]["valid"] is True
    assert payload["validation"]["auth"]["runtime_ready"] is True
    assert payload["validation"]["auth"]["status"] == "ready"
    assert payload["validation"]["auth"]["endpoint_mode"] == "url"
    assert payload["validation"]["auth"]["region"] == ""

    env_file = project_root / "secrets" / "local" / "runtime.env"
    env_text = env_file.read_text(encoding="utf-8")
    assert "AZURE_SPEECH_KEY=azure-test-key" in env_text
    assert "ASR_AZURE_ENDPOINT=https://example.invalid" in env_text
    assert "AZURE_SPEECH_REGION=" not in env_text

    status = client.get("/api/secrets/azure_env")
    assert status.status_code == 200
    assert status.json()["auth"]["runtime_ready"] is True
    assert status.json()["auth"]["endpoint_mode"] == "url"


def test_google_service_account_upload_and_clear(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    upload = client.post(
        "/api/secrets/google_service_account/upload",
        data={"ref_name": "google_service_account"},
        files={
            "file": (
                "service-account.json",
                json.dumps(
                    {
                        "type": "service_account",
                        "project_id": "demo-project",
                        "private_key": "mock-private-key-material",
                        "client_email": "demo-account@demo-project.iam.gserviceaccount.com",
                    }
                ).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    assert payload["validation"]["valid"] is True
    assert payload["validation"]["auth"]["runtime_ready"] is True
    assert payload["validation"]["auth"]["status"] == "ready"
    assert payload["validation"]["auth"]["project_id"] == "demo-project"

    stored = project_root / "secrets" / "google" / "service-account.json"
    assert stored.exists()

    status = client.get("/api/secrets/google_service_account")
    assert status.status_code == 200
    assert status.json()["auth"]["runtime_ready"] is True

    cleared = client.post(
        "/api/secrets/google_service_account/clear", json={"ref_name": "google_service_account"}
    )
    assert cleared.status_code == 200
    assert cleared.json()["validation"]["valid"] is False
    assert stored.exists() is False


def test_google_invalid_service_account_file_marks_secret_invalid_and_dashboard_unready(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    credential_path = project_root / "secrets" / "google" / "service-account.json"
    credential_path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "demo-project",
            }
        ),
        encoding="utf-8",
    )

    status = client.get("/api/secrets/google_service_account")
    assert status.status_code == 200
    assert status.json()["validation"]["valid"] is False
    assert status.json()["auth"]["runtime_ready"] is False
    assert status.json()["auth"]["status"] == "invalid_service_account_json"

    refs = client.get("/api/secrets/refs")
    assert refs.status_code == 200
    google = next(item for item in refs.json()["refs"] if item["name"] == "google_service_account")
    assert google["validation"]["valid"] is False
    assert google["validation"]["auth"]["status"] == "invalid_service_account_json"
    assert any(
        "complete service-account JSON" in issue for issue in google["validation"]["issues"]
    )

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    google_row = next(
        item for item in dashboard.json()["cloud_credentials"] if item["provider"] == "google"
    )
    assert google_row["runtime_ready"] is False
    assert google_row["state"] == "invalid_service_account_json"


def test_secret_ref_upsert_rejects_unsafe_path(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/secrets/refs",
        json={
            "file_name": "evil_ref",
            "ref_id": "secrets/evil",
            "provider": "google",
            "kind": "file",
            "path": "../outside.json",
            "env_fallback": "GOOGLE_APPLICATION_CREDENTIALS",
            "required": [],
            "optional": [],
            "masked": True,
        },
    )

    assert response.status_code == 400
    assert "Unsafe path" in response.json()["detail"]


def test_huggingface_token_save_rejects_multiline_env_injection(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/secrets/huggingface_token",
        json={
            "ref_name": "huggingface_api_token",
            "token": "hf_demo_token\nINJECTED=1",
        },
    )

    assert response.status_code == 400
    assert "invalid control characters" in response.json()["detail"]


def test_secrets_refs_expose_structured_aws_auth_state(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _FakeAwsBackend:
        def auth_status(self):
            return {
                "profile": "ros2ws",
                "region": "eu-north-1",
                "uses_sso": True,
                "runtime_ready": True,
                "login_supported": True,
                "login_recommended": False,
                "status": "role_credentials_valid_sso_expired",
                "message": "Role credentials still work, but the SSO sign-in session is expired.",
                "sso_session_expires_at": "2026-03-16T08:00:00Z",
                "sso_session_valid": False,
                "role_credentials_expires_at": "2026-03-16T20:00:00Z",
                "role_credentials_valid": True,
                "login_command": "aws sso login --profile ros2ws",
            }

        def auth_validation_errors(self):
            return []

    monkeypatch.setattr(gateway_api, "_aws_backend_from_current_env", lambda: _FakeAwsBackend())

    response = client.get("/api/secrets/refs")

    assert response.status_code == 200
    refs = response.json()["refs"]
    aws = next(item for item in refs if item["name"] == "aws_profile")
    assert aws["validation"]["valid"] is True
    assert aws["validation"]["auth"]["status"] == "role_credentials_valid_sso_expired"
    assert aws["validation"]["auth"]["role_credentials_valid"] is True
    assert aws["validation"]["auth"]["sso_session_valid"] is False
    assert aws["validation"]["auth"]["login_supported"] is True


def test_secrets_refs_keep_aws_ref_valid_when_sso_can_mint_role_credentials(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _FakeAwsBackend:
        def auth_status(self):
            return {
                "profile": "ros2ws",
                "region": "eu-north-1",
                "uses_sso": True,
                "runtime_ready": True,
                "login_supported": True,
                "login_recommended": False,
                "status": "sso_session_valid_no_role_credentials",
                "message": (
                    "IAM Identity Center sign-in session is valid. "
                    "Active role credentials are not cached yet, "
                    "but the AWS SDK can mint them on the first real request."
                ),
                "sso_session_expires_at": "2026-03-16T20:00:00Z",
                "sso_session_valid": True,
                "role_credentials_expires_at": "",
                "role_credentials_valid": False,
                "login_command": "aws sso login --profile ros2ws",
            }

        def auth_validation_errors(self):
            return []

    monkeypatch.setattr(gateway_api, "_aws_backend_from_current_env", lambda: _FakeAwsBackend())

    response = client.get("/api/secrets/refs")

    assert response.status_code == 200
    refs = response.json()["refs"]
    aws = next(item for item in refs if item["name"] == "aws_profile")
    assert aws["validation"]["valid"] is True
    assert aws["validation"]["auth"]["status"] == "sso_session_valid_no_role_credentials"
    assert aws["validation"]["auth"]["runtime_ready"] is True
    assert aws["validation"]["auth"]["role_credentials_valid"] is False
    assert aws["validation"]["auth"]["sso_session_valid"] is True


def test_secrets_refs_keep_non_sso_aws_profile_runtime_ready(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _FakeAwsBackend:
        def auth_status(self):
            return {
                "profile": "ros2ws",
                "region": "eu-north-1",
                "uses_sso": False,
                "runtime_ready": True,
                "login_supported": False,
                "login_recommended": False,
                "status": "profile_configured",
                "message": (
                    "AWS profile is configured and does not use SSO. "
                    "The AWS SDK will resolve credentials on the first real request."
                ),
                "sso_session_expires_at": "",
                "sso_session_valid": False,
                "role_credentials_expires_at": "",
                "role_credentials_valid": False,
                "login_command": "",
            }

        def auth_validation_errors(self):
            return []

    monkeypatch.setattr(gateway_api, "_aws_backend_from_current_env", lambda: _FakeAwsBackend())

    response = client.get("/api/secrets/refs")

    assert response.status_code == 200
    refs = response.json()["refs"]
    aws = next(item for item in refs if item["name"] == "aws_profile")
    assert aws["validation"]["valid"] is True
    assert aws["validation"]["auth"]["status"] == "profile_configured"
    assert aws["validation"]["auth"]["runtime_ready"] is True
    assert aws["validation"]["auth"]["uses_sso"] is False


def test_secrets_aws_sso_login_endpoints(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    def _fake_start_aws_login_job(**kwargs):
        return {
            "job_id": "job_aws_login_demo",
            "kind": "aws_sso_login",
            "provider": "aws",
            "ref_name": kwargs["ref_name"],
            "profile": kwargs["profile"],
            "state": "running",
            "started_at": "2026-03-16T10:00:00Z",
            "completed_at": "",
            "return_code": None,
            "lines": [
                "Using a browser, open the following URL:",
                "https://d-c36767bf7f.awsapps.com/start/#/device",
                "Then enter the code:",
                "ABCD-EFGH",
            ],
            "command": [
                "aws",
                "sso",
                "login",
                "--profile",
                kwargs["profile"],
                "--no-browser",
                "--use-device-code",
            ],
            "validation": {},
        }

    monkeypatch.setattr(gateway_api, "_start_aws_login_job", _fake_start_aws_login_job)

    class _FakeProcess:
        def __init__(self):
            self._terminated = False

        def poll(self):
            return 0 if self._terminated else None

        def terminate(self):
            self._terminated = True

    fake_process = _FakeProcess()

    gateway_api._SECRET_LOGIN_JOBS["job_aws_login_demo"] = {
        "job_id": "job_aws_login_demo",
        "kind": "aws_sso_login",
        "provider": "aws",
        "ref_name": "aws_profile",
        "profile": "ros2ws",
        "state": "running",
        "started_at": "2026-03-16T10:00:00Z",
        "completed_at": "",
        "return_code": None,
        "lines": [
            "Using a browser, open the following URL:",
            "https://d-c36767bf7f.awsapps.com/start/#/device",
            "Then enter the code:",
            "ABCD-EFGH",
        ],
        "command": [
            "aws",
            "sso",
            "login",
            "--profile",
            "ros2ws",
            "--no-browser",
            "--use-device-code",
        ],
        "validation": {},
        "_process": fake_process,
    }

    start = client.post(
        "/api/secrets/aws_sso_login",
        json={
            "ref_name": "aws_profile",
            "profile": "ros2ws",
            "use_device_code": True,
            "no_browser": True,
        },
    )
    assert start.status_code == 200
    assert start.json()["job"]["kind"] == "aws_sso_login"
    assert start.json()["job"]["profile"] == "ros2ws"
    assert (
        start.json()["job"]["login_page_url"] == "https://d-c36767bf7f.awsapps.com/start/#/device"
    )
    assert start.json()["job"]["user_code"] == "ABCD-EFGH"

    status = client.get("/api/secrets/aws_sso_login/job_aws_login_demo")
    assert status.status_code == 200
    assert status.json()["job"]["state"] == "running"
    assert (
        status.json()["job"]["login_page_url"] == "https://d-c36767bf7f.awsapps.com/start/#/device"
    )
    assert status.json()["job"]["user_code"] == "ABCD-EFGH"
    assert "browser" in status.json()["job"]["lines"][0].lower()

    cancel = client.post("/api/secrets/aws_sso_login/job_aws_login_demo/cancel", json={})
    assert cancel.status_code == 200
    assert cancel.json()["job"]["state"] == "cancelled"
    assert (
        cancel.json()["job"]["login_page_url"] == "https://d-c36767bf7f.awsapps.com/start/#/device"
    )
    assert cancel.json()["job"]["user_code"] == "ABCD-EFGH"
    assert fake_process._terminated is True


def test_provider_test_returns_bad_request_for_missing_wav(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/providers/test",
        json={"provider_profile": "whisper_local", "wav_path": "missing.wav", "language": "en-US"},
    )

    assert response.status_code == 400
    assert "WAV file not found" in response.json()["detail"]


def test_provider_test_rejects_wav_outside_project(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/providers/test",
        json={
            "provider_profile": "whisper_local",
            "wav_path": str(tmp_path / "outside.wav"),
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "Unsafe wav_path" in response.json()["detail"]


def test_provider_test_tears_down_adapter_on_failure(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class ExplodingAdapter(FakeProviderAdapter):
        def __init__(self) -> None:
            super().__init__(provider_id="whisper")
            self.teardown_called = False

        def recognize_once(self, audio, options=None):  # type: ignore[override]
            del audio, options
            raise RuntimeError("recognize exploded")

        def teardown(self) -> None:
            self.teardown_called = True
            super().teardown()

    adapter = ExplodingAdapter()

    class CrashManager:
        def __init__(self, configs_root: str = "") -> None:
            self.configs_root = configs_root

        def create_from_profile(
            self,
            provider_profile: str,
            *,
            preset_id: str = "",
            settings_overrides: dict[str, object] | None = None,
        ) -> ExplodingAdapter:
            del provider_profile, preset_id, settings_overrides
            return adapter

    monkeypatch.setattr(gateway_api, "ProviderManager", CrashManager)
    monkeypatch.setattr(
        gateway_api,
        "_preflight_provider_profile",
        lambda *args, **kwargs: {
            "normalized_profile": "providers/whisper_local",
            "execution": {"selected_preset": ""},
        },
    )

    response = client.post(
        "/api/providers/test",
        json={
            "provider_profile": "whisper_local",
            "wav_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "recognize exploded" in response.json()["detail"]
    assert adapter.teardown_called is True


def test_provider_catalog_distinguishes_ready_and_degraded_profiles(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)
    _write_provider_profile(project_root / "configs", "azure_invalid", "azure")
    monkeypatch.setattr(
        gateway_api,
        "list_providers",
        lambda *args, **kwargs: ["whisper", "azure", "nemo"],
    )

    response = client.get("/api/providers/catalog")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["providers"]}
    assert providers["whisper"]["status"] == "ready"
    assert providers["whisper"]["runtime_ready"] is True
    assert providers["azure"]["status"] == "degraded"
    assert providers["azure"]["runtime_ready"] is True
    assert providers["azure"]["invalid_profiles"] >= 1
    assert providers["nemo"]["status"] == "not_configured"
    assert providers["nemo"]["runtime_ready"] is False


def test_provider_catalog_lists_huggingface_local_and_api_profiles(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)
    monkeypatch.setattr(
        gateway_api,
        "list_providers",
        lambda *args, **kwargs: ["huggingface_local", "huggingface_api"],
    )

    response = client.get("/api/providers/catalog")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["providers"]}
    assert providers["huggingface_local"]["kind"] == "local"
    assert providers["huggingface_local"]["runtime_ready"] is True
    assert providers["huggingface_local"]["status"] == "ready"
    assert providers["huggingface_api"]["kind"] == "cloud"
    assert providers["huggingface_api"]["capabilities"]["requires_network"] is True
    assert providers["huggingface_api"]["runtime_ready"] is True
    assert providers["huggingface_api"]["status"] == "ready"


def test_runtime_start_rejects_invalid_provider_preflight(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _RejectingManager:
        def __init__(self, configs_root: str = "configs") -> None:
            self.configs_root = configs_root

        def resolve_profile_payload(self, provider_profile: str):
            return {"provider_id": provider_profile.split("/")[-1]}

        def create_from_profile(
            self,
            provider_profile: str,
            *,
            preset_id: str = "",
            settings_overrides: dict | None = None,
        ):
            del provider_profile, preset_id, settings_overrides
            raise ValueError("Provider config validation failed: AWS SSO token expired")

    monkeypatch.setattr(gateway_api, "ProviderManager", _RejectingManager)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/aws_cloud",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )

    assert response.status_code == 400
    assert "AWS SSO token expired" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_invalid_processing_mode(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "broken_mode",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "orchestrator.processing_mode must be one of" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_invalid_audio_source(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "segmented",
            "audio_source": "broken_source",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "audio.source must be one of" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_auto_audio_source(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "segmented",
            "audio_source": "auto",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "audio.source must be one of: file, mic" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_missing_runtime_wav(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "segmented",
            "audio_source": "file",
            "audio_file_path": "data/sample/missing.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 404
    assert "Runtime WAV not found" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_provider_stream_for_non_streaming_provider(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)
    _write_provider_profile(
        project_root / "configs", "fake_batch_only", "fake_batch_only_component"
    )

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/fake_batch_only",
            "processing_mode": "provider_stream",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "does not support processing_mode=provider_stream" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_start_rejects_provider_stream_for_whisper(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "provider_stream",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        },
    )

    assert response.status_code == 400
    assert "does not support processing_mode=provider_stream" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_runtime_recognize_once_rejects_missing_runtime_sample(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/recognize_once",
        json={
            "wav_path": "data/sample/missing.wav",
            "language": "en-US",
            "provider_profile": "providers/whisper_local",
        },
    )

    assert response.status_code == 404
    assert "Runtime WAV not found" in response.json()["detail"]


def test_benchmark_run_rejects_streaming_for_non_streaming_provider(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)
    _write_provider_profile(
        project_root / "configs", "fake_batch_only", "fake_batch_only_component"
    )

    response = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "sample_dataset",
            "providers": ["providers/fake_batch_only"],
            "benchmark_settings": {"execution_mode": "streaming"},
        },
    )

    assert response.status_code == 400
    assert "does not support streaming benchmark mode" in response.json()["detail"]


def test_benchmark_run_rejects_provider_overrides_for_unselected_provider(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "sample_dataset",
            "providers": ["providers/whisper_local"],
            "provider_overrides": {
                "providers/azure_cloud": {
                    "preset_id": "",
                    "settings": {},
                }
            },
            "benchmark_settings": {"execution_mode": "batch"},
        },
    )

    assert response.status_code == 400
    assert "provider_overrides contains profiles that are not selected" in response.json()["detail"]


def test_dataset_import_upload_registers_manifest(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)
    sample_wav = repo_root / "data" / "sample" / "vosk_test.wav"

    response = client.post(
        "/api/datasets/import_upload",
        data={
            "dataset_id": "upload_demo",
            "dataset_profile": "upload_demo",
            "language": "en-US",
        },
        files=[
            ("files", ("vosk_test.wav", sample_wav.read_bytes(), "audio/wav")),
            ("files", ("vosk_test.txt", b"10001 90210 01803\n", "text/plain")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == "upload_demo"
    manifest_path = project_root / "datasets" / "manifests" / "upload_demo.jsonl"
    assert manifest_path.exists()
    datasets = client.get("/api/datasets").json()
    assert "upload_demo" in datasets["dataset_ids"]
