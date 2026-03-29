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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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
        lambda provider_id: build_stub_provider_manager(str(project_root / "configs"))().create_from_profile(
            f"providers/{'azure_cloud' if provider_id == 'azure' else 'whisper_local'}"
        ),
    )
    monkeypatch.setattr(gateway_api, "list_providers", lambda: ["whisper", "azure", "aws"])

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

    page.click("text=Open Results")
    page.wait_for_timeout(500)
    assert "Run Detail" in page.locator("#results").inner_text()

    page.click('button[data-page="logs"]')
    page.wait_for_timeout(500)
    assert "Diagnostics" in page.locator("#logs").inner_text()
    issues_text = page.locator("#diagnosticsIssues").inner_text().lower()
    assert "secret ref" in issues_text
    assert "ensure required env vars/files exist" in issues_text


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
