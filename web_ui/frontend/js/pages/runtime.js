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
  const wavPathInput = document.getElementById('runtimeWavPath');
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

  function selectedProviderProfile() {
    const value = runtimeProviderSelect.value || '';
    return value.startsWith('providers/') ? value : `providers/${value}`;
  }

  function providerRow() {
    const current = selectedProviderProfile();
    return providerProfiles.find((item) => `providers/${item.provider_profile}` === current || item.provider_profile === current) || null;
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

  function setBusy(busy) {
    requestInFlight = busy;
    [startButton, reconfigureButton, stopButton, recognizeButton].forEach((button) => {
      if (button) {
        button.disabled = busy;
      }
    });
  }

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
    runtimeProviderPresetMeta.innerHTML = `
      <div class="stack-item">
        <strong>${ui.escapeHtml(preset?.label || presetId || 'Default execution')}</strong>
        <p>${ui.escapeHtml(preset?.description || 'Provider will run with its profile defaults unless you add explicit JSON overrides.')}</p>
        <p class="muted">quality=${ui.escapeHtml(preset?.quality_tier || 'n/a')} resource=${ui.escapeHtml(preset?.resource_tier || 'n/a')} cost=${ui.escapeHtml(preset?.estimated_cost_tier || 'n/a')}</p>
        <p class="muted">advanced fields: ${ui.escapeHtml((advancedFields || []).join(', ') || 'none')}</p>
      </div>
    `;
  }

  function renderPresetOptions(selected = '') {
    const row = providerRow();
    const presets = row?.model_presets || [];
    if (!presets.length) {
      ui.updateSelectOptions(runtimeProviderPresetSelect, ['default'], 'default');
      runtimeProviderPresetSelect.disabled = true;
      renderPresetMeta();
      return;
    }
    runtimeProviderPresetSelect.disabled = false;
    const values = presets.map((item) => item.preset_id);
    ui.updateSelectOptions(runtimeProviderPresetSelect, values, selected || row.default_preset || values[0]);
    renderPresetMeta();
  }

  async function loadSelectors() {
    const currentRuntimeProfile = runtimeProfileSelect.value;
    const currentProviderProfile = runtimeProviderSelect.value;
    const [runtimeProfiles, providerProfilesResp] = await Promise.all([
      api.profilesByType('runtime'),
      api.providersProfiles(),
    ]);

    providerProfiles = providerProfilesResp.profiles || [];
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
    renderPresetOptions(runtimeProviderPresetSelect.value);
    selectorsLoaded = true;
  }

  function renderStatus() {
    const status = state.runtime.live?.status || {};
    const nodeStatuses = state.runtime.live?.node_statuses || [];
    const activeSession = state.runtime.live?.active_session || {};
    const readyNodes = nodeStatuses.filter((item) => item.ready).length;
    const pairs = [
      { key: 'Session State', value: status.session_state || status.state || 'unknown' },
      { key: 'Session ID', value: status.session_id || 'n/a' },
      { key: 'Backend', value: status.backend || 'n/a' },
      { key: 'Model Preset', value: status.model || 'n/a' },
      { key: 'Runtime Profile', value: status.runtime_profile || activeSession.profile_id || 'n/a' },
      { key: 'Audio Source', value: status.audio_source || sourceModeSelect.value || 'n/a' },
      { key: 'Processing Mode', value: status.processing_mode || activeSession.processing_mode || processingModeSelect.value || 'n/a' },
      { key: 'Provider Streaming Mode', value: status.streaming_mode || 'none' },
      { key: 'Status Message', value: status.status_message || status.message || 'n/a' },
      { key: 'Streaming Supported', value: String(status.streaming_supported ?? false) },
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
    const activeSessionId =
      state.runtime.live?.active_session?.session_id ||
      state.runtime.live?.status?.session_id ||
      sessionIdInput.value ||
      '';
    const items = [...partials, ...finals]
      .filter((item) => !activeSessionId || item.session_id === activeSessionId)
      .sort((left, right) => String(right.time || '').localeCompare(String(left.time || '')))
      .slice(0, 16);
    if (!items.length) {
      transcriptsRoot.innerHTML = ui.renderEmpty(
        activeSessionId
          ? 'No transcription output for the active session yet.'
          : 'No transcription output yet. Start a session or use Recognize Once to test runtime path.'
      );
      return;
    }
    transcriptsRoot.innerHTML = items
      .map(
        (item) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.provider_id || 'provider')} · ${ui.escapeHtml(item.type || 'final')}</strong>
            <p>${ui.escapeHtml(item.text || '(empty transcript)')}</p>
            <p class="muted">request=${ui.escapeHtml(item.request_id || '')} latency=${ui.escapeHtml(String(item.latency_ms ?? ''))}</p>
            <p class="muted">${ui.escapeHtml(item.degraded ? 'mode=degraded' : 'mode=normal')}</p>
            <p class="muted">${ui.escapeHtml(item.time || '')}</p>
          </div>
        `
      )
      .join('');
  }

  async function refreshLive() {
    const payload = await api.runtimeLive();
    state.runtime.live = payload;
    renderStatus();
    renderTimeline();
    renderTranscripts();

    const runtimeState = payload.status?.session_state || payload.status?.state || 'unknown';
    ui.patchPulse('runtimePulse', `Runtime: ${runtimeState}`, runtimeState);
  }

  function runtimePayload() {
    return {
      runtime_profile: runtimeProfileSelect.value,
      provider_profile: selectedProviderProfile(),
      provider_preset: runtimeProviderPresetSelect.disabled ? '' : runtimeProviderPresetSelect.value,
      provider_settings: parseProviderSettings(),
      session_id: sessionIdInput.value,
      audio_source: sourceModeSelect.value || 'file',
      processing_mode: processingModeSelect.value || 'segmented',
      audio_file_path: sourceModeSelect.value === 'file' ? wavPathInput.value : '',
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
      wav_path: wavPathInput.value,
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

  runtimeProviderSelect.addEventListener('change', () => renderPresetOptions(''));
  runtimeProviderPresetSelect.addEventListener('change', renderPresetMeta);

  document.getElementById('runtimeStartBtn')?.addEventListener('click', async () => {
    if (requestInFlight) {
      return;
    }
    setBusy(true);
    try {
      await startRuntime();
    } catch (error) {
      ui.setFeedback('runtimeFeedback', error.message, 'error');
      ui.toast(`Start failed: ${error.message}`, 'error');
    } finally {
      setBusy(false);
    }
  });

  document.getElementById('runtimeReconfigureBtn')?.addEventListener('click', async () => {
    if (requestInFlight) {
      return;
    }
    setBusy(true);
    try {
      await reconfigureRuntime();
    } catch (error) {
      ui.setFeedback('runtimeFeedback', error.message, 'error');
      ui.toast(`Reconfigure failed: ${error.message}`, 'error');
    } finally {
      setBusy(false);
    }
  });

  document.getElementById('runtimeStopBtn')?.addEventListener('click', async () => {
    if (requestInFlight) {
      return;
    }
    setBusy(true);
    try {
      await stopRuntime();
    } catch (error) {
      ui.setFeedback('runtimeFeedback', error.message, 'error');
      ui.toast(`Stop failed: ${error.message}`, 'error');
    } finally {
      setBusy(false);
    }
  });

  document.getElementById('runtimeRecognizeBtn')?.addEventListener('click', async () => {
    if (requestInFlight) {
      return;
    }
    setBusy(true);
    try {
      await recognizeOnce();
    } catch (error) {
      ui.setFeedback('runtimeFeedback', error.message, 'error');
      ui.toast(`Recognize failed: ${error.message}`, 'error');
    } finally {
      setBusy(false);
    }
  });

  return {
    refresh: async () => {
      await loadSelectors();
      await refreshLive();
    },
    poll: refreshLive,
  };
}
