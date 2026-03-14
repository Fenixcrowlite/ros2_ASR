# User Flows

## 1. Quick Runtime Start (operator)
1. Open Dashboard.
2. Confirm gateway/runtime health is not critical.
3. Click `Start Runtime` quick action or open Runtime page.
4. Select runtime and provider profiles.
5. Start runtime.
6. Run recognize-once sample or provide audio source.
7. Observe partial/final output and session status.

## 2. Runtime Profile Setup (engineer)
1. Open Profiles page.
2. Filter by `runtime` type.
3. Open profile in guided editor.
4. Edit language/audio/provider/VAD options.
5. Validate profile.
6. Save and apply via Runtime page.

## 3. Connect New Provider
1. Open Providers page.
2. Inspect provider catalog and capabilities.
3. Choose provider profile.
4. Link credential reference if required.
5. Run `Validate` and `Test`.
6. Use profile in Runtime/Benchmark.

## 4. Credentials Setup
1. Open Secrets page.
2. Create or edit credential reference metadata.
3. Validate file/env availability.
4. Link ref to provider profile.
5. Re-validate provider profile.

## 5. Dataset Import
1. Open Datasets page.
2. Start import flow (folder or manifest path).
3. Set dataset id and optional profile.
4. Run import/register.
5. Inspect dataset detail and sample preview.

## 6. Benchmark Run
1. Open Benchmark page.
2. Use step builder: dataset -> providers -> scenario -> metrics -> review.
3. Validate dependencies.
4. Start run.
5. Track progress and state.
6. Open result detail when completed.

## 7. Compare Results
1. Open Results page.
2. Select two or more run IDs.
3. Compare metrics in table.
4. Export JSON/CSV/Markdown summary.

## 8. Diagnostics and Recovery
1. Open Logs & Diagnostics page.
2. Review issue feed (missing creds/profile errors/provider unavailable).
3. Follow suggested fix.
4. Re-run validation action from relevant page.
