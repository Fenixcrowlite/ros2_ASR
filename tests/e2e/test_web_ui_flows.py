from __future__ import annotations

import importlib
import socket
import threading
import time
from pathlib import Path

import pytest
import requests
import uvicorn

from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs

pytestmark = [pytest.mark.e2e, pytest.mark.gui, pytest.mark.slow]


def _find_free_tcp_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except PermissionError as exc:
        pytest.skip(f"local TCP bind is not permitted in this environment: {exc}")


@pytest.fixture()
def live_gateway(repo_root: Path, tmp_path: Path, monkeypatch):
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_ui_seed_a", wer=0.0, cer=0.0)
    seed_benchmark_run(project_root, "bench_ui_seed_b", wer=0.15, cer=0.08)
    (project_root / "configs" / "providers" / "fake_batch_only.yaml").write_text(
        "provider_id: fake_batch_only_component\nsettings: {}\n",
        encoding="utf-8",
    )

    fake_ros = FakeGatewayRosClient(project_root=project_root)
    import asr_gateway.ros_client as ros_client_module

    monkeypatch.setenv("ASR_PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(ros_client_module, "GatewayRosClient", lambda timeout_sec=5.0: fake_ros)
    import asr_gateway.api as gateway_api

    gateway_api = importlib.reload(gateway_api)
    monkeypatch.setattr(gateway_api, "ProviderManager", build_stub_provider_manager(str(project_root / "configs")))
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

    port = _find_free_tcp_port()
    config = uvicorn.Config(gateway_api.app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 10.0
    base_url = f"http://127.0.0.1:{port}"
    while time.time() < deadline:
        try:
            if requests.get(f"{base_url}/api/health", timeout=0.5).status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        server.should_exit = True
        thread.join(timeout=2.0)
        raise AssertionError("gateway server did not start")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5.0)


@pytest.fixture()
def browser_page():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        try:
            yield page
        finally:
            page.close()
            browser.close()


def test_runtime_happy_path_is_visible_in_gui(live_gateway: str, browser_page) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.wait_for_selector("text=Dashboard")

    page.click('button[data-page="runtime"]')
    page.wait_for_selector("#runtimeStatusSummary")
    page.click("#runtimeStartBtn")
    page.wait_for_timeout(300)
    assert "active" in page.locator("#runtimeStatusSummary").inner_text().lower()

    page.click("#runtimeRecognizeBtn")
    page.wait_for_timeout(500)
    assert "recognized from vosk_test.wav" in page.locator("#runtimeTranscripts").inner_text()

    page.click("#runtimeStopBtn")
    page.wait_for_timeout(300)
    assert "idle" in page.locator("#runtimeStatusSummary").inner_text().lower()


def test_runtime_invalid_provider_stream_combo_surfaces_error_in_gui(
    live_gateway: str, browser_page
) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.wait_for_selector("text=Dashboard")

    page.click('button[data-page="runtime"]')
    page.select_option("#runtimeProviderSelect", "fake_batch_only")
    page.select_option("#runtimeProcessingMode", "provider_stream")
    page.click("#runtimeStartBtn")
    page.wait_for_timeout(300)

    feedback = page.locator("#runtimeFeedback").inner_text().lower()
    assert "does not support provider_stream mode" in feedback
    assert "active" not in page.locator("#runtimeStatusSummary").inner_text().lower()


def test_runtime_provider_stream_is_blocked_for_whisper_in_gui(
    live_gateway: str, browser_page
) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.wait_for_selector("text=Dashboard")

    page.click('button[data-page="runtime"]')
    page.select_option("#runtimeProviderSelect", "whisper_local")
    page.wait_for_timeout(200)

    provider_stream_disabled = page.locator('#runtimeProcessingMode option[value="provider_stream"]').evaluate(
        "el => el.disabled"
    )
    assert provider_stream_disabled is True
    assert page.locator("#runtimeProcessingMode").input_value() == "segmented"
    meta = page.locator("#runtimeProviderPresetMeta").inner_text().lower()
    assert "provider stream is unavailable for this provider" in meta


def test_benchmark_to_results_and_diagnostics_flow(live_gateway: str, browser_page) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.click('button[data-page="benchmark"]')
    page.wait_for_selector("text=Run Builder")

    page.click("#benchmarkRunBtn")
    page.wait_for_timeout(800)
    assert "bench" in page.locator("#benchmarkActiveRun").inner_text().lower()

    page.click('#benchmarkHistoryTable button[data-action="open_results"]')
    page.wait_for_timeout(500)
    results_text = page.locator("#results").inner_text()
    assert "Run Overview" in results_text
    assert "Sample Explorer" in results_text

    page.click('button[data-page="logs"]')
    page.wait_for_timeout(500)
    assert "Diagnostics" in page.locator("#logs").inner_text()
    issues_text = page.locator("#diagnosticsIssues").inner_text().lower()
    assert "secret ref" in issues_text
    assert "ensure required env vars/files exist" in issues_text
    logs_text = page.locator("#logsViewer").inner_text().lower()
    assert "sample error" in logs_text
    assert "runtime.log" in page.locator("#logsMeta").inner_text().lower()


def test_benchmark_audio_preview_loads_in_gui(live_gateway: str, browser_page) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.click('button[data-page="benchmark"]')
    page.wait_for_selector("#benchmarkAudioPreview")

    page.click('[data-benchmark-preview-load]')
    page.wait_for_timeout(800)

    preview_text = page.locator("#benchmarkAudioPreview").inner_text().lower()
    assert "preview ready" in preview_text
    audio_src = page.locator(".benchmark-preview-player").evaluate("el => el.currentSrc || el.src || ''")
    assert audio_src.startswith("blob:")


def test_benchmark_audio_preview_supports_custom_snr_in_gui(live_gateway: str, browser_page) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.click('button[data-page="benchmark"]')
    page.wait_for_selector("#benchmarkAudioPreview")

    page.fill("#benchmarkCustomNoiseSnr", "17.5")
    page.wait_for_timeout(200)
    page.select_option("[data-benchmark-preview-level]", "custom")
    page.fill("[data-benchmark-preview-snr]", "17.5")
    page.click("[data-benchmark-preview-load]")
    page.wait_for_timeout(800)

    preview_text = page.locator("#benchmarkAudioPreview").inner_text().lower()
    assert "preview ready: custom 17.5 db via" in preview_text
    audio_src = page.locator(".benchmark-preview-player").evaluate("el => el.currentSrc || el.src || ''")
    assert audio_src.startswith("blob:")


def test_benchmark_invalid_streaming_combo_surfaces_error_in_gui(
    live_gateway: str, browser_page
) -> None:
    page = browser_page
    page.goto(live_gateway, wait_until="domcontentloaded")
    page.click('button[data-page="benchmark"]')
    page.wait_for_selector("text=Run Builder")

    page.locator('input[type="checkbox"][value="whisper_local"]').uncheck()
    page.locator('input[type="checkbox"][value="fake_batch_only"]').check()
    page.select_option("#benchmarkExecutionMode", "streaming")
    page.click("#benchmarkRunBtn")
    page.wait_for_timeout(300)

    review_text = page.locator("#benchmarkReview").inner_text().lower()
    assert "streaming benchmark mode requires streaming-capable providers" in review_text
