// Runtime page controller for the browser UI.
import { createActionRunner } from '../action-runner.js';
import { renderProviderGuideHtml } from '../provider-guides.js';

export function initRuntimePage(ctx) {
  const { api, ui, state } = ctx;

  const runtimeProfileSelect = document.getElementById('runtimeProfileSelect');
  const runtimeProviderSelect = document.getElementById('runtimeProviderSelect');
  const runtimeProviderPresetSelect = document.getElementById('runtimeProviderPresetSelect');
  const runtimeProviderPresetMeta = document.getElementById('runtimeProviderPresetMeta');
  const runtimeProviderSettings = document.getElementById('runtimeProviderSettings');
  const sessionIdInput = document.getElementById('runtimeSessionId');
  const languageInput = document.getElementById('runtimeLanguage');
  const sourceModeSelect = document.getElementById('runtimeSourceMode');
  const processingModeSelect = document.getElementById('runtimeProcessingMode');
  const sampleSelect = document.getElementById('runtimeSampleSelect');
  const sampleDropzone = document.getElementById('runtimeSampleDropzone');
  const sampleBrowseButton = document.getElementById('runtimeSampleBrowseBtn');
  const sampleUploadInput = document.getElementById('runtimeSampleUploadInput');
  const sampleCatalogMeta = document.getElementById('runtimeSampleCatalogMeta');
  const noiseModeSelect = document.getElementById('runtimeNoiseMode');
  const noisePresetLevelsRoot = document.getElementById('runtimeNoisePresetLevels');
  const noiseLevelsInput = document.getElementById('runtimeNoiseLevels');
  const generateNoiseButton = document.getElementById('runtimeGenerateNoiseBtn');
  const statusRoot = document.getElementById('runtimeStatusSummary');
  const timelineRoot = document.getElementById('runtimeTimeline');
  const transcriptsRoot = document.getElementById('runtimeTranscripts');
  const startButton = document.getElementById('runtimeStartBtn');
  const reconfigureButton = document.getElementById('runtimeReconfigureBtn');
  const stopButton = document.getElementById('runtimeStopBtn');
  const recognizeButton = document.getElementById('runtimeRecognizeBtn');

  let selectorsLoaded = false;
  let requestInFlight = false;
  let providerProfiles = [];
  // Sample catalog is fetched from gateway because the browser cannot inspect
  // repository files or uploaded WAVs directly.
  let sampleCatalog = {
    samples: [],
    skipped: [],
    root: 'data/sample',
    upload_root: 'data/sample/uploads',
    default_sample: '',
    upload_enabled: true,
  };
  let noiseCatalog = {
    levels: [
      { id: 'clean', snr_db: null },
      { id: 'light', snr_db: 30 },
      { id: 'medium', snr_db: 20 },
      { id: 'heavy', snr_db: 10 },
      { id: 'extreme', snr_db: 0 },
    ],
    modes: [
      { id: 'white' },
      { id: 'pink' },
      { id: 'brown' },
      { id: 'babble' },
      { id: 'hum' },
    ],
  };

  function selectedProviderProfile() {
    // Normalize UI values so the backend always receives a full providers/* id.
    const value = runtimeProviderSelect.value || '';
    return value.startsWith('providers/') ? value : `providers/${value}`;
  }

  function providerRow() {
    const current = selectedProviderProfile();
    return providerProfiles.find((item) => `providers/${item.provider_profile}` === current || item.provider_profile === current) || null;
  }

  function providerCapabilities() {
    return providerRow()?.capabilities || {};
  }

  function refreshProcessingModeOptions() {
    const providerStreamOption = processingModeSelect.querySelector('option[value="provider_stream"]');
    if (!providerStreamOption) {
      return;
    }
    const supportsStreaming = Boolean(providerCapabilities().supports_streaming);
    providerStreamOption.disabled = !supportsStreaming;
    providerStreamOption.textContent = supportsStreaming
      ? 'provider stream'
      : 'provider stream (unsupported by selected provider)';
    if (!supportsStreaming && (processingModeSelect.value || 'segmented') === 'provider_stream') {
      processingModeSelect.value = 'segmented';
      ui.setFeedback(
        'runtimeFeedback',
        `Selected provider profile ${selectedProviderProfile()} does not support provider_stream mode. GUI switched back to segmented via VAD.`
      );
    }
  }

  function parseProviderSettings() {
    const raw = String(runtimeProviderSettings.value || '').trim();
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Advanced provider settings must be a JSON object');
    }
    return parsed;
  }

  function selectedSampleRow() {
    const current = sampleSelect.value || '';
    return (sampleCatalog.samples || []).find((item) => item.path === current) || null;
  }

  function selectedSamplePath({ required = false } = {}) {
    const value = sampleSelect.value || sampleCatalog.default_sample || '';
    if (required && !value) {
      throw new Error('Select a project WAV sample or upload one before using file-mode runtime.');
    }
    return value;
  }

  function activeRuntimeSessionId() {
    return (
      state.runtime.live?.status?.session_id ||
      state.runtime.live?.active_session?.session_id ||
      sessionIdInput.value ||
      ''
    );
  }

  function audioInputStatusForSession(sessionId) {
    const audioNode = (state.runtime.live?.node_statuses || []).find((item) => item.node_name === 'audio_input_node');
    if (!audioNode) {
      return null;
    }
    const message = String(audioNode.status_message || '');
    if (!sessionId) {
      return audioNode;
    }
    return message.includes(`session=${sessionId}`) ? audioNode : null;
  }

  function effectiveRuntimeState() {
    const status = state.runtime.live?.status || {};
    const activeSession = state.runtime.live?.active_session || {};
    const sessionId = activeRuntimeSessionId();
    const audioNode = audioInputStatusForSession(sessionId);
    const audioMessage = String(audioNode?.status_message || '');
    if (sessionId && audioMessage.startsWith('completed') && audioMessage.includes(`session=${sessionId}`)) {
      return 'completed';
    }
    return status.session_state || status.state || activeSession.state || 'unknown';
  }

  function effectiveRuntimeMessage() {
    const status = state.runtime.live?.status || {};
    const sessionId = activeRuntimeSessionId();
    const audioNode = audioInputStatusForSession(sessionId);
    const audioMessage = String(audioNode?.status_message || '');
    if (sessionId && audioMessage.startsWith('completed') && audioMessage.includes(`session=${sessionId}`)) {
      return 'file replay finished; review the merged session transcript or start a new session';
    }
    return status.status_message || status.message || state.runtime.live?.active_session?.status_message || 'n/a';
  }

  function parseNoiseLevels() {
    return String(noiseLevelsInput?.value || '')
      .split(',')
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));
  }

  function selectedNoisePresetLevels() {
    return Array.from(noisePresetLevelsRoot?.querySelectorAll('input[type="checkbox"]:checked') || [])
      .map((item) => Number(item.dataset.snr))
      .filter((item) => Number.isFinite(item));
  }

  function effectiveNoiseLevels() {
    const merged = [];
    [...selectedNoisePresetLevels(), ...parseNoiseLevels()].forEach((value) => {
      if (!merged.some((existing) => Math.abs(existing - value) < 0.0001)) {
        merged.push(value);
      }
    });
    return merged;
  }

  function renderNoiseModeOptions(selected = '') {
    const values = (noiseCatalog.modes || []).map((item) => item.id);
    const current = selected || noiseModeSelect.value || values[0] || 'white';
    noiseModeSelect.innerHTML = values
      .map((item) => `<option value="${ui.escapeHtml(item)}">${ui.escapeHtml(item)}</option>`)
      .join('');
    if (values.includes(current)) {
      noiseModeSelect.value = current;
    }
  }

  function renderNoisePresetLevels(selectedIds = ['light', 'medium', 'heavy', 'extreme']) {
    noisePresetLevelsRoot.innerHTML = (noiseCatalog.levels || [])
      .filter((item) => item.id !== 'clean' && item.snr_db != null)
      .map((item) => {
        const checked = selectedIds.includes(item.id);
        return `
          <label>
            <input
              type="checkbox"
              value="${ui.escapeHtml(item.id)}"
              data-snr="${ui.escapeHtml(String(item.snr_db))}"
              ${checked ? 'checked' : ''}
            />
            ${ui.escapeHtml(item.id)} <span class="muted">(${ui.escapeHtml(String(item.snr_db))} dB)</span>
          </label>
        `;
      })
      .join('');
  }

  function setBusy(busy) {
    requestInFlight = busy;
    [startButton, reconfigureButton, stopButton, recognizeButton, sampleBrowseButton, generateNoiseButton].forEach((button) => {
      if (button) {
        button.disabled = busy;
      }
    });
    if (sampleUploadInput) {
      sampleUploadInput.disabled = busy;
    }
    if (sampleDropzone) {
      sampleDropzone.classList.toggle('is-busy', busy);
    }
  }

  const runRuntimeAction = createActionRunner({
    ui,
    isBusy: () => requestInFlight,
    setBusy,
  });

  function renderPresetMeta() {
    const row = providerRow();
    if (!row) {
      runtimeProviderPresetMeta.innerHTML = ui.renderEmpty('Select a provider profile to inspect available model presets.');
      return;
    }
    const presetId = runtimeProviderPresetSelect.value || row.default_preset || '';
    const presets = row.model_presets || [];
    const preset = presets.find((item) => item.preset_id === presetId) || row.execution_preview?.preset || null;
    const advancedFields = row.ui?.advanced_fields || [];
    const caps = providerCapabilities();
    runtimeProviderPresetMeta.innerHTML = `
      <div class="stack-item">
        <strong>${ui.escapeHtml(preset?.label || presetId || 'Default execution')}</strong>
        <p>${ui.escapeHtml(preset?.description || 'Provider will run with its profile defaults unless you add explicit JSON overrides.')}</p>
        <p class="muted">quality=${ui.escapeHtml(preset?.quality_tier || 'n/a')} resource=${ui.escapeHtml(preset?.resource_tier || 'n/a')} cost=${ui.escapeHtml(preset?.estimated_cost_tier || 'n/a')}</p>
        <p class="muted">streaming=${ui.escapeHtml(String(Boolean(caps.supports_streaming)))} mode=${ui.escapeHtml(caps.streaming_mode || 'none')}</p>
        ${!Boolean(caps.supports_streaming) ? '<p class="muted">Provider stream is unavailable for this provider. Use segmented via VAD or whole-file transcription.</p>' : ''}
        <p class="muted">advanced fields: ${ui.escapeHtml((advancedFields || []).join(', ') || 'none')}</p>
      </div>
      ${renderProviderGuideHtml(ui, row)}
    `;
  }

  function renderPresetOptions(selected = '') {
    const row = providerRow();
    const presets = row?.model_presets || [];
    if (!presets.length) {
      ui.updateSelectOptions(runtimeProviderPresetSelect, ['default'], 'default');
      runtimeProviderPresetSelect.disabled = true;
      refreshProcessingModeOptions();
      renderPresetMeta();
      return;
    }
    runtimeProviderPresetSelect.disabled = false;
    const values = presets.map((item) => item.preset_id);
    ui.updateSelectOptions(runtimeProviderPresetSelect, values, selected || row.default_preset || values[0]);
    refreshProcessingModeOptions();
    renderPresetMeta();
  }

  function renderSampleMeta() {
    const selected = selectedSampleRow();
    const items = [];

    if (selected) {
      items.push(`
        <div class="stack-item">
          <strong>Selected sample: ${ui.escapeHtml(selected.name)}</strong>
          <p>${ui.escapeHtml(selected.path)}</p>
          <p class="muted">duration=${ui.escapeHtml(String(selected.duration_sec ?? 'n/a'))}s sample_rate=${ui.escapeHtml(String(selected.sample_rate_hz ?? 'n/a'))}Hz size=${ui.escapeHtml(String(selected.size_bytes ?? 'n/a'))}B</p>
        </div>
      `);
      if ((selected.duration_sec || 0) >= 30 && (sourceModeSelect.value || 'file') === 'file') {
        items.push(`
          <div class="stack-item">
            <strong>Recommendation for long WAV files</strong>
            <p>Use <code>Transcribe Whole File</code> when you want one transcript for the entire recording. Use <code>Start Live Runtime</code> only when you want to inspect the live segmented pipeline and per-segment behavior.</p>
          </div>
        `);
      }
    } else {
      items.push(ui.renderEmpty('No valid project WAV samples found yet. Upload one with drag-and-drop or Browse WAV.'));
    }

    items.push(`
      <div class="stack-item">
        <strong>Runtime sample catalog</strong>
        <p>${ui.escapeHtml(String(sampleCatalog.sample_count ?? (sampleCatalog.samples || []).length))} usable WAV sample(s) from ${ui.escapeHtml(sampleCatalog.root || 'data/sample')}</p>
        <p class="muted">Uploaded samples are stored in ${ui.escapeHtml(sampleCatalog.upload_root || 'data/sample/uploads')}</p>
      </div>
    `);

    if ((sampleCatalog.skipped || []).length) {
      items.push(`
        <div class="stack-item">
          <strong>Skipped invalid sample files</strong>
          ${(sampleCatalog.skipped || [])
            .slice(0, 8)
            .map(
              (item) => `<p>${ui.escapeHtml(item.path)}${item.reason ? ` · ${ui.escapeHtml(item.reason)}` : ''}</p>`
            )
            .join('')}
        </div>
      `);
    }

    sampleCatalogMeta.innerHTML = items.join('');
  }

  async function loadSamples(preferred = '') {
    sampleCatalog = await api.runtimeSamples();
    const values = (sampleCatalog.samples || []).map((item) => item.path);
    if (!values.length) {
      sampleSelect.innerHTML = '<option value="">No usable WAV samples found</option>';
      sampleSelect.disabled = true;
      renderSampleMeta();
      return;
    }
    sampleSelect.disabled = false;
    ui.updateSelectOptions(
      sampleSelect,
      values,
      preferred || sampleSelect.value || sampleCatalog.default_sample || values[0]
    );
    renderSampleMeta();
  }

  async function loadSelectors() {
    // Runtime profile controls pipeline behavior; provider profile controls the
    // ASR adapter. They are loaded from different gateway endpoints.
    const currentRuntimeProfile = runtimeProfileSelect.value;
    const currentProviderProfile = runtimeProviderSelect.value;
    const currentNoiseMode = noiseModeSelect.value;
    const currentNoisePresetIds = Array.from(
      noisePresetLevelsRoot?.querySelectorAll('input[type="checkbox"]:checked') || []
    ).map((item) => item.value);
    const [runtimeProfiles, providerProfilesResp, fetchedNoiseCatalog] = await Promise.all([
      api.profilesByType('runtime'),
      api.providersProfiles(),
      api.noiseCatalog().catch(() => noiseCatalog),
    ]);

    providerProfiles = providerProfilesResp.profiles || [];
    noiseCatalog = fetchedNoiseCatalog || noiseCatalog;
    ui.updateSelectOptions(
      runtimeProfileSelect,
      runtimeProfiles.profiles || [],
      currentRuntimeProfile || (selectorsLoaded ? '' : 'default_runtime')
    );
    ui.updateSelectOptions(
      runtimeProviderSelect,
      providerProfiles.map((item) => item.provider_profile),
      currentProviderProfile || (selectorsLoaded ? '' : 'whisper_local')
    );
    renderNoiseModeOptions(currentNoiseMode || 'white');
    renderNoisePresetLevels(
      currentNoisePresetIds.length ? currentNoisePresetIds : ['light', 'medium', 'heavy', 'extreme']
    );
    renderPresetOptions(runtimeProviderPresetSelect.value);
    selectorsLoaded = true;
  }

  function renderStatus() {
    // Show live runtime state separately from the form draft. The operator may
    // change fields locally before applying them via Start/Reconfigure.
    const status = state.runtime.live?.status || {};
    const nodeStatuses = state.runtime.live?.node_statuses || [];
    const activeSession = state.runtime.live?.active_session || {};
    const sessionId = activeRuntimeSessionId();
    const audioNode = audioInputStatusForSession(sessionId);
    const readyNodes = nodeStatuses.filter((item) => item.ready).length;
    const pairs = [
      { key: 'Session State', value: effectiveRuntimeState() },
      { key: 'Session ID', value: sessionId || 'n/a' },
      { key: 'Backend', value: status.backend || 'n/a' },
      { key: 'Model Preset', value: status.model || 'n/a' },
      { key: 'Runtime Profile', value: status.runtime_profile || activeSession.profile_id || 'n/a' },
      { key: 'Audio Source', value: status.audio_source || sourceModeSelect.value || 'n/a' },
      { key: 'Processing Mode', value: status.processing_mode || activeSession.processing_mode || processingModeSelect.value || 'n/a' },
      { key: 'Audio Input', value: audioNode?.status_message || 'n/a' },
      { key: 'Provider Streaming Mode', value: status.streaming_mode || 'none' },
      { key: 'Status Message', value: effectiveRuntimeMessage() },
      { key: 'Streaming Supported', value: String(status.streaming_supported ?? false) },
      { key: 'Provider Runtime Ready', value: String(status.provider_runtime_ready ?? status.cloud_credentials_available ?? false) },
      { key: 'Cloud Credentials Available', value: String(status.cloud_credentials_available ?? false) },
      { key: 'Runtime Nodes Ready', value: `${readyNodes}/${nodeStatuses.length || 0}` },
    ];
    statusRoot.innerHTML = ui.renderKeyValueList(pairs);
  }

  function renderTimeline() {
    const events = state.runtime.live?.recent_events || [];
    const sessions = state.runtime.live?.session_statuses || [];
    const nodeStatuses = state.runtime.live?.node_statuses || [];
    const items = [
      ...events.map((item) => ({ type: 'event', ...item })),
      ...sessions.map((item) => ({ type: 'session', ...item })),
      ...nodeStatuses
        .filter((item) => item.last_error_code || item.health === 'degraded')
        .map((item) => ({ type: 'node', ...item })),
    ]
      .sort((left, right) => String(right.time || right.updated_at || '').localeCompare(String(left.time || left.updated_at || '')))
      .slice(0, 12);

    if (!items.length) {
      timelineRoot.innerHTML = ui.renderEmpty('No runtime events yet. Start a session to populate timeline.');
      return;
    }
    timelineRoot.innerHTML = items
      .map(
        (item) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.event || item.node_name || item.state || item.type || 'event')}</strong>
            <p>${ui.escapeHtml(item.message || item.status_message || item.last_error_message || '')}</p>
            <p class="muted">${ui.escapeHtml(item.time || item.updated_at || '')}</p>
          </div>
        `
      )
      .join('');
  }

  function renderTranscripts() {
    const partials = state.runtime.live?.recent_partials || [];
    const finals = state.runtime.live?.recent_results || [];
    const activeSessionId = activeRuntimeSessionId();
    const sessionFinals = finals
      .filter((item) => !activeSessionId || item.session_id === activeSessionId)
      .slice()
      .sort((left, right) => String(left.time || '').localeCompare(String(right.time || '')));
    const mergedTranscript = sessionFinals
      .filter((item) => String(item.text || '').trim())
      .map((item) => String(item.text || '').trim())
      .join('\n');
    const items = [...partials, ...finals]
      .filter((item) => !activeSessionId || item.session_id === activeSessionId)
      .sort((left, right) => String(right.time || '').localeCompare(String(left.time || '')))
      .slice(0, 16);
    if (!items.length) {
      transcriptsRoot.innerHTML = ui.renderEmpty(
        activeSessionId
          ? 'No transcription output for the active session yet.'
          : 'No transcription output yet. Start a session or use Transcribe Whole File to test the selected WAV.'
      );
      return;
    }
    const summaryCard = mergedTranscript
      ? `
          <div class="stack-item transcript-aggregate">
            <strong>Session Transcript</strong>
            <p class="transcript-block">${ui.escapeHtml(mergedTranscript)}</p>
            <p class="muted">${ui.escapeHtml(String(sessionFinals.length))} final segment(s) merged for the active session.</p>
          </div>
        `
      : '';
    transcriptsRoot.innerHTML = summaryCard + items
      .map(
        (item) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.provider_id || 'provider')} · ${ui.escapeHtml(item.type || 'final')}</strong>
            <p>${ui.escapeHtml(item.text || '(empty transcript)')}</p>
            <p class="muted">request=${ui.escapeHtml(item.request_id || '')} provider_ms=${ui.escapeHtml(String(item.provider_compute_latency_ms ?? item.latency_ms ?? ''))} e2e_ms=${ui.escapeHtml(String(item.end_to_end_latency_ms ?? item.time_to_final_result_ms ?? ''))}</p>
            <p class="muted">${ui.escapeHtml(item.degraded ? 'mode=degraded' : 'mode=normal')}</p>
            <p class="muted">${ui.escapeHtml(item.time || '')}</p>
          </div>
        `
      )
      .join('');
  }

  async function refreshLive() {
    // Live snapshot combines service-based status with topic-based recent
    // events/results collected by the gateway observer.
    const payload = await api.runtimeLive();
    state.runtime.live = payload;
    renderStatus();
    renderTimeline();
    renderTranscripts();

    const runtimeState = effectiveRuntimeState();
    ui.patchPulse('runtimePulse', `Runtime: ${runtimeState}`, runtimeState);
  }

  function runtimePayload() {
    // Keep one canonical payload builder so Start/Reconfigure share the same
    // interpretation of form values.
    const fileSamplePath = sourceModeSelect.value === 'file' ? selectedSamplePath({ required: true }) : '';
    if ((processingModeSelect.value || 'segmented') === 'provider_stream' && !providerCapabilities().supports_streaming) {
      throw new Error(
        `Selected provider profile ${selectedProviderProfile()} does not support provider_stream mode. Choose segmented via VAD or a streaming-capable provider.`
      );
    }
    return {
      runtime_profile: runtimeProfileSelect.value,
      provider_profile: selectedProviderProfile(),
      provider_preset: runtimeProviderPresetSelect.disabled ? '' : runtimeProviderPresetSelect.value,
      provider_settings: parseProviderSettings(),
      session_id: sessionIdInput.value,
      audio_source: sourceModeSelect.value || 'file',
      processing_mode: processingModeSelect.value || 'segmented',
      audio_file_path: fileSamplePath,
      language: languageInput.value,
      mic_capture_sec: 4.0,
    };
  }

  async function startRuntime() {
    const payload = await api.runtimeStart(runtimePayload());
    if (payload.session_id) {
      sessionIdInput.value = payload.session_id;
    }
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Runtime session started', 'success');
    await refreshLive();
  }

  async function reconfigureRuntime() {
    const payload = await api.runtimeReconfigure(runtimePayload());
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Runtime reconfigured', 'info');
    await refreshLive();
  }

  async function stopRuntime() {
    const payload = await api.runtimeStop({ session_id: sessionIdInput.value });
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Runtime stopped', 'info');
    await refreshLive();
  }

  async function recognizeOnce() {
    const base = runtimePayload();
    const payload = await api.runtimeRecognizeOnce({
      wav_path: selectedSamplePath({ required: true }),
      language: base.language,
      session_id: base.session_id,
      provider_profile: base.provider_profile,
      provider_preset: base.provider_preset,
      provider_settings: base.provider_settings,
    });
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Recognize once completed', 'success');
    await refreshLive();
  }

  async function uploadRuntimeSample(file) {
    if (!file) {
      throw new Error('Choose a WAV file to upload');
    }
    const payload = await api.runtimeUploadSample({ file });
    sampleCatalog = payload.catalog || sampleCatalog;
    await loadSamples(payload.sample_path || '');
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast(`Runtime sample uploaded: ${payload.sample?.name || file.name}`, 'success');
  }

  async function generateNoiseVariants() {
    const snrLevels = effectiveNoiseLevels();
    if (!snrLevels.length) {
      throw new Error('Select at least one preset level or enter a numeric SNR list');
    }
    const payload = await api.runtimeGenerateNoise({
      source_wav: selectedSamplePath({ required: true }),
      noise_mode: noiseModeSelect.value || 'white',
      snr_levels: snrLevels,
    });
    sampleCatalog = payload.catalog || sampleCatalog;
    const preferredSample = payload.generated?.[payload.generated.length - 1]?.path || '';
    await loadSamples(preferredSample);
    ui.setFeedback('runtimeNoiseFeedback', JSON.stringify(payload, null, 2));
    ui.toast(`Generated ${payload.generated?.length || 0} noise variant(s)`, 'success');
  }

  runtimeProviderSelect.addEventListener('change', () => renderPresetOptions(''));
  runtimeProviderPresetSelect.addEventListener('change', renderPresetMeta);
  sampleSelect.addEventListener('change', renderSampleMeta);

  const uploadFromInput = async (file) =>
    runRuntimeAction(() => uploadRuntimeSample(file), {
      feedbackId: 'runtimeFeedback',
      errorPrefix: 'Sample upload failed',
      onFinally: () => {
        if (sampleUploadInput) {
          sampleUploadInput.value = '';
        }
      },
    });

  sampleBrowseButton?.addEventListener('click', () => sampleUploadInput?.click());
  sampleUploadInput?.addEventListener('change', async (event) => {
    const [file] = Array.from(event.target.files || []);
    await uploadFromInput(file);
  });

  const preventDropDefaults = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  ['dragenter', 'dragover'].forEach((eventName) => {
    sampleDropzone?.addEventListener(eventName, (event) => {
      preventDropDefaults(event);
      sampleDropzone.classList.add('is-dragover');
    });
  });
  ['dragleave', 'drop'].forEach((eventName) => {
    sampleDropzone?.addEventListener(eventName, (event) => {
      preventDropDefaults(event);
      sampleDropzone.classList.remove('is-dragover');
    });
  });
  sampleDropzone?.addEventListener('drop', async (event) => {
    const [file] = Array.from(event.dataTransfer?.files || []);
    await uploadFromInput(file);
  });
  sampleDropzone?.addEventListener('click', (event) => {
    if (event.target === sampleBrowseButton) {
      return;
    }
    sampleUploadInput?.click();
  });
  sampleDropzone?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      sampleUploadInput?.click();
    }
  });
  generateNoiseButton?.addEventListener('click', () =>
    runRuntimeAction(generateNoiseVariants, {
      feedbackId: 'runtimeNoiseFeedback',
      errorPrefix: 'Noise generation failed',
    })
  );

  document.getElementById('runtimeStartBtn')?.addEventListener('click', () =>
    runRuntimeAction(startRuntime, {
      feedbackId: 'runtimeFeedback',
      errorPrefix: 'Start failed',
    })
  );

  document.getElementById('runtimeReconfigureBtn')?.addEventListener('click', () =>
    runRuntimeAction(reconfigureRuntime, {
      feedbackId: 'runtimeFeedback',
      errorPrefix: 'Reconfigure failed',
    })
  );

  document.getElementById('runtimeStopBtn')?.addEventListener('click', () =>
    runRuntimeAction(stopRuntime, {
      feedbackId: 'runtimeFeedback',
      errorPrefix: 'Stop failed',
    })
  );

  document.getElementById('runtimeRecognizeBtn')?.addEventListener('click', () =>
    runRuntimeAction(recognizeOnce, {
      feedbackId: 'runtimeFeedback',
      errorPrefix: 'Recognize failed',
    })
  );

  return {
    refresh: async () => {
      await Promise.all([loadSelectors(), loadSamples()]);
      await refreshLive();
    },
    poll: refreshLive,
  };
}
