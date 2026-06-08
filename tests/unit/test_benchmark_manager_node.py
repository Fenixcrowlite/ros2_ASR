from __future__ import annotations

from types import SimpleNamespace

from asr_benchmark_nodes.benchmark_manager_node import BenchmarkManagerNode


class _FakeRegistry:
    def __init__(self) -> None:
        self.entries = []

    def register(self, entry) -> None:
        self.entries.append(entry)


class _FakeNode:
    def __init__(self) -> None:
        self.registry = _FakeRegistry()


def test_register_dataset_service_persists_entry(monkeypatch) -> None:
    node = _FakeNode()
    request = SimpleNamespace(
        dataset_id="sample_dataset",
        dataset_profile="datasets/sample_dataset",
        manifest_path="datasets/manifests/sample_dataset.jsonl",
    )
    response = SimpleNamespace(success=False, dataset_id="", message="")
    monkeypatch.setattr(
        "asr_benchmark_nodes.benchmark_manager_node.load_manifest",
        lambda manifest_path: [{"manifest_path": manifest_path}],
    )

    result = BenchmarkManagerNode._on_register_dataset(node, request, response)

    assert result.success is True
    assert result.dataset_id == "sample_dataset"
    assert result.message == "Dataset registered"
    assert len(node.registry.entries) == 1
    assert node.registry.entries[0].dataset_id == "sample_dataset"
    assert node.registry.entries[0].metadata["dataset_profile"] == "datasets/sample_dataset"


def test_register_dataset_service_returns_error(monkeypatch) -> None:
    node = _FakeNode()
    request = SimpleNamespace(
        dataset_id="broken_dataset",
        dataset_profile="datasets/broken_dataset",
        manifest_path="datasets/manifests/missing.jsonl",
    )
    response = SimpleNamespace(success=True, dataset_id="", message="")
    monkeypatch.setattr(
        "asr_benchmark_nodes.benchmark_manager_node.load_manifest",
        lambda manifest_path: (_ for _ in ()).throw(FileNotFoundError(manifest_path)),
    )

    result = BenchmarkManagerNode._on_register_dataset(node, request, response)

    assert result.success is False
    assert result.dataset_id == "broken_dataset"
    assert "missing.jsonl" in result.message
    assert node.registry.entries == []
