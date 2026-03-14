# E2E User Flows

## Flow 1: Runtime Happy Path
1. Open GUI root page.
2. Navigate to Runtime.
3. Start runtime session.
4. Run `Recognize Once`.
5. Confirm transcript appears in live transcription.
6. Stop runtime.
7. Confirm runtime returns to idle.

## Flow 2: Benchmark To Results
1. Open Benchmark page.
2. Launch benchmark run.
3. Observe active run/status.
4. Open Results from benchmark history.
5. Confirm run detail is visible.

## Flow 3: Diagnostics Visibility
1. Open Logs & Diagnostics.
2. Confirm diagnostic issues are rendered.
3. Verify missing secret ref problems are human-visible.

## Flow Coverage Notes
- These flows use the real frontend and browser engine.
- Backend state is deterministic and fake-driven to keep assertions stable.
- Future work: dataset import browser flow, provider setup flow, page reload/back-navigation stress cases.
