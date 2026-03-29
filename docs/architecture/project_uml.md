# Project UML

This document groups the UML source files for the current modular ROS2 ASR baseline.

One diagram for the entire workspace would be unreadable, so the project model is split into four complementary views:

- `uml/01_ros2_package_view.puml` - full ROS2 package dependency view from `package.xml`.
- `uml/02_runtime_gateway_view.puml` - runtime pipeline, gateway boundary, provider path, configs, and secrets.
- `uml/03_core_provider_class_view.puml` - core abstractions, provider contracts, benchmark/storage classes.
- `uml/04_benchmark_sequence_view.puml` - end-to-end benchmark flow from UI request to persisted artifacts.

Coverage includes:

- the current modular baseline packages,
- the runtime vs benchmark architecture split,
- the GUI -> gateway -> ROS2 boundary,
- compatibility packages still kept during migration (`asr_ros`, `asr_benchmark`).

This UML set complements the auto-generated Mermaid architecture output in `docs/arch/`.

## Render

If PlantUML CLI is installed:

```bash
plantuml docs/architecture/uml/*.puml
```

If only the JAR is available:

```bash
java -jar plantuml.jar docs/architecture/uml/*.puml
```
