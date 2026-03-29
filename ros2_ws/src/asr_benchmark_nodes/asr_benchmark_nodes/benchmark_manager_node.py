"""ROS2 benchmark manager node exposing actions/services for benchmark and datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import rclpy
from asr_benchmark_core import BenchmarkOrchestrator, BenchmarkRunRequest
from asr_core import make_run_id
from asr_core.shutdown import safe_shutdown_node
from asr_datasets import DatasetEntry, DatasetRegistry, import_from_folder, load_manifest
from asr_interfaces.action import ImportDataset, RunBenchmarkExperiment
from asr_interfaces.msg import BenchmarkJobStatus, DatasetStatus, ExperimentSummary
from asr_interfaces.srv import GetBenchmarkStatus, ListDatasets, RegisterDataset
from rclpy.action import ActionServer
from rclpy.node import Node


class BenchmarkManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("benchmark_manager_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("artifacts_root", "artifacts")
        self.declare_parameter("registry_path", "datasets/registry/datasets.json")

        cwd = Path.cwd()
        raw_configs_root = str(self.get_parameter("configs_root").value)
        raw_artifacts_root = str(self.get_parameter("artifacts_root").value)
        raw_registry_path = str(self.get_parameter("registry_path").value)

        self.configs_root = str((cwd / raw_configs_root).resolve()) if not Path(raw_configs_root).is_absolute() else raw_configs_root
        self.artifacts_root = (
            str((cwd / raw_artifacts_root).resolve()) if not Path(raw_artifacts_root).is_absolute() else raw_artifacts_root
        )
        self.registry_path = (
            str((cwd / raw_registry_path).resolve()) if not Path(raw_registry_path).is_absolute() else raw_registry_path
        )

        self.registry = DatasetRegistry(self.registry_path)

        # Keep simple in-memory status so GUI and scripts can ask "what is the
        # current state of run X?" without reading artifacts on every request.
        self.run_status: dict[str, BenchmarkJobStatus] = {}

        # This node is intentionally a ROS-facing shell around benchmark_core:
        # it exposes actions/services, while core code performs the heavy work.
        self.run_action = ActionServer(
            self,
            RunBenchmarkExperiment,
            "/benchmark/run_experiment",
            execute_callback=self._execute_benchmark,
        )
        self.import_action = ActionServer(
            self,
            ImportDataset,
            "/datasets/import",
            execute_callback=self._execute_import,
        )

        self.get_status_srv = self.create_service(
            GetBenchmarkStatus,
            "/benchmark/get_status",
            self._on_get_status,
        )
        self.register_dataset_srv = self.create_service(
            RegisterDataset,
            "/datasets/register",
            self._on_register_dataset,
        )
        self.list_datasets_srv = self.create_service(
            ListDatasets,
            "/datasets/list",
            self._on_list_datasets,
        )

    def _build_orchestrator(self) -> BenchmarkOrchestrator:
        return BenchmarkOrchestrator(
            configs_root=self.configs_root,
            artifact_root=self.artifacts_root,
            registry_path=self.registry_path,
        )

    def _execute_benchmark(self, goal_handle):
        # A benchmark run is a long-lived action because it may process many
        # samples/providers and should report progress back to the caller.
        request = goal_handle.request
        raw_run_id = str(request.run_id).strip()
        run_id = raw_run_id if raw_run_id and raw_run_id.lower() not in {"none", "null"} else make_run_id("bench")

        status_msg = BenchmarkJobStatus()
        status_msg.run_id = run_id
        status_msg.state = "running"
        status_msg.providers = list(request.providers)
        status_msg.status_message = "Benchmark started"
        self.run_status[run_id] = status_msg
        goal_handle.publish_feedback(RunBenchmarkExperiment.Feedback(status=status_msg))

        try:
            result = self._build_orchestrator().run(
                BenchmarkRunRequest(
                    benchmark_profile=request.benchmark_profile,
                    dataset_profile=request.dataset_profile,
                    providers=list(request.providers),
                    scenario=str(request.scenario or ""),
                    provider_overrides=self._parse_json_object(request.provider_overrides_json, "provider_overrides_json"),
                    benchmark_settings=self._parse_json_object(request.benchmark_settings_json, "benchmark_settings_json"),
                    run_id=run_id,
                )
            )
            status_msg.state = "completed"
            status_msg.total_samples = int(result.total_samples)
            status_msg.processed_samples = int(result.total_samples)
            status_msg.failed_samples = int(result.failed_samples)
            status_msg.progress = 1.0
            status_msg.status_message = "Benchmark completed"
            self.run_status[run_id] = status_msg

            summary = ExperimentSummary()
            summary.run_id = result.run_id
            summary.benchmark_profile_id = result.benchmark_profile
            summary.dataset_id = result.dataset_id
            summary.providers = result.providers
            summary.total_samples = int(result.total_samples)
            summary.successful_samples = int(result.successful_samples)
            summary.failed_samples = int(result.failed_samples)
            summary.mean_wer = float(result.mean_metrics.get("wer", 0.0))
            summary.mean_cer = float(result.mean_metrics.get("cer", 0.0))
            summary.mean_latency_ms = float(result.mean_metrics.get("total_latency_ms", 0.0))
            summary.summary_artifact_ref = result.artifacts.get("summary_json", "")

            goal_handle.succeed()
            action_result = RunBenchmarkExperiment.Result()
            action_result.success = True
            action_result.run_id = result.run_id
            action_result.message = "Benchmark completed"
            action_result.summary = summary
            return action_result
        except Exception as exc:
            status_msg.state = "failed"
            status_msg.error_message = str(exc)
            status_msg.status_message = "Benchmark failed"
            self.run_status[run_id] = status_msg
            goal_handle.abort()
            action_result = RunBenchmarkExperiment.Result()
            action_result.success = False
            action_result.run_id = run_id
            action_result.message = str(exc)
            return action_result

    def _execute_import(self, goal_handle):
        # Import supports two user paths:
        # 1. register an existing JSONL manifest;
        # 2. scan a folder and create a manifest automatically.
        request = goal_handle.request

        status = DatasetStatus()
        status.dataset_id = request.dataset_id
        status.state = "running"
        status.status_message = "Import started"
        goal_handle.publish_feedback(ImportDataset.Feedback(status=status))

        try:
            if request.source_path.endswith(".jsonl"):
                samples = load_manifest(request.source_path)
                manifest_ref = request.source_path
                sample_count = len(samples)
            else:
                manifest_ref, sample_count = import_from_folder(
                    source_folder=request.source_path,
                    target_dataset_id=request.dataset_id,
                )

            self.registry.register(
                DatasetEntry(
                    dataset_id=request.dataset_id,
                    manifest_ref=manifest_ref,
                    sample_count=sample_count,
                    metadata={"dataset_profile": request.dataset_profile},
                )
            )

            status.state = "completed"
            status.sample_count = int(sample_count)
            status.manifest_ref = manifest_ref
            status.status_message = "Import completed"
            goal_handle.publish_feedback(ImportDataset.Feedback(status=status))

            goal_handle.succeed()
            result = ImportDataset.Result()
            result.success = True
            result.dataset_id = request.dataset_id
            result.manifest_ref = manifest_ref
            result.message = "Dataset imported"
            return result
        except Exception as exc:
            status.state = "failed"
            status.error_message = str(exc)
            status.status_message = "Import failed"
            goal_handle.publish_feedback(ImportDataset.Feedback(status=status))
            goal_handle.abort()
            result = ImportDataset.Result()
            result.success = False
            result.dataset_id = request.dataset_id
            result.message = str(exc)
            return result

    @staticmethod
    def _parse_json_object(raw: str, field_name: str) -> dict[str, Any]:
        # ROS actions/services carry rich override payloads as JSON strings.
        value = str(raw or "").strip()
        if not value:
            return {}
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return parsed

    def _on_get_status(self, request: GetBenchmarkStatus.Request, response: GetBenchmarkStatus.Response):
        status = self.run_status.get(request.run_id)
        if status is None:
            status = BenchmarkJobStatus()
            status.run_id = request.run_id
            status.state = "unknown"
            status.status_message = "Run ID not found"
        response.status = status
        return response

    def _on_register_dataset(self, request: RegisterDataset.Request, response: RegisterDataset.Response):
        try:
            samples = load_manifest(request.manifest_path)
            entry = DatasetEntry(
                dataset_id=request.dataset_id,
                manifest_ref=request.manifest_path,
                sample_count=len(samples),
                metadata={"dataset_profile": request.dataset_profile},
            )
            self.registry.register(entry)
            response.success = True
            response.dataset_id = request.dataset_id
            response.message = "Dataset registered"
        except Exception as exc:
            response.success = False
            response.dataset_id = request.dataset_id
            response.message = str(exc)
        return response

    def _on_list_datasets(self, request: ListDatasets.Request, response: ListDatasets.Response):
        del request
        entries = self.registry.list()
        response.dataset_ids = [item.dataset_id for item in entries]
        response.dataset_manifest_refs = [item.manifest_ref for item in entries]
        return response


def main() -> None:
    rclpy.init()
    node = BenchmarkManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
