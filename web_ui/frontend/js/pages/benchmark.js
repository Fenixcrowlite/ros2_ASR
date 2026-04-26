// Benchmark page controller for the browser UI.
const TIER_SCORE = {
  low: 1,
  medium: 2,
  high: 3,
  very_high: 4,
  local: 1,
  unknown: 0,
};

// Benchmark page is a draft builder for one benchmark run. Most helpers below
// exist to keep the visible form, the review JSON, and the final request
// payload in sync.
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
  const researchSummaryRoot = document.getElementById('benchmarkResearchSummary');
  const qualityResourceRoot = document.getElementById('benchmarkQualityResourceView');
  const audioPreviewRoot = document.getElementById('benchmarkAudioPreview');
  const noiseLevelsRoot = document.getElementById('benchmarkNoiseLevels');
  const customNoiseSNRInput = document.getElementById('benchmarkCustomNoiseSnr');
  const scenarioSelect = document.getElementById('benchmarkScenario');
  const noiseModeSelect = document.getElementById('benchmarkNoiseMode');
  const noiseModeHint = document.getElementById('benchmarkNoiseModeHint');
  const executionModeSelect = document.getElementById('benchmarkExecutionMode');
  const streamingChunkInput = document.getElementById('benchmarkStreamingChunkMs');

  let providerProfiles = [];
  let datasetPreviewState = {
    datasetProfile: '',
    datasetId: '',
    sampleCount: 0,
    samples: [],
    error: '',
  };
  // The backend owns the real catalog. The inline copy is only a bootstrap
  // fallback so the page still renders sensible controls before the fetch
  // completes or if the catalog endpoint is temporarily unavailable.
  let noiseCatalog = {
    levels: [
      { id: 'clean', snr_db: null, description: 'Reference baseline without synthetic corruption.' },
      { id: 'light', snr_db: 30, description: 'Mild additive noise.' },
      { id: 'medium', snr_db: 20, description: 'Moderate additive noise.' },
      { id: 'heavy', snr_db: 10, description: 'Strong additive noise.' },
      { id: 'extreme', snr_db: 0, description: 'Speech and noise at similar energy.' },
    ],
    modes: [
      { id: 'white', description: 'Broadband Gaussian baseline used for additive SNR sweeps.' },
      { id: 'pink', description: '1/f-shaped ambient-style noise.' },
      { id: 'brown', description: 'Low-frequency-heavy rumble.' },
      { id: 'babble', description: 'Speech-like multi-speaker interference.' },
      { id: 'hum', description: 'Tonal hum plus harmonics and hiss.' },
    ],
    scenario_defaults: {
      clean_baseline: { mode: 'white', levels: ['clean'] },
      noise_robustness: { mode: 'white', levels: ['clean', 'light', 'medium', 'heavy'] },
      provider_comparison: { mode: 'white', levels: ['clean'] },
      latency_profile: { mode: 'white', levels: ['clean'] },
    },
  };

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

  function parseCustomNoiseSNRLevels() {
    const merged = [];
    String(customNoiseSNRInput?.value || '')
      .split(',')
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item))
      .forEach((value) => {
        if (!merged.some((existing) => Math.abs(existing - value) < 0.0001)) {
          merged.push(value);
        }
      });
    return merged;
  }

  function formatSnrDb(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return 'n/a';
    }
    return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1).replace(/\.0$/, '');
  }

  function noiseModeMeta(modeId) {
    return (noiseCatalog.modes || []).find((item) => item.id === modeId) || null;
  }

  function noiseLevelMeta(levelId) {
    return (noiseCatalog.levels || []).find((item) => item.id === levelId) || null;
  }

  function scenarioNoiseDefaults() {
    return (
      noiseCatalog.scenario_defaults?.[scenarioSelect.value || 'clean_baseline'] ||
      noiseCatalog.scenario_defaults?.clean_baseline ||
      { mode: 'white', levels: ['clean'] }
    );
  }

  function effectiveNoiseLevels() {
    // Scenario defaults are only used when the operator has not explicitly
    // chosen levels. This keeps "noise_robustness" opinionated without
    // overriding user input.
    const selected = selectedNoiseLevels();
    if (selected.length) {
      return selected;
    }
    if (parseCustomNoiseSNRLevels().length) {
      return [];
    }
    return [...(scenarioNoiseDefaults().levels || ['clean'])];
  }

  function effectiveNoiseMode() {
    return noiseModeSelect.value || scenarioNoiseDefaults().mode || 'white';
  }

  function previewNoiseLevels() {
    const ordered = [];
    const add = (value) => {
      const normalized = String(value || '').trim().toLowerCase();
      if (!normalized || ordered.includes(normalized)) {
        return;
      }
      ordered.push(normalized);
    };
    add('clean');
    effectiveNoiseLevels().forEach(add);
    return ordered.filter((level) => level === 'clean' || noiseLevelMeta(level));
  }

  function previewDefaultDuration(sample = {}) {
    const value = Number(sample.duration_sec);
    if (!Number.isFinite(value) || value <= 0) {
      return '5.0';
    }
    return Math.max(0.5, Math.min(value, 5.0)).toFixed(1);
  }

  function previewSeed() {
    try {
      const advanced = safeJson(document.getElementById('benchmarkSettingsEditor').value);
      const seed = Number(advanced?.noise?.seed);
      return Number.isInteger(seed) ? seed : 1337;
    } catch (_error) {
      return 1337;
    }
  }

  async function loadAudioBlobIntoPlayer(player, url, { statusNode, loadingText, readyText }) {
    if (!player) {
      return;
    }
    if (statusNode) {
      statusNode.textContent = loadingText;
    }
    const previousUrl = player.dataset.objectUrl || '';
    if (previousUrl) {
      URL.revokeObjectURL(previousUrl);
      delete player.dataset.objectUrl;
    }

    try {
      const response = await fetch(url, { cache: 'no-store' });
      if (!response.ok) {
        let detail = `${response.status} ${response.statusText}`;
        try {
          const payload = await response.json();
          detail = payload?.detail || payload?.message || detail;
        } catch (_error) {
          // leave fallback text
        }
        if (response.status === 404 && String(detail).trim() === 'Not Found') {
          detail =
            'Preview endpoint is unavailable in the running gateway. Restart the web UI/gateway to load the latest API.';
        }
        throw new Error(detail);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      player.dataset.objectUrl = objectUrl;
      player.src = objectUrl;
      player.load();
      if (statusNode) {
        statusNode.textContent = readyText;
      }
    } catch (error) {
      player.removeAttribute('src');
      player.load();
      if (statusNode) {
        statusNode.textContent = error.message;
      }
    }
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

  function renderNoiseModeOptions(selected = '') {
    const values = (noiseCatalog.modes || []).map((item) => item.id);
    const current = selected || noiseModeSelect.value || scenarioNoiseDefaults().mode || values[0] || 'white';
    noiseModeSelect.innerHTML = values
      .map((item) => `<option value="${ui.escapeHtml(item)}">${ui.escapeHtml(item)}</option>`)
      .join('');
    if (values.includes(current)) {
      noiseModeSelect.value = current;
    }
    renderNoiseModeHint();
  }

  function renderNoiseModeHint() {
    if (!noiseModeHint) {
      return;
    }
    const mode = noiseModeMeta(effectiveNoiseMode());
    const defaults = scenarioNoiseDefaults();
    const recommended = (defaults.levels || []).join(', ');
    const prefix =
      (scenarioSelect.value || 'clean_baseline') === 'noise_robustness'
        ? `Recommended levels: ${recommended}. `
        : 'Clean-only preset unless you enable noisy levels. ';
    noiseModeHint.textContent = `${prefix}${mode?.description || 'Noise mode is applied to every non-clean variant.'}`.trim();
  }

  function bindNoiseLevelListeners() {
    noiseLevelsRoot.querySelectorAll('input').forEach((input) => {
      input.addEventListener('change', () => {
        renderBenchmarkAudioPreview();
        renderReview();
      });
    });
  }

  function renderNoiseLevels(defaultSelection = []) {
    noiseLevelsRoot.innerHTML = (noiseCatalog.levels || [])
      .map((item) => {
        const checked = defaultSelection.includes(item.id);
        const snrLabel = item.snr_db == null ? 'clean' : `${item.snr_db} dB`;
        return `
          <label title="${ui.escapeHtml(item.description || '')}">
            <input type="checkbox" value="${ui.escapeHtml(item.id)}" ${checked ? 'checked' : ''} />
            ${ui.escapeHtml(item.id)} <span class="muted">(${ui.escapeHtml(String(snrLabel))})</span>
          </label>
        `;
      })
      .join('');
    bindNoiseLevelListeners();
  }

  function applyScenarioNoisePreset() {
    const defaults = scenarioNoiseDefaults();
    renderNoiseModeOptions(defaults.mode || 'white');
    renderNoiseLevels(defaults.levels || ['clean']);
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

  function experimentVariantsCount() {
    return Math.max(1, effectiveNoiseLevels().length + parseCustomNoiseSNRLevels().length);
  }

  function reviewWarnings() {
    const warnings = [];
    if (!selectedProviders().length) {
      warnings.push('Select at least one provider profile before running benchmark.');
    }
    if ((executionModeSelect.value || 'batch') === 'streaming') {
      const incompatible = incompatibleStreamingProviders();
      if (incompatible.length) {
        warnings.push(`Streaming benchmark mode requires streaming-capable providers: ${incompatible.join(', ')}`);
      }
    }
    if ((scenarioSelect.value || 'clean_baseline') === 'noise_robustness' && experimentVariantsCount() <= 1) {
      warnings.push('Noise robustness scenario is selected, but only one effective noise variant is configured.');
    }
    if (datasetPreviewState.error) {
      warnings.push(`Dataset preview failed: ${datasetPreviewState.error}`);
    }
    return warnings;
  }

  function renderResearchSummary(summary = null) {
    if (!researchSummaryRoot) {
      return;
    }
    researchSummaryRoot.innerHTML = ui.statCards([
      {
        label: 'Dataset Samples',
        value: String(summary?.total_samples ?? datasetPreviewState.sampleCount ?? 0),
        badge: datasetProfileSelect.value || 'none',
        tone: datasetProfileSelect.value ? 'ok' : 'warning',
        hint: 'Samples in scope for this draft or latest result',
      },
      {
        label: 'Providers',
        value: String(summary?.provider_summaries?.length || selectedProviders().length),
        badge: scenarioSelect.value || 'clean_baseline',
        tone: selectedProviders().length ? 'ok' : 'warning',
        hint: 'Primary provider comparison axis',
      },
      {
        label: 'Noise Variants',
        value: String(summary?.noise_levels?.length || experimentVariantsCount()),
        badge: effectiveNoiseMode(),
        tone: experimentVariantsCount() > 1 ? 'info' : 'warning',
        hint: 'Distinct clean/noise variants in the current design',
      },
      {
        label: 'Metric Profiles',
        value: String(selectedMetricProfiles().length),
        badge: executionModeSelect.value || 'batch',
        tone: selectedMetricProfiles().length ? 'ok' : 'warning',
        hint: 'Metrics and execution mode driving the run',
      },
    ]);
  }

  function renderReview() {
    // The review box is the easiest way to verify what will actually be sent to
    // the gateway after defaults, UI selections, and advanced JSON are merged.
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
    const warnings = reviewWarnings();
    const providers = selectedProviders();
    const effectiveLevels = effectiveNoiseLevels();
    const customLevels = parseCustomNoiseSNRLevels();
    const datasetSamples = datasetPreviewState.sampleCount || 0;
    const matrixSize = datasetSamples * Math.max(1, providers.length) * Math.max(1, experimentVariantsCount());
    renderResearchSummary();
    reviewRoot.innerHTML = `
      ${ui.statCards([
        {
          label: 'Scenario',
          value: scenarioSelect.value || 'clean_baseline',
          badge: executionModeSelect.value || 'batch',
          tone: 'info',
          hint: 'Experiment posture',
        },
        {
          label: 'Comparison Axes',
          value: `${providers.length || 0} provider(s) x ${experimentVariantsCount()} variant(s)`,
          badge: `${selectedMetricProfiles().length} metric profile(s)`,
          tone: providers.length ? 'ok' : 'warning',
          hint: 'Provider/noise span of the current draft',
        },
        {
          label: 'Estimated Matrix',
          value: String(matrixSize || 0),
          badge: benchmarkProfileSelect.value || 'default_benchmark',
          tone: matrixSize ? 'ok' : 'warning',
          hint: 'Sample x provider x variant combinations',
        },
      ])}
      <div class="stack-item">
        <strong>Resolved comparison design</strong>
        <p>providers=${ui.escapeHtml(providers.join(', ') || 'none')}</p>
        <p>noise=${ui.escapeHtml(`${effectiveNoiseMode()} :: ${effectiveLevels.join(', ') || 'clean'}${customLevels.length ? ` + custom(${customLevels.join(', ')})` : ''}`)}</p>
        <p>metrics=${ui.escapeHtml(selectedMetricProfiles().join(', ') || 'benchmark defaults')}</p>
      </div>
      ${
        warnings.length
          ? `
            <div class="stack-item">
              <strong>Warnings</strong>
              ${warnings.map((warning) => `<p>${ui.escapeHtml(warning)}</p>`).join('')}
            </div>
          `
          : `
            <div class="stack-item">
              <strong>Validation signal</strong>
              <p>No blocking warnings detected for the current benchmark draft.</p>
            </div>
          `
      }
      ${
        advancedSettingsError || providerOverridesError
          ? `
            <div class="stack-item">
              <strong>Draft errors</strong>
              ${advancedSettingsError ? `<p>${ui.escapeHtml(advancedSettingsError)}</p>` : ''}
              ${providerOverridesError ? `<p>${ui.escapeHtml(providerOverridesError)}</p>` : ''}
            </div>
          `
          : ''
      }
      <div class="stack-item">
        <strong>Resolved request preview</strong>
        <pre class="metric-details__code">${ui.escapeHtml(
          JSON.stringify(
            {
              benchmark_profile: benchmarkProfileSelect.value,
              dataset_profile: datasetProfileSelect.value,
              providers,
              provider_overrides: providerOverrides,
              provider_overrides_error: providerOverridesError,
              scenario: scenarioSelect.value,
              execution_mode: executionModeSelect.value,
              noise: {
                mode: effectiveNoiseMode(),
                levels: effectiveLevels,
                custom_snr_db: customLevels,
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
          )
        )}</pre>
      </div>
    `;
  }

  function renderBenchmarkAudioPreview() {
    if (!audioPreviewRoot) {
      return;
    }
    if (!datasetProfileSelect.value) {
      audioPreviewRoot.innerHTML = ui.renderEmpty('Select a dataset profile to audition benchmark samples.');
      return;
    }
    if (datasetPreviewState.error) {
      audioPreviewRoot.innerHTML = ui.renderEmpty(`Failed to load dataset preview: ${datasetPreviewState.error}`);
      return;
    }
    if (!datasetPreviewState.samples.length) {
      audioPreviewRoot.innerHTML = ui.renderEmpty('No dataset preview samples available. Builder preview currently uses the first 25 manifest rows.');
      return;
    }

    const currentSampleId = audioPreviewRoot.querySelector('[data-benchmark-preview-sample]')?.value || '';
    const currentNoiseLevel = audioPreviewRoot.querySelector('[data-benchmark-preview-level]')?.value || '';
    const currentStartSec = audioPreviewRoot.querySelector('[data-benchmark-preview-start]')?.value || '0.0';
    const currentDurationSec = audioPreviewRoot.querySelector('[data-benchmark-preview-duration]')?.value || '';
    const currentCustomSnr = audioPreviewRoot.querySelector('[data-benchmark-preview-snr]')?.value || '';
    const sample =
      datasetPreviewState.samples.find((item) => item.sample_id === currentSampleId) ||
      datasetPreviewState.samples[0];
    const previewLevels = previewNoiseLevels();
    const configuredCustomSnr = parseCustomNoiseSNRLevels();
    const previewVariants = [...previewLevels, 'custom'].filter(
      (level, index, values) => level && values.indexOf(level) === index
    );
    const fallbackLevel = configuredCustomSnr.length ? 'custom' : previewLevels[0] || 'clean';
    const selectedLevel =
      previewVariants.find((level) => level === currentNoiseLevel) ||
      fallbackLevel ||
      'clean';
    const durationValue = currentDurationSec || previewDefaultDuration(sample);
    const levelMeta = noiseLevelMeta(selectedLevel);
    const mode = selectedLevel === 'clean' ? 'none' : effectiveNoiseMode();
    const customSnrValue =
      currentCustomSnr ||
      (configuredCustomSnr.length ? formatSnrDb(configuredCustomSnr[0]) : '15');
    const customSnrNumber = Number(customSnrValue);
    const previewLabel =
      selectedLevel === 'clean'
        ? 'clean source'
        : selectedLevel === 'custom'
          ? `custom ${Number.isFinite(customSnrNumber) ? `${formatSnrDb(customSnrNumber)} dB` : 'SNR'} via ${mode} noise`
          : `${selectedLevel} via ${mode} noise${levelMeta?.snr_db == null ? '' : ` (${levelMeta.snr_db} dB)`}`;

    audioPreviewRoot.innerHTML = `
      <div class="stack-item benchmark-preview-card">
        <strong>Audition Dataset Sample</strong>
        <p class="helper">
          Listen to the clean source or a noise-augmented preview before you launch the benchmark.
          Preview uses the current scenario noise mode and the selected preview level.
        </p>
        <div class="benchmark-preview-grid">
          <label>
            Sample
            <select data-benchmark-preview-sample>
              ${datasetPreviewState.samples
                .map(
                  (item) => `
                    <option value="${ui.escapeHtml(item.sample_id)}"${item.sample_id === sample.sample_id ? ' selected' : ''}>
                      ${ui.escapeHtml(item.sample_id)}
                    </option>
                  `
                )
                .join('')}
            </select>
          </label>
          <label>
            Preview level
            <select data-benchmark-preview-level>
              ${previewLevels
                .map((level) => {
                  const meta = noiseLevelMeta(level);
                  const label =
                    level === 'clean'
                      ? 'clean'
                      : `${level}${meta?.snr_db == null ? '' : ` (${meta.snr_db} dB)`}`;
                  return `<option value="${ui.escapeHtml(level)}"${level === selectedLevel ? ' selected' : ''}>${ui.escapeHtml(label)}</option>`;
                })
                .concat(
                  `<option value="custom"${selectedLevel === 'custom' ? ' selected' : ''}>custom (manual SNR)</option>`
                )
                .join('')}
            </select>
          </label>
          <label>
            Start sec
            <input data-benchmark-preview-start type="number" min="0" step="0.1" value="${ui.escapeHtml(currentStartSec)}" />
          </label>
          <label>
            Duration sec
            <input data-benchmark-preview-duration type="number" min="0.1" max="120" step="0.1" value="${ui.escapeHtml(durationValue)}" />
          </label>
          <label>
            Manual SNR dB
            <input
              data-benchmark-preview-snr
              type="number"
              min="-5"
              max="60"
              step="0.1"
              value="${ui.escapeHtml(customSnrValue)}"
              ${selectedLevel === 'custom' ? '' : 'disabled'}
            />
            <span class="field-note">Used only when preview level is <code>custom</code>.</span>
          </label>
        </div>
        <div class="benchmark-preview-meta">
          <div class="stack-item compact">
            <strong>${ui.escapeHtml(sample.sample_id || 'sample')}</strong>
            <p>${ui.escapeHtml(sample.transcript || '')}</p>
            <p class="muted">language=${ui.escapeHtml(sample.language || 'n/a')} split=${ui.escapeHtml(sample.split || 'n/a')} duration=${ui.escapeHtml(String(sample.duration_sec ?? 'n/a'))}s</p>
          </div>
          <div class="stack-item compact">
            <strong>Active Preview Variant</strong>
            <p>${ui.escapeHtml(previewLabel)}</p>
            <p class="muted">dataset_profile=${ui.escapeHtml(datasetProfileSelect.value)} sample_count=${ui.escapeHtml(String(datasetPreviewState.sampleCount || datasetPreviewState.samples.length))}</p>
          </div>
        </div>
        <div class="actions-row">
          <button type="button" class="btn-secondary" data-benchmark-preview-load>Load Preview</button>
        </div>
        <audio class="benchmark-preview-player" controls preload="none"></audio>
        <p class="helper benchmark-preview-status">Preview is generated on demand from the selected sample.</p>
      </div>
    `;

    audioPreviewRoot.querySelector('[data-benchmark-preview-sample]')?.addEventListener('change', () => {
      renderBenchmarkAudioPreview();
    });
    audioPreviewRoot.querySelector('[data-benchmark-preview-level]')?.addEventListener('change', () => {
      renderBenchmarkAudioPreview();
    });

    audioPreviewRoot.querySelector('[data-benchmark-preview-load]')?.addEventListener('click', () => {
      const sampleId = audioPreviewRoot.querySelector('[data-benchmark-preview-sample]')?.value || sample.sample_id;
      const noiseLevel = audioPreviewRoot.querySelector('[data-benchmark-preview-level]')?.value || 'clean';
      const startSec = audioPreviewRoot.querySelector('[data-benchmark-preview-start]')?.value || '0.0';
      const durationSec = audioPreviewRoot.querySelector('[data-benchmark-preview-duration]')?.value || previewDefaultDuration(sample);
      const customSnr = Number(audioPreviewRoot.querySelector('[data-benchmark-preview-snr]')?.value || '');
      const player = audioPreviewRoot.querySelector('.benchmark-preview-player');
      const status = audioPreviewRoot.querySelector('.benchmark-preview-status');
      if (!player || !status) {
        return;
      }
      if (noiseLevel === 'custom' && !Number.isFinite(customSnr)) {
        status.textContent = 'Enter a numeric SNR dB for custom preview.';
        return;
      }
      void loadAudioBlobIntoPlayer(
        player,
        api.benchmarkPreviewAudioUrl({
          dataset_profile: datasetProfileSelect.value,
          sample_id: sampleId,
          start_sec: startSec,
          duration_sec: durationSec,
          noise_level: noiseLevel,
          noise_mode: noiseLevel === 'clean' ? null : effectiveNoiseMode(),
          snr_db: noiseLevel === 'custom' ? customSnr : null,
          seed: previewSeed(),
        }),
        {
          statusNode: status,
          loadingText: 'Loading benchmark preview clip...',
          readyText:
            noiseLevel === 'clean'
              ? 'Preview ready: clean source'
              : noiseLevel === 'custom'
                ? `Preview ready: custom ${formatSnrDb(customSnr)} dB via ${effectiveNoiseMode()}`
                : `Preview ready: ${noiseLevel} via ${effectiveNoiseMode()}`,
        }
      );
    });
  }

  async function loadDatasetPreview() {
    if (!audioPreviewRoot) {
      return;
    }
    const datasetProfile = datasetProfileSelect.value || '';
    if (!datasetProfile) {
      datasetPreviewState = {
        datasetProfile: '',
        datasetId: '',
        sampleCount: 0,
        samples: [],
        error: '',
      };
      renderBenchmarkAudioPreview();
      return;
    }

    audioPreviewRoot.innerHTML = ui.renderEmpty('Loading dataset sample preview...');
    try {
      const profile = await api.profileDetail('datasets', datasetProfile);
      const datasetId = profile?.payload?.dataset_id || datasetProfile;
      const detail = await api.datasetDetail(datasetId);
      datasetPreviewState = {
        datasetProfile,
        datasetId,
        sampleCount: Number(detail.sample_count || 0),
        samples: Array.isArray(detail.preview) ? detail.preview : [],
        error: '',
      };
    } catch (error) {
      datasetPreviewState = {
        datasetProfile,
        datasetId: '',
        sampleCount: 0,
        samples: [],
        error: error.message,
      };
    }
    renderBenchmarkAudioPreview();
  }

  async function loadOptions() {
    const [benchmarkProfiles, datasetProfiles, metricsProfiles, providerProfilesResp, fetchedNoiseCatalog] = await Promise.all([
      api.profilesByType('benchmark'),
      api.profilesByType('datasets'),
      api.profilesByType('metrics'),
      api.providersProfiles(),
      api.noiseCatalog().catch(() => noiseCatalog),
    ]);

    ui.updateSelectOptions(benchmarkProfileSelect, benchmarkProfiles.profiles || [], 'default_benchmark');
    ui.updateSelectOptions(datasetProfileSelect, datasetProfiles.profiles || [], 'sample_dataset');

    providerProfiles = providerProfilesResp.profiles || [];
    noiseCatalog = fetchedNoiseCatalog || noiseCatalog;
    renderChecks(
      providersChecksRoot,
      providerProfiles.map((item) => item.provider_profile),
      providerProfiles.length ? [providerProfiles[0].provider_profile] : []
    );
    renderChecks(metricsChecksRoot, metricsProfiles.profiles || [], []);
    applyScenarioNoisePreset();
    renderProviderTuning();
    await loadDatasetPreview();
    renderResearchSummary();
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
  }

  function benchmarkSettingsPayload() {
    const advanced = safeJson(document.getElementById('benchmarkSettingsEditor').value);
    return {
      ...advanced,
      execution_mode: executionModeSelect.value || 'batch',
      noise: {
        ...(advanced.noise || {}),
        mode: effectiveNoiseMode(),
        levels: effectiveNoiseLevels(),
        custom_snr_db: parseCustomNoiseSNRLevels(),
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
      scenario: scenarioSelect.value,
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
      renderResearchSummary();
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
          renderResearchSummary(summary);
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
      ],
      { className: 'table--compact', stickyFirstColumn: true }
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
          state.results.selectedRunId = runId;
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
      await loadDatasetPreview();
      renderReview();
      ui.toast(`Uploaded dataset ready: ${payload.dataset_profile}`, 'success');
    } catch (error) {
      reviewRoot.innerHTML = `<div class="stack-item"><strong>Upload failed</strong><p>${ui.escapeHtml(error.message)}</p></div>`;
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
  datasetProfileSelect.addEventListener('change', async () => {
    await loadDatasetPreview();
    renderReview();
  });
  scenarioSelect.addEventListener('change', () => {
    applyScenarioNoisePreset();
    renderBenchmarkAudioPreview();
    renderReview();
  });
  noiseModeSelect.addEventListener('change', () => {
    renderNoiseModeHint();
    renderBenchmarkAudioPreview();
    renderReview();
  });
  customNoiseSNRInput?.addEventListener('input', () => {
    renderBenchmarkAudioPreview();
    renderReview();
  });
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
