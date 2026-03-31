from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def test_frontend_shell_and_assets_are_served(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_gui_seed", wer=0.0, cer=0.0)

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

    client = TestClient(gateway_api.app)

    index = client.get("/")
    styles = client.get("/ui/styles.css")
    script = client.get("/ui/js/app.js")
    action_runner = client.get("/ui/js/action-runner.js")
    results_page_script = client.get("/ui/js/pages/results.js")
    benchmark_page_script = client.get("/ui/js/pages/benchmark.js")

    assert index.status_code == 200
    assert "ROS2 ASR Platform" in index.text
    assert 'data-page="runtime"' in index.text
    assert 'data-page="benchmark"' in index.text
    assert 'id="runtimeProcessingMode"' in index.text
    assert 'id="runtimeSampleSelect"' in index.text
    assert 'id="runtimeSampleDropzone"' in index.text
    assert 'id="runtimeSampleUploadInput"' in index.text
    assert 'id="runtimeGenerateNoiseBtn"' in index.text
    assert "Start Live Runtime" in index.text
    assert "Transcribe Whole File" in index.text
    assert 'id="benchmarkExecutionMode"' in index.text
    assert 'id="benchmarkStreamingChunkMs"' in index.text
    assert 'id="dashboardCloudHealth"' in index.text
    assert 'class="guide-card"' in index.text
    assert 'id="commonLanguageOptions"' in index.text
    assert 'id="providerProfileOptions"' in index.text
    assert 'id="diagnosticsPreflightBtn"' in index.text
    assert 'id="awsAuthSummary"' in index.text
    assert 'id="awsSsoLoginBtn"' in index.text
    assert 'id="awsSsoAutoOpenPage"' in index.text
    assert 'id="awsSsoLoginUrl"' in index.text
    assert 'id="awsSsoOpenLoginPageBtn"' in index.text
    assert 'id="awsSsoCopyLoginPageBtn"' in index.text
    assert 'id="awsSsoDeviceCode"' in index.text
    assert 'id="awsSsoCopyDeviceCodeBtn"' in index.text
    assert 'id="awsSsoLoginFeedback"' in index.text
    assert 'id="googleAuthSummary"' in index.text
    assert 'id="googleUploadBtn"' in index.text
    assert 'id="googleValidateProviderBtn"' in index.text
    assert 'id="azureAuthSummary"' in index.text
    assert 'id="azureSaveBtn"' in index.text
    assert 'id="azureValidateProviderBtn"' in index.text
    assert "/ui/styles.css" in index.text
    assert "/ui/js/app.js" in index.text
    assert index.headers["cache-control"].startswith("no-store")
    assert styles.status_code == 200
    assert styles.headers["cache-control"].startswith("no-store")
    assert script.status_code == 200
    assert script.headers["cache-control"].startswith("no-store")
    assert action_runner.status_code == 200
    assert action_runner.headers["cache-control"].startswith("no-store")
    assert results_page_script.status_code == 200
    assert "Exact Match Rate" in results_page_script.text
    assert "referenceHasContent && normalizedReference === normalizedHypothesis" in results_page_script.text
    assert "referenceWords.length || hypothesisWords.length" not in results_page_script.text
    assert "referenceChars.length || hypothesisChars.length" not in results_page_script.text
    assert benchmark_page_script.status_code == 200
    assert "Exact Match Rate" in benchmark_page_script.text
