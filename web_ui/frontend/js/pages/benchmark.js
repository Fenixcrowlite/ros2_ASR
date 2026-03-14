export function initBenchmarkPage(ctx) {
  const { api, ui, state, navigate } = ctx;

  const benchmarkProfileSelect = document.getElementById('benchmarkProfileSelect');
  const datasetProfileSelect = document.getElementById('benchmarkDatasetProfile');
  const providersChecksRoot = document.getElementById('benchmarkProviderChecks');
  const metricsChecksRoot = document.getElementById('benchmarkMetricChecks');
  const historyRoot = document.getElementById('benchmarkHistoryTable');
  const activeRunRoot = document.getElementById('benchmarkActiveRun');
  const reviewRoot = document.getElementById('benchmarkReview');

  let providerProfiles = [];

  function selectedProviders() {
    return Array.from(providersChecksRoot.querySelectorAll('input[type="checkbox"]:checked')).map((item) =>
      item.value.startsWith('providers/') ? item.value : `providers/${item.value}`
    );
  }

  function selectedMetricProfiles() {
    return Array.from(metricsChecksRoot.querySelectorAll('input[type="checkbox"]:checked')).map((item) =>
      item.value.startsWith('metrics/') ? item.value : `metrics/${item.value}`
    );
  }

  function renderChecks(root, values, defaultSelection = []) {
    root.innerHTML = values
      .map((item) => {
        const checked = defaultSelection.includes(item);
        return `
          <label>
            <input type="checkbox" value="${ui.escapeHtml(item)}" ${checked ? 'checked' : ''} />
            ${ui.escapeHtml(item)}
          </label>
        `;
      })
      .join('');
  }

  function renderReview() {
    reviewRoot.textContent = JSON.stringify(
      {
        benchmark_profile: benchmarkProfileSelect.value,
        dataset_profile: datasetProfileSelect.value,
        providers: selectedProviders(),
        scenario: document.getElementById('benchmarkScenario').value,
        metric_profiles: selectedMetricProfiles(),
      },
      null,
      2
    );
  }

  async function loadOptions() {
    const [benchmarkProfiles, datasetProfiles, metricsProfiles, providerProfilesResp] = await Promise.all([
      api.profilesByType('benchmark'),
      api.profilesByType('datasets'),
      api.profilesByType('metrics'),
      api.profilesByType('providers'),
    ]);

    ui.updateSelectOptions(benchmarkProfileSelect, benchmarkProfiles.profiles || [], 'default_benchmark');
    ui.updateSelectOptions(datasetProfileSelect, datasetProfiles.profiles || [], 'sample_dataset');

    providerProfiles = providerProfilesResp.profiles || [];
    renderChecks(providersChecksRoot, providerProfiles, providerProfiles.length ? [providerProfiles[0]] : []);
    renderChecks(metricsChecksRoot, metricsProfiles.profiles || [], []);
    renderReview();

    providersChecksRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', renderReview);
    });
    metricsChecksRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', renderReview);
    });
  }

  async function runBenchmark() {
    const providers = selectedProviders();
    if (!providers.length) {
      throw new Error('Select at least one provider profile before running benchmark');
    }

    const runIdInput = document.getElementById('benchmarkRunId').value;

    const payload = await api.benchmarkRun({
      benchmark_profile: benchmarkProfileSelect.value,
      dataset_profile: datasetProfileSelect.value,
      providers,
      run_id: runIdInput,
    });
    state.benchmark.activeRunId = payload.run_id;
    ui.toast(`Benchmark queued: ${payload.run_id}`, 'success');
    await refreshStatus();
    await refreshHistory();
  }

  async function refreshStatus() {
    const runId = state.benchmark.activeRunId;
    if (!runId) {
      activeRunRoot.innerHTML = ui.renderEmpty('No active benchmark run. Build a run and start execution.');
      ui.patchPulse('benchmarkPulse', 'Benchmark: idle', 'idle');
      return;
    }

    try {
      const status = await api.benchmarkStatus(runId);
      const stateName = status.state || status.ros_status?.state || 'unknown';

      activeRunRoot.innerHTML = ui.renderKeyValueList([
        { key: 'Run ID', value: runId },
        { key: 'State', value: stateName },
        { key: 'Message', value: status.message || status.ros_status?.status_message || '' },
        { key: 'Started', value: status.started_at || '' },
        { key: 'Completed', value: status.completed_at || '' },
        {
          key: 'Progress',
          value: status.ros_status?.progress != null ? `${Math.round((status.ros_status.progress || 0) * 100)}%` : 'n/a',
        },
      ]);

      ui.patchPulse('benchmarkPulse', `Benchmark: ${stateName}`, stateName);

      if (['completed', 'failed'].includes(String(stateName).toLowerCase())) {
        await refreshHistory();
      }
    } catch (error) {
      activeRunRoot.innerHTML = ui.renderEmpty(`Failed to get benchmark status: ${error.message}`);
    }
  }

  async function refreshHistory() {
    const payload = await api.benchmarkHistory(30);
    const rows = payload.runs || [];
    state.benchmark.history = rows;

    if (!rows.length) {
      historyRoot.innerHTML = ui.renderEmpty('No benchmark runs yet.');
      return;
    }

    historyRoot.innerHTML = ui.table(
      [
        { key: 'run_id', label: 'Run ID', value: (row) => ui.toCode(row.run_id) },
        {
          key: 'state',
          label: 'State',
          value: (row) => `<span class="${ui.statusBadgeClass(row.state)}">${ui.escapeHtml(row.state)}</span>`,
        },
        { key: 'dataset_profile', label: 'Dataset', value: (row) => ui.escapeHtml(row.dataset_profile || '') },
        {
          key: 'providers',
          label: 'Providers',
          value: (row) => ui.escapeHtml((row.providers || []).join(', ')),
        },
        {
          key: 'mean_metrics',
          label: 'Mean Metrics',
          value: (row) => ui.escapeHtml(JSON.stringify(row.mean_metrics || {})),
        },
      ],
      rows,
      [
        { id: 'status', label: 'Status', rowKey: (row) => row.run_id },
        { id: 'open_results', label: 'Open Results', rowKey: (row) => row.run_id },
      ]
    );

    historyRoot.querySelectorAll('button[data-action]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const action = event.currentTarget.getAttribute('data-action');
        const runId = event.currentTarget.getAttribute('data-row');
        if (!runId) {
          return;
        }
        if (action === 'status') {
          state.benchmark.activeRunId = runId;
          await refreshStatus();
          return;
        }
        if (action === 'open_results') {
          document.getElementById('resultsRunSelect').value = runId;
          navigate('results');
        }
      });
    });
  }

  document.getElementById('benchmarkRunBtn')?.addEventListener('click', async () => {
    try {
      renderReview();
      await runBenchmark();
    } catch (error) {
      ui.toast(`Benchmark run failed: ${error.message}`, 'error', 4500);
      reviewRoot.textContent = error.message;
    }
  });

  benchmarkProfileSelect.addEventListener('change', renderReview);
  datasetProfileSelect.addEventListener('change', renderReview);
  document.getElementById('benchmarkScenario').addEventListener('change', renderReview);

  return {
    refresh: async () => {
      await loadOptions();
      await refreshStatus();
      await refreshHistory();
    },
    poll: refreshStatus,
  };
}
