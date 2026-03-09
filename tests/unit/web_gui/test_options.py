from __future__ import annotations

from web_gui.app.options import get_options_payload


def test_options_payload_exposes_discovered_base_configs() -> None:
    payload = get_options_payload()
    base_configs = payload.get("base_configs", [])

    assert "configs/default.yaml" in base_configs
    assert "configs/live_mic_whisper.yaml" in base_configs
    assert "configs/web_latest_local_matrix.yaml" in base_configs
    assert "configs/commercial.example.yaml" not in base_configs


def test_options_payload_includes_scenario_catalog_and_defaults_map() -> None:
    payload = get_options_payload()
    defaults = payload.get("defaults_by_config", {})
    scenario_catalog = payload.get("scenario_presets", [])

    assert "configs/web_latest_cloud_matrix.yaml" in defaults
    web_cfg = defaults["configs/web_latest_cloud_matrix.yaml"].get("web", {})
    assert web_cfg.get("scenario_label") == "Web: Latest Cloud Matrix"

    labels = {item.get("label", "") for item in scenario_catalog}
    assert "Web: ROS Wrapper E2E" in labels


def test_options_payload_includes_dropdown_catalogs() -> None:
    payload = get_options_payload()

    assert "language_modes" in payload
    assert "input_modes" in payload
    assert "model_run_presets" in payload
    assert "benchmark_backend_presets" in payload
    assert "sample_rates" in payload
    assert "chunk_ms_values" in payload
    assert "noise_level_presets" in payload
    assert "aws_auth_profiles" in payload
    assert "aws_sso_start_urls" in payload
    assert "aws_sso_regions" in payload
