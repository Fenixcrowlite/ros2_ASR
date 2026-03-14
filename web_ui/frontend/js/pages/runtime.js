export function initRuntimePage(ctx) {
  const { api, ui, state } = ctx;

  const runtimeProfileSelect = document.getElementById('runtimeProfileSelect');
  const runtimeProviderSelect = document.getElementById('runtimeProviderSelect');
  const sessionIdInput = document.getElementById('runtimeSessionId');
  const languageInput = document.getElementById('runtimeLanguage');
  const sourceModeSelect = document.getElementById('runtimeSourceMode');
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

  function setBusy(busy) {
    requestInFlight = busy;
    [startButton, reconfigureButton, stopButton, recognizeButton].forEach((button) => {
      if (button) {
        button.disabled = busy;
      }
    });
  }

  async function loadSelectors() {
    const currentRuntimeProfile = runtimeProfileSelect.value;
    const currentProviderProfile = runtimeProviderSelect.value;
    const [runtimeProfiles, providerProfiles] = await Promise.all([
      api.profilesByType('runtime'),
      api.profilesByType('providers'),
    ]);

    ui.updateSelectOptions(
      runtimeProfileSelect,
      runtimeProfiles.profiles || [],
      currentRuntimeProfile || (selectorsLoaded ? '' : 'default_runtime')
    );
    ui.updateSelectOptions(
      runtimeProviderSelect,
      providerProfiles.profiles || [],
      currentProviderProfile || (selectorsLoaded ? '' : 'whisper_local')
    );
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
      { key: 'Runtime Profile', value: status.runtime_profile || activeSession.profile_id || 'n/a' },
      { key: 'Audio Source', value: status.audio_source || sourceModeSelect.value || 'n/a' },
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
            <p class="muted">request=${ui.escapeHtml(item.request_id || '')} latency=${ui.escapeHtml(
              String(item.latency_ms ?? '')
            )}</p>
            <p class="muted">${ui.escapeHtml(
              item.raw_metadata_ref === 'provider:mock_fallback'
                ? 'mode=mock-fallback'
                : item.degraded
                  ? 'mode=degraded'
                  : 'mode=normal'
            )}</p>
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

  async function startRuntime() {
    const audioSource = sourceModeSelect.value || 'file';
    const payload = await api.runtimeStart({
      runtime_profile: runtimeProfileSelect.value,
      provider_profile: runtimeProviderSelect.value.startsWith('providers/')
        ? runtimeProviderSelect.value
        : `providers/${runtimeProviderSelect.value}`,
      session_id: sessionIdInput.value,
      audio_source: audioSource,
      audio_file_path: audioSource === 'file' ? wavPathInput.value : '',
      language: languageInput.value,
      mic_capture_sec: 4.0,
    });
    if (payload.session_id) {
      sessionIdInput.value = payload.session_id;
    }
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Runtime session started', 'success');
    await refreshLive();
  }

  async function reconfigureRuntime() {
    const audioSource = sourceModeSelect.value || 'file';
    const payload = await api.runtimeReconfigure({
      session_id: sessionIdInput.value,
      runtime_profile: runtimeProfileSelect.value,
      provider_profile: runtimeProviderSelect.value.startsWith('providers/')
        ? runtimeProviderSelect.value
        : `providers/${runtimeProviderSelect.value}`,
      audio_source: audioSource,
      audio_file_path: audioSource === 'file' ? wavPathInput.value : '',
      language: languageInput.value,
      mic_capture_sec: 4.0,
    });
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
    const payload = await api.runtimeRecognizeOnce({
      wav_path: wavPathInput.value,
      language: languageInput.value,
      session_id: sessionIdInput.value,
      provider_profile: runtimeProviderSelect.value.startsWith('providers/')
        ? runtimeProviderSelect.value
        : `providers/${runtimeProviderSelect.value}`,
    });
    ui.setFeedback('runtimeFeedback', JSON.stringify(payload, null, 2));
    ui.toast('Recognize once completed', 'success');
    await refreshLive();
  }

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
