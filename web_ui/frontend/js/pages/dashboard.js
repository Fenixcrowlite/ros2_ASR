export function initDashboardPage(ctx) {
  const { api, ui, state, navigate } = ctx;

  const cardsRoot = document.getElementById('dashboardCards');
  const alertsRoot = document.getElementById('dashboardAlerts');
  const outputRoot = document.getElementById('dashboardRuntimeOutput');
  const cloudRoot = document.getElementById('dashboardCloudHealth');
  const actionsRoot = document.getElementById('dashboardQuickActions');
  let runtimeActionInFlight = false;

  function renderCards(payload) {
    const runtime = payload.runtime || {};
    const providersConfigured = payload.system?.providers_configured ?? 0;
    const providersInvalid = payload.system?.providers_invalid ?? 0;
    const benchmarkActive = payload.system?.benchmark_active ? 'yes' : 'no';

    cardsRoot.innerHTML = [
      {
        title: 'Gateway',
        value: payload.system?.gateway || 'unknown',
        hint: 'GUI backend health',
      },
      {
        title: 'Runtime State',
        value: runtime.session_state || runtime.state || 'unknown',
        hint: `backend: ${runtime.backend || 'n/a'}`,
      },
      {
        title: 'Provider Profiles',
        value: `${providersConfigured} valid / ${providersInvalid} invalid`,
        hint: 'Readiness snapshot',
      },
      {
        title: 'Benchmark Active',
        value: benchmarkActive,
        hint: 'Background benchmark execution',
      },
    ]
      .map(
        (card) => `
          <div class="panel">
            <h3>${ui.escapeHtml(card.title)}</h3>
            <div class="badge ${ui.statusBadgeClass(card.value).replace('badge ', '')}">${ui.escapeHtml(card.value)}</div>
            <p class="helper">${ui.escapeHtml(card.hint)}</p>
          </div>
        `
      )
      .join('');
  }

  function renderAlerts(payload) {
    const alerts = payload.alerts || [];
    if (!alerts.length) {
      alertsRoot.innerHTML = ui.renderEmpty('No current alerts. System is ready for runtime or benchmark workflows.');
      return;
    }
    alertsRoot.innerHTML = alerts
      .map(
        (item) => `
          <div class="stack-item">
            <span class="${ui.statusBadgeClass(item.severity)}">${ui.escapeHtml(item.severity)}</span>
            <p><strong>${ui.escapeHtml(item.component || 'system')}</strong>: ${ui.escapeHtml(item.message || '')}</p>
            <p>${ui.escapeHtml(item.suggestion || '')}</p>
          </div>
        `
      )
      .join('');
  }

  function renderRuntimeOutput(runtimeLive) {
    const recent = [...(runtimeLive?.recent_partials || []), ...(runtimeLive?.recent_results || [])]
      .sort((left, right) => String(right.time || '').localeCompare(String(left.time || '')));
    if (!recent.length) {
      outputRoot.innerHTML = ui.renderEmpty('No runtime outputs yet. Start Runtime or open Runtime page to inspect the live stream.');
      return;
    }
    outputRoot.innerHTML = recent
      .slice(0, 6)
      .map(
        (item) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.provider_id || 'provider')} · ${ui.escapeHtml(item.type || 'final')}</strong>
            <p>${ui.escapeHtml(item.text || item.message || '(empty result)')}</p>
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

  function renderCloudHealth(rows) {
    if (!rows?.length) {
      cloudRoot.innerHTML = ui.renderEmpty('No cloud credential refs discovered yet.');
      return;
    }
    cloudRoot.innerHTML = rows
      .map(
        (row) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(row.provider || 'provider')}</strong>
            <p><span class="${ui.statusBadgeClass(row.tone || (row.runtime_ready ? 'valid' : 'invalid'))}">${ui.escapeHtml(
              row.state || 'unknown'
            )}</span></p>
            <p>${ui.escapeHtml(row.message || '')}</p>
            <p class="muted">linked=${ui.escapeHtml((row.linked_provider_profiles || []).join(', ') || 'none')}</p>
          </div>
        `
      )
      .join('');
  }

  function bindActions() {
    actionsRoot.innerHTML = `
      <button class="btn-primary" id="dashboardStartRuntime">Start Runtime</button>
      <button class="btn-danger" id="dashboardStopRuntime">Stop Runtime</button>
      <button class="btn-secondary" id="dashboardOpenRuntime">Open Runtime</button>
      <button class="btn-secondary" id="dashboardOpenBenchmark">Open Benchmark</button>
      <button class="btn-secondary" id="dashboardOpenDatasets">Import Dataset</button>
    `;

    document.getElementById('dashboardStartRuntime')?.addEventListener('click', async () => {
      if (runtimeActionInFlight) {
        return;
      }
      runtimeActionInFlight = true;
      try {
        const payload = await api.runtimeStart({
          runtime_profile: 'default_runtime',
          provider_profile: 'providers/whisper_local',
          session_id: '',
          audio_source: 'file',
          audio_file_path: 'data/sample/vosk_test.wav',
          language: 'en-US',
          mic_capture_sec: 4.0,
        });
        ui.toast(`Runtime started: ${payload.session_id || 'session active'}`, 'success');
        await refresh();
        navigate('runtime');
      } catch (error) {
        ui.toast(`Runtime start failed: ${error.message}`, 'error', 4500);
      } finally {
        runtimeActionInFlight = false;
      }
    });

    document.getElementById('dashboardStopRuntime')?.addEventListener('click', async () => {
      if (runtimeActionInFlight) {
        return;
      }
      runtimeActionInFlight = true;
      try {
        await api.runtimeStop({ session_id: '' });
        ui.toast('Runtime stopped', 'info');
        await refresh();
      } catch (error) {
        ui.toast(`Runtime stop failed: ${error.message}`, 'error', 4500);
      } finally {
        runtimeActionInFlight = false;
      }
    });

    document.getElementById('dashboardOpenRuntime')?.addEventListener('click', () => navigate('runtime'));
    document.getElementById('dashboardOpenBenchmark')?.addEventListener('click', () => navigate('benchmark'));
    document.getElementById('dashboardOpenDatasets')?.addEventListener('click', () => navigate('datasets'));
  }

  async function refresh() {
    const payload = await api.dashboard();
    state.runtime.live = payload.runtime_live || state.runtime.live || {};
    renderCards(payload);
    renderAlerts(payload);
    renderRuntimeOutput(state.runtime.live);
    renderCloudHealth(payload.cloud_credentials || []);

    const runtimeState = payload.runtime?.session_state || payload.runtime?.state || 'unknown';
    const benchmarkActive = payload.benchmark?.active_runs?.length ? 'running' : 'idle';

    ui.patchPulse('gatewayPulse', 'Gateway: online', 'ok');
    ui.patchPulse('runtimePulse', `Runtime: ${runtimeState}`, runtimeState);
    ui.patchPulse('benchmarkPulse', `Benchmark: ${benchmarkActive}`, benchmarkActive);
  }

  bindActions();

  return {
    refresh,
    poll: refresh,
  };
}
