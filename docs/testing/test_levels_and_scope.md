# Test Levels And Scope

| Level | Purpose | Primary Targets | Default CI |
|---|---|---|---|
| `unit` | Validate isolated logic | config loader, secrets, manifests, metrics, artifact helpers | Yes |
| `component` | Validate module behavior end-to-end without full stack | provider manager, benchmark orchestrator | Yes |
| `contract` | Lock architectural behavior | provider adapters, gateway contracts, normalized results, dataset manifests | Yes |
| `api` | Validate backend HTTP surface | runtime, benchmark, datasets, results, logs, secrets | Yes |
| `gui` | Validate served GUI shell/assets | index page, frontend asset wiring | Yes |
| `integration` | Validate CLI/manual engineering flows | scripts and subprocess entry points | Yes |
| `regression` | Prevent storage/schema drift | artifact layout and reproducibility shape | Yes |
| `e2e` | Validate human-visible browser flows | runtime/benchmark/results/diagnostics | No |
| `ros` | Validate ROS graph behavior | services/actions/topics/launch | No |
| `cloud` | Validate real provider integrations | Azure/Google/AWS live behavior | No |

## Scope Rules
- `unit` must be deterministic and filesystem-light.
- `component` may use temp directories and fake adapters.
- `contract` must assert required fields/behaviors explicitly.
- `api` must not depend on a live ROS graph in the fast suite.
- `e2e` must use a real browser and real frontend JavaScript execution.
- `ros` and `cloud` are intentionally excluded from baseline CI to avoid flakiness and credential coupling.
