// Dashboard page controller for the browser UI.
function metricValue(row, metricName, fallbacks = []) {
  const sectionOrder = [
    'quality_metrics',
    'latency_metrics',
    'reliability_metrics',
    'cost_metrics',
    'cost_totals',
    'streaming_metrics',
    'resource_metrics',
    'mean_metrics',
  ];
  for (const candidate of [metricName, ...fallbacks]) {
    for (const sectionName of sectionOrder) {
      const section = row?.[sectionName];
      const value = Number(section?.[candidate]);
      if (Number.isFinite(value)) {
        return value;
      }
    }
    const statistic = row?.metric_statistics?.[candidate];
    for (const key of ['value', 'mean', 'sum']) {
      const value = Number(statistic?.[key]);
      if (Number.isFinite(value)) {
        return value;
      }
    }
  }
  return null;
}

function providerLabel(row) {
  const base = row?.provider_profile || row?.provider_id || row?.provider_key || 'provider';
  return row?.provider_preset ? `${base} [${row.provider_preset}]` : base;
}

function bestProvider(providerSummaries = []) {
  return [...providerSummaries]
    .filter(Boolean)
    .sort((left, right) => {
      const leftWer = metricValue(left, 'wer') ?? Number.POSITIVE_INFINITY;
      const rightWer = metricValue(right, 'wer') ?? Number.POSITIVE_INFINITY;
      if (leftWer !== rightWer) {
        return leftWer - rightWer;
      }
      const leftLatency = metricValue(left, 'end_to_end_latency_ms', ['total_latency_ms']) ?? Number.POSITIVE_INFINITY;
      const rightLatency = metricValue(right, 'end_to_end_latency_ms', ['total_latency_ms']) ?? Number.POSITIVE_INFINITY;
      return leftLatency - rightLatency;
    })[0];
}

export function initDashboardPage(ctx) {
  const { api, ui, state, navigate } = ctx;

  const cardsRoot = document.getElementById('dashboardCards');
  const latestRunRoot = document.getElementById('dashboardLatestRun');
  const leaderboardRoot = document.getElementById('dashboardLeaderboard');
  const whatChangedRoot = document.getElementById('dashboardWhatChanged');
  const nextActionsRoot = document.getElementById('dashboardNextActions');
  const alertsRoot = document.getElementById('dashboardAlerts');
  const outputRoot = document.getElementById('dashboardRuntimeOutput');
  const cloudRoot = document.getElementById('dashboardCloudHealth');
  const actionsRoot = document.getElementById('dashboardQuickActions');

  let runtimeActionInFlight = false;

  function recentCompletedRuns(payload) {
    return (payload?.benchmark?.recent_runs || []).filter((row) => row.state === 'completed');
  }

  function renderCards(payload) {
    const runtime = payload.runtime || {};
    const completedRuns = recentCompletedRuns(payload);
    const cloudReady = (payload.cloud_credentials || []).filter((row) => row.runtime_ready).length;
    cardsRoot.innerHTML = ui.statCards([
      {
        label: 'Gateway',
        value: payload.system?.gateway || 'unknown',
        badge: payload.system?.gateway || 'unknown',
        tone: payload.system?.gateway || 'unknown',
        hint: 'HTTP control plane status',
      },
      {
        label: 'Runtime',
        value: runtime.session_state || runtime.state || 'unknown',
        badge: runtime.backend || 'n/a',
        tone: runtime.session_state || runtime.state || 'unknown',
        hint: 'Live runtime session state',
      },
      {
        label: 'Completed Runs',
        value: String(completedRuns.length),
        badge: payload.system?.benchmark_active ? 'running' : 'idle',
        tone: payload.system?.benchmark_active ? 'running' : 'idle',
        hint: 'Recent benchmark artifacts available for analysis',
      },
      {
        label: 'Cloud Ready',
        value: `${cloudReady}/${(payload.cloud_credentials || []).length || 0}`,
        badge: cloudReady ? 'ready' : 'warning',
        tone: cloudReady ? 'ok' : 'warning',
        hint: 'Credential refs ready for runtime/benchmark use',
      },
    ]);
  }

  function renderLatestRun(payload) {
    const latest = recentCompletedRuns(payload)[0];
    if (!latest) {
      latestRunRoot.innerHTML = ui.renderEmpty('No completed benchmark runs yet. Start from Benchmark to create the first research artifact.');
      return;
    }

    const topProvider = bestProvider(latest.provider_summaries || []);
    latestRunRoot.innerHTML = `
      <div class="stack-item">
        <strong>${ui.escapeHtml(latest.run_id || 'run')}</strong>
        <p>scenario=${ui.escapeHtml(latest.scenario || 'n/a')} · mode=${ui.escapeHtml(latest.execution_mode || 'batch')}</p>
        <p>samples=${ui.escapeHtml(String(latest.total_samples || 0))} · warnings=${ui.escapeHtml(String(latest.warning_samples || 0))}</p>
        ${
          topProvider
            ? `<p class="muted">best provider: ${ui.escapeHtml(providerLabel(topProvider))} · wer=${ui.escapeHtml(ui.formatNumber(metricValue(topProvider, 'wer')))}</p>`
            : '<p class="muted">No per-provider summary stored for this run.</p>'
        }
      </div>
    `;
  }

  function renderLeaderboard(payload) {
    const latest = recentCompletedRuns(payload)[0];
    const providerSummaries = latest?.provider_summaries || [];
    if (!providerSummaries.length) {
      leaderboardRoot.innerHTML = ui.renderEmpty('Leaderboard appears when the latest completed run stores per-provider summaries.');
      return;
    }
    leaderboardRoot.innerHTML = ui.table(
      [
        { key: 'provider', label: 'Provider', value: (row) => ui.escapeHtml(providerLabel(row)) },
        { key: 'wer', label: 'WER', value: (row) => ui.escapeHtml(ui.formatNumber(metricValue(row, 'wer'))) },
        {
          key: 'latency',
          label: 'Latency ms',
          value: (row) =>
            ui.escapeHtml(ui.formatNumber(metricValue(row, 'end_to_end_latency_ms', ['total_latency_ms']))),
        },
        {
          key: 'cost',
          label: 'Cost USD',
          value: (row) => ui.escapeHtml(ui.formatNumber(metricValue(row, 'estimated_cost_usd'), 4)),
        },
      ],
      [...providerSummaries].sort((left, right) => {
        const leftWer = metricValue(left, 'wer') ?? Number.POSITIVE_INFINITY;
        const rightWer = metricValue(right, 'wer') ?? Number.POSITIVE_INFINITY;
        return leftWer - rightWer;
      }),
      null,
      { className: 'table--compact', stickyFirstColumn: true }
    );
  }

  function renderWhatChanged(payload) {
    const completedRuns = recentCompletedRuns(payload);
    if (completedRuns.length < 2) {
      whatChangedRoot.innerHTML = ui.renderEmpty('Need at least two completed runs to describe the latest change in research signal.');
      return;
    }
    const latest = completedRuns[0];
    const previous = completedRuns[1];
    const latestBest = bestProvider(latest.provider_summaries || []);
    const previousBest = bestProvider(previous.provider_summaries || []);

    const comparisons = [
      {
        label: 'Best WER',
        latest: metricValue(latestBest || latest, 'wer'),
        previous: metricValue(previousBest || previous, 'wer'),
      },
      {
        label: 'Latency ms',
        latest: metricValue(latestBest || latest, 'end_to_end_latency_ms', ['total_latency_ms']),
        previous: metricValue(previousBest || previous, 'end_to_end_latency_ms', ['total_latency_ms']),
      },
      {
        label: 'Exact Match',
        latest: metricValue(latestBest || latest, 'sample_accuracy'),
        previous: metricValue(previousBest || previous, 'sample_accuracy'),
      },
    ];

    whatChangedRoot.innerHTML = comparisons
      .map((item) => {
        const latestValue = Number(item.latest);
        const previousValue = Number(item.previous);
        const delta = Number.isFinite(latestValue) && Number.isFinite(previousValue) ? latestValue - previousValue : null;
        return `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.label)}</strong>
            <p>latest=${ui.escapeHtml(ui.formatNumber(latestValue))} · previous=${ui.escapeHtml(ui.formatNumber(previousValue))}</p>
            <p class="muted">delta=${ui.escapeHtml(delta == null ? 'n/a' : ui.formatNumber(delta))} between ${ui.escapeHtml(previous.run_id)} and ${ui.escapeHtml(latest.run_id)}</p>
          </div>
        `;
      })
      .join('');
  }

  function renderNextActions(payload) {
    const items = [];
    const latest = recentCompletedRuns(payload)[0];
    if (!latest) {
      items.push({
        title: 'Create the first benchmark artifact',
        body: 'Open Benchmark, keep the clean baseline scenario, and run a small provider comparison so Results has data to analyze.',
      });
    }
    if ((payload.cloud_credentials || []).some((row) => !row.runtime_ready)) {
      items.push({
        title: 'Repair cloud credentials',
        body: 'Open Secrets and fix any provider ref that is linked but not runtime-ready.',
      });
    }
    if ((payload.alerts || []).length) {
      items.push({
        title: 'Resolve current alerts',
        body: 'Open Logs & Diagnostics after checking the latest warning cards below.',
      });
    }
    if (latest?.provider_summaries?.length > 1) {
      items.push({
        title: 'Inspect provider tradeoffs',
        body: `Open Results for ${latest.run_id} to compare quality, latency, and cost on one screen.`,
      });
    }

    nextActionsRoot.innerHTML = items.length
      ? items
          .map(
            (item) => `
              <div class="stack-item">
                <strong>${ui.escapeHtml(item.title)}</strong>
                <p>${ui.escapeHtml(item.body)}</p>
              </div>
            `
          )
          .join('')
      : ui.renderEmpty('No urgent next actions. The system is ready for more runtime or benchmark work.');
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
            <p class="muted">${ui.escapeHtml(item.degraded ? 'mode=degraded' : 'mode=normal')}</p>
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
      <button class="btn-secondary" id="dashboardStartHfLocal">Start HF Local</button>
      <button class="btn-danger" id="dashboardStopRuntime">Stop Runtime</button>
      <button class="btn-secondary" id="dashboardOpenBenchmark">Open Benchmark</button>
      <button class="btn-secondary" id="dashboardOpenResults">Open Results</button>
      <button class="btn-secondary" id="dashboardOpenSecrets">Open Secrets</button>
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

    document.getElementById('dashboardStartHfLocal')?.addEventListener('click', async () => {
      if (runtimeActionInFlight) {
        return;
      }
      runtimeActionInFlight = true;
      try {
        const payload = await api.runtimeStart({
          runtime_profile: 'huggingface_local_runtime',
          provider_profile: 'providers/huggingface_local',
          session_id: '',
          audio_source: 'file',
          audio_file_path: 'data/sample/vosk_test.wav',
          language: 'en-US',
          mic_capture_sec: 4.0,
        });
        ui.toast(`HF local runtime started: ${payload.session_id || 'session active'}`, 'success');
        await refresh();
        navigate('runtime');
      } catch (error) {
        ui.toast(`HF local runtime start failed: ${error.message}`, 'error', 4500);
      } finally {
        runtimeActionInFlight = false;
      }
    });

    document.getElementById('dashboardOpenBenchmark')?.addEventListener('click', () => navigate('benchmark'));
    document.getElementById('dashboardOpenResults')?.addEventListener('click', () => navigate('results'));
    document.getElementById('dashboardOpenSecrets')?.addEventListener('click', () => navigate('secrets'));
    document.getElementById('dashboardOpenDatasets')?.addEventListener('click', () => navigate('datasets'));
  }

  async function refresh() {
    const payload = await api.dashboard();
    state.runtime.live = payload.runtime_live || state.runtime.live || {};
    renderCards(payload);
    renderLatestRun(payload);
    renderLeaderboard(payload);
    renderWhatChanged(payload);
    renderNextActions(payload);
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
