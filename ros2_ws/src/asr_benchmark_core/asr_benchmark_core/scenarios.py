"""Benchmark scenario manager baseline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Scenario:
    name: str
    description: str


DEFAULT_SCENARIOS = {
    "clean_baseline": Scenario(
        name="clean_baseline",
        description="Baseline scenario on clean audio without synthetic perturbations.",
    ),
    "noise_robustness": Scenario(
        name="noise_robustness",
        description=(
            "Noise-robustness sweep across clean plus synthetic additive-noise variants."
        ),
    ),
    "provider_comparison": Scenario(
        name="provider_comparison",
        description="Cross-provider comparison under the same dataset and profile settings.",
    ),
    "latency_profile": Scenario(
        name="latency_profile",
        description="Latency-focused run with timing metrics enabled.",
    ),
}


class ScenarioManager:
    def resolve(self, names: list[str]) -> list[Scenario]:
        resolved: list[Scenario] = []
        for name in names:
            if name in DEFAULT_SCENARIOS:
                resolved.append(DEFAULT_SCENARIOS[name])
        return resolved
