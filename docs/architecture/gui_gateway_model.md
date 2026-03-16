# GUI / Gateway Model

## Rule
GUI must not access runtime internals directly.
All control and data access passes through gateway API.

## Gateway responsibilities
- Validate profiles/config via ROS service bridge.
- Trigger runtime session start/stop/reconfigure.
- Trigger recognize-once calls.
- Trigger benchmark runs and fetch status.
- Register/list datasets.
- Expose artifact and secret-ref metadata endpoints.
- Translate provider-native auth nuance into human-readable UI state.
- For AWS IAM Identity Center / SSO, expose both:
  - sign-in session health
  - effective role-credential health used by runtime/benchmark requests
- Provide a safe GUI-triggered native login path (`aws sso login`) so operators can recover from expired AWS sign-in sessions without dropping to a terminal.

## Baseline implementation
- ROS package: `asr_gateway`
- API app: `asr_gateway.api`
- Client bridge: `asr_gateway.ros_client`
- Web skeleton: `web_ui/frontend`

## GUI baseline pages
- dashboard
- runtime control
- providers
- profiles
- datasets
- benchmark
- results
- logs/diagnostics
- secrets/credentials metadata

## Secrets UX contract
- GUI never stores raw cloud secrets in client-side state longer than the active request lifecycle.
- `Secrets` is the operator-facing place for:
  - seeing whether credentials are configured
  - seeing whether credentials are usable right now
  - understanding why a provider is blocked
  - initiating supported recovery actions
- For Azure, GUI can save native env vars into the local ignored env-injection file (`secrets/local/runtime.env`) so both gateway validation and runtime/provider initialization can resolve them without putting secrets into tracked YAML.
- For Google, GUI can upload the native service-account JSON into the ignored `secrets/google/service-account.json` path used by the provider profile. The gateway exposes metadata and readiness, but never echoes private key material back to the UI.
- AWS is modeled as a richer state machine than a plain `valid/invalid` flag because an expired SSO sign-in session does not always mean runtime use has already stopped. The gateway is responsible for making that distinction explicit.

## Dashboard auth visibility
- `Dashboard` includes a cloud credential readiness board for `google`, `azure`, and `aws`.
- Its purpose is to answer one operator question quickly: which cloud providers are actually ready to run right now.
- This keeps provider auth state visible without forcing the user to open `Secrets` first.
