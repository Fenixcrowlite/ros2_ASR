const TIER_SCORE = {
  low: 1,
  medium: 2,
  high: 3,
  very_high: 4,
  local: 1,
  unknown: 0,
};

function safeJson(raw) {
  const text = String(raw || '').trim();
  if (!text) {
    return {};
  }
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('Advanced benchmark/provider settings must be a JSON object');
  }
  return parsed;
}

function scoreBar(label, tier, score, ui) {
  const width = Math.max(6, Math.min(100, (score / 4) * 100));
  return `
    <div class="metric-bar">
      <div class="metric-bar__head">
        <span>${ui.escapeHtml(label)}</span>
        <code>${ui.escapeHtml(tier || 'n/a')}</code>
      </div>
      <div class="metric-bar__track">
        <span class="metric-bar__fill higher" style="width:${width}%"></span>
      </div>
    </div>
  `;
}

export function initBenchmarkPage(ctx) {
  const { api, ui, state, navigate } = ctx;

  const benchmarkProfileSelect = document.getElementById('benchmarkProfileSelect');
  const datasetProfileSelect = document.getElementById('benchmarkDatasetProfile');
  const providersChecksRoot = document.getElementById('benchmarkProviderChecks');
  const providerTuningRoot = document.getElementById('benchmarkProviderTuning');
  const metricsChecksRoot = document.getElementById('benchmarkMetricChecks');
  const historyRoot = document.getElementById('benchmarkHistoryTable');
  const activeRunRoot = document.getElementById('benchmarkActiveRun');
  const reviewRoot = document.getElementById('benchmarkReview');
  const qualityResourceRoot = document.getElementById('benchmarkQualityResourceView');
  const noiseLevelsRoot = document.getElementById('benchmarkNoiseLevels');
  const executionModeSelect = document.getElementById('benchmarkExecutionMode');
  const streamingChunkInput = document.getElementById('benchmarkStreamingChunkMs');

  let providerProfiles = [];
  function fmtMetric(value) {
    if (value == null || value === '') {
      return '—';
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return ui.escapeHtml(String(value));
    }
    if (Number.isInteger(numeric)) {
      return ui.escapeHtml(String(numeric));
    }
    return ui.escapeHtml(numeric.toFixed(4));
  }

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

  function selectedNoiseLevels() {
    return Array.from(noiseLevelsRoot.querySelectorAll('input[type="checkbox"]:checked')).map((item) => item.value);
  }

  function incompatibleStreamingProviders() {
    return selectedProviders().filter((providerProfile) => !providerRow(providerProfile)?.capabilities?.supports_streaming);
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

  function providerRow(providerProfile) {
    return providerProfiles.find((item) => `providers/${item.provider_profile}` === providerProfile || item.provider_profile === providerProfile) || null;
  }

  function renderProviderSummaries(summary = {}) {
    const providerSummaries = summary.provider_summaries || [];
    if (!providerSummaries.length) {
      return ui.renderEmpty('Per-provider metrics will appear after a completed run with stored provider summaries.');
    }
    return ui.table(
      [
        {
          key: 'provider',
          label: 'Provider',
          value: (row) => `${ui.escapeHtml(row.provider_profile || row.provider_id || row.provider_key || 'unknown')}${row.legacy_metrics ? ' <span class="badge badge-warning">Legacy semantics</span>' : ''}`,
        },
        {
          key: 'preset',
          label: 'Preset',
          value: (row) => ui.escapeHtml(row.provider_preset || 'default'),
        },
        { key: 'samples', label: 'Samples', value: (row) => fmtMetric(row.total_samples) },
        { key: 'success', label: 'Success', value: (row) => fmtMetric(row.successful_samples) },
        { key: 'failed', label: 'Failed', value: (row) => fmtMetric(row.failed_samples) },
        { key: 'wer', label: 'WER', value: (row) => fmtMetric(row.quality_metrics?.wer) },
        { key: 'cer', label: 'CER', value: (row) => fmtMetric(row.quality_metrics?.cer) },
        { key: 'acc', label: 'Exact Match Rate', value: (row) => fmtMetric(row.quality_metrics?.sample_accuracy) },
        { key: 'lat', label: 'End-to-end ms', value: (row) => fmtMetric(row.latency_metrics?.end_to_end_latency_ms) },
        { key: 'rtf', label: 'End-to-end RTF', value: (row) => fmtMetric(row.latency_metrics?.end_to_end_rtf) },
        { key: 'succ_rate', label: 'Success Rate', value: (row) => fmtMetric(row.reliability_metrics?.success_rate) },
        { key: 'fail_rate', label: 'Failure Rate', value: (row) => fmtMetric(row.reliability_metrics?.failure_rate) },
        { key: 'cost_mean', label: 'Mean Cost USD', value: (row) => fmtMetric(row.cost_metrics?.estimated_cost_usd) },
        {
          key: 'cost_total',
          label: 'Total Cost USD',
          value: (row) => fmtMetric(row.metric_statistics?.estimated_cost_usd?.sum),
        },
      ],
      providerSummaries
    );
  }

  function renderProviderTuning() {
    const selected = selectedProviders();
    if (!selected.length) {
      providerTuningRoot.innerHTML = ui.renderEmpty('Select at least one provider to configure model presets and advanced execution settings.');
      renderQualityResourceView();
      return;
    }
    providerTuningRoot.innerHTML = selected
      .map((providerProfile) => {
        const row = providerRow(providerProfile);
        const presets = row?.model_presets || [];
        const presetOptions = presets.length
          ? presets
              .map(
                (preset) => `<option value="${ui.escapeHtml(preset.preset_id)}" ${preset.preset_id === row.default_preset ? 'selected' : ''}>${ui.escapeHtml(preset.label)}</option>`
              )
              .join('')
          : '<option value="">default</option>';
        return `
          <div class="stack-item provider-tuning-card" data-provider-card="${ui.escapeHtml(providerProfile)}">
            <strong>${ui.escapeHtml(providerProfile)}</strong>
            <label>
              Model / preset
              <select data-provider-preset="${ui.escapeHtml(providerProfile)}">${presetOptions}</select>
            </label>
            <label>
              Advanced provider settings JSON
              <textarea class="code-area" data-provider-settings="${ui.escapeHtml(providerProfile)}" placeholder='{"temperature":0.2}'></textarea>
            </label>
            <div data-provider-preset-meta="${ui.escapeHtml(providerProfile)}"></div>
          </div>
        `;
      })
      .join('');

    providerTuningRoot.querySelectorAll('select[data-provider-preset]').forEach((select) => {
      select.addEventListener('change', () => {
        renderProviderPresetMeta(select.getAttribute('data-provider-preset'));
        renderQualityResourceView();
      });
    });
    providerTuningRoot.querySelectorAll('textarea[data-provider-settings]').forEach((textarea) => {
      textarea.addEventListener('input', () => renderQualityResourceView());
    });
    selected.forEach((profile) => renderProviderPresetMeta(profile));
    renderQualityResourceView();
  }

  function renderProviderPresetMeta(providerProfile) {
    const row = providerRow(providerProfile);
    const target = providerTuningRoot.querySelector(`[data-provider-preset-meta="${providerProfile}"]`);
    const presetSelect = providerTuningRoot.querySelector(`[data-provider-preset="${providerProfile}"]`);
    if (!row || !target || !presetSelect) {
      return;
    }
    const preset = (row.model_presets || []).find((item) => item.preset_id === presetSelect.value) || row.execution_preview?.preset || null;
    target.innerHTML = `
      <div class="stack-item compact">
        <p>${ui.escapeHtml(preset?.description || 'Default provider execution.')}</p>
        <p class="muted">quality=${ui.escapeHtml(preset?.quality_tier || 'n/a')} resource=${ui.escapeHtml(preset?.resource_tier || 'n/a')} cost=${ui.escapeHtml(preset?.estimated_cost_tier || 'n/a')}</p>
      </div>
    `;
  }

  function collectProviderOverrides() {
    const overrides = {};
    selectedProviders().forEach((providerProfile) => {
      const presetSelect = providerTuningRoot.querySelector(`[data-provider-preset="${providerProfile}"]`);
      const settingsEditor = providerTuningRoot.querySelector(`[data-provider-settings="${providerProfile}"]`);
      overrides[providerProfile] = {
        preset_id: presetSelect?.value || '',
        settings: safeJson(settingsEditor?.value || ''),
      };
    });
    return overrides;
  }

  function renderQualityResourceView(summary = null) {
    if (summary) {
      qualityResourceRoot.innerHTML = `
        <div class="stack-item">
          <strong>Per-provider metrics</strong>
          <p class="helper">Rows are provider-specific. Mixed aggregate is intentionally hidden.</p>
          ${renderProviderSummaries(summary)}
        </div>
      `;
      return;
    }

    const selected = selectedProviders();
    if (!selected.length) {
      qualityResourceRoot.innerHTML = ui.renderEmpty('Quality/resource view will appear when you select providers and presets.');
      return;
    }
    qualityResourceRoot.innerHTML = selected
      .map((providerProfile) => {
        const row = providerRow(providerProfile);
        const presetSelect = providerTuningRoot.querySelector(`[data-provider-preset="${providerProfile}"]`);
        const preset = (row?.model_presets || []).find((item) => item.preset_id === presetSelect?.value) || row?.execution_preview?.preset || {};
        const qualityTier = preset.quality_tier || 'balanced';
        const resourceTier = preset.resource_tier || 'medium';
        const costTier = preset.estimated_cost_tier || 'unknown';
        return `
          <div class="stack-item">
            <strong>${ui.escapeHtml(providerProfile)}</strong>
            ${scoreBar('Quality tier', qualityTier, TIER_SCORE[qualityTier] || 2, ui)}
            ${scoreBar('Resource tier', resourceTier, TIER_SCORE[resourceTier] || 2, ui)}
            ${scoreBar('Cost tier', costTier, TIER_SCORE[costTier] || (costTier === 'high' ? 3 : 1), ui)}
          </div>
        `;
      })
      .join('');
  }

  function renderReview() {
    let advancedSettings = {};
    let advancedSettingsError = '';
    try {
      advancedSettings = safeJson(document.getElementById('benchmarkSettingsEditor').value);
    } catch (error) {
      advancedSettingsError = error.message;
    }
    let providerOverrides = {};
    let providerOverridesError = '';
    try {
      providerOverrides = collectProviderOverrides();
    } catch (error) {
      providerOverridesError = error.message;
    }
    reviewRoot.textContent = JSON.stringify(
      {
        benchmark_profile: benchmarkProfileSelect.value,
        dataset_profile: datasetProfileSelect.value,
        providers: selectedProviders(),
        provider_overrides: providerOverrides,
        provider_overrides_error: providerOverridesError,
        scenario: document.getElementById('benchmarkScenario').value,
        execution_mode: executionModeSelect.value,
        noise: {
          mode: document.getElementById('benchmarkNoiseMode').value,
          levels: selectedNoiseLevels(),
        },
        streaming: {
          chunk_ms: Number(streamingChunkInput.value || 500),
        },
        metric_profiles: selectedMetricProfiles(),
        benchmark_settings: advancedSettings,
        benchmark_settings_error: advancedSettingsError,
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
      api.providersProfiles(),
    ]);

    ui.updateSelectOptions(benchmarkProfileSelect, benchmarkProfiles.profiles || [], 'default_benchmark');
    ui.updateSelectOptions(datasetProfileSelect, datasetProfiles.profiles || [], 'sample_dataset');

    providerProfiles = providerProfilesResp.profiles || [];
    renderChecks(
      providersChecksRoot,
      providerProfiles.map((item) => item.provider_profile),
      providerProfiles.length ? [providerProfiles[0].provider_profile] : []
    );
    renderChecks(metricsChecksRoot, metricsProfiles.profiles || [], []);
    renderChecks(noiseLevelsRoot, ['clean', 'light', 'medium', 'heavy', 'extreme'], ['clean']);
    renderProviderTuning();
    renderReview();

    providersChecksRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', () => {
        renderProviderTuning();
        renderReview();
      });
    });
    metricsChecksRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', renderReview);
    });
    noiseLevelsRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', renderReview);
    });
  }

  function benchmarkSettingsPayload() {
    const advanced = safeJson(document.getElementById('benchmarkSettingsEditor').value);
    return {
      ...advanced,
      execution_mode: executionModeSelect.value || 'batch',
      noise: {
        ...(advanced.noise || {}),
        mode: document.getElementById('benchmarkNoiseMode').value,
        levels: selectedNoiseLevels(),
      },
      streaming: {
        ...(advanced.streaming || {}),
        chunk_ms: Number(streamingChunkInput.value || 500),
      },
    };
  }

  async function runBenchmark() {
    const providers = selectedProviders();
    if (!providers.length) {
      throw new Error('Select at least one provider profile before running benchmark');
    }
    if ((executionModeSelect.value || 'batch') === 'streaming') {
      const incompatible = incompatibleStreamingProviders();
      if (incompatible.length) {
        throw new Error(
          `Streaming benchmark mode requires streaming-capable providers: ${incompatible.join(', ')}`
        );
      }
    }

    const runIdInput = document.getElementById('benchmarkRunId').value;

    const payload = await api.benchmarkRun({
      benchmark_profile: benchmarkProfileSelect.value,
      dataset_profile: datasetProfileSelect.value,
      providers,
      scenario: document.getElementById('benchmarkScenario').value,
      provider_overrides: collectProviderOverrides(),
      benchmark_settings: benchmarkSettingsPayload(),
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
      const summary = status.result?.summary || status.result || {};

      activeRunRoot.innerHTML = ui.renderKeyValueList([
        { key: 'Run ID', value: runId },
        { key: 'State', value: stateName },
        { key: 'Message', value: status.message || status.ros_status?.status_message || '' },
        { key: 'Execution Mode', value: summary.execution_mode || status.result?.execution_mode || 'n/a' },
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
        if (summary.provider_summaries) {
          renderQualityResourceView(summary);
        }
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
        { key: 'scenario', label: 'Scenario', value: (row) => ui.escapeHtml(row.scenario || '') },
        { key: 'execution_mode', label: 'Mode', value: (row) => ui.escapeHtml(row.execution_mode || 'batch') },
        { key: 'dataset_profile', label: 'Dataset', value: (row) => ui.escapeHtml(row.dataset_profile || '') },
        {
          key: 'providers',
          label: 'Providers',
          value: (row) => ui.escapeHtml((row.providers || []).join(', ')),
        },
        {
          key: 'provider_summaries',
          label: 'Per Provider',
          value: (row) =>
            ui.escapeHtml(
              (row.provider_summaries || [])
                .map((item) => {
                  const name = item.provider_profile || item.provider_id || item.provider_key || 'unknown';
                  const wer = item.quality_metrics?.wer;
                  const latency = item.latency_metrics?.end_to_end_latency_ms;
                  return `${name}: wer=${wer ?? 'n/a'}, latency=${latency ?? 'n/a'}`;
                })
                .join(' | ')
            ),
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

  document.getElementById('benchmarkUploadDatasetBtn')?.addEventListener('click', async () => {
    try {
      const files = Array.from(document.getElementById('benchmarkDatasetFiles').files || []);
      if (!files.length) {
        throw new Error('Select files or a folder first');
      }
      const payload = await api.datasetImportUpload({
        dataset_id: document.getElementById('benchmarkDatasetId').value,
        dataset_profile: document.getElementById('benchmarkDatasetId').value,
        language: document.getElementById('benchmarkDatasetLanguage').value,
        files,
      });
      await loadOptions();
      datasetProfileSelect.value = (payload.dataset_profile || '').replace(/^datasets\//, '');
      renderReview();
      ui.toast(`Uploaded dataset ready: ${payload.dataset_profile}`, 'success');
    } catch (error) {
      reviewRoot.textContent = error.message;
      ui.toast(`Dataset upload failed: ${error.message}`, 'error', 4500);
    }
  });

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
  document.getElementById('benchmarkNoiseMode').addEventListener('change', renderReview);
  executionModeSelect.addEventListener('change', renderReview);
  streamingChunkInput.addEventListener('input', renderReview);
  document.getElementById('benchmarkSettingsEditor').addEventListener('input', renderReview);

  return {
    refresh: async () => {
      await loadOptions();
      await refreshStatus();
      await refreshHistory();
    },
    poll: refreshStatus,
  };
}
