export function initResultsPage(ctx) {
  const { api, ui, state } = ctx;

  const overviewRoot = document.getElementById('resultsOverview');
  const runSelect = document.getElementById('resultsRunSelect');
  const runDetailRoot = document.getElementById('resultsRunDetail');
  const compareInput = document.getElementById('resultsCompareRuns');
  const compareRoot = document.getElementById('resultsComparisonTable');

  let recentRuns = [];

  function renderOverview(payload) {
    const latest = payload.latest_completed || {};
    const rows = payload.recent_runs || [];
    recentRuns = rows;

    overviewRoot.innerHTML = [
      {
        title: 'Latest Run',
        value: latest.run_id || 'none',
        hint: latest.state || 'unknown',
      },
      {
        title: 'Recent Runs',
        value: String(rows.length),
        hint: 'Stored under artifacts/benchmark_runs',
      },
      {
        title: 'Comparison Ready',
        value: String((payload.comparison_ready_runs || []).length),
        hint: 'Can be selected for metric comparison',
      },
    ]
      .map(
        (card) => `
          <div class="panel">
            <h3>${ui.escapeHtml(card.title)}</h3>
            <div class="badge badge-info">${ui.escapeHtml(card.value)}</div>
            <p class="helper">${ui.escapeHtml(card.hint)}</p>
          </div>
        `
      )
      .join('');

    ui.updateSelectOptions(runSelect, rows.map((row) => row.run_id), rows[0]?.run_id || '');
  }

  async function loadOverview() {
    const payload = await api.resultsOverview();
    renderOverview(payload);
  }

  async function loadRunDetail(runId) {
    if (!runId) {
      runDetailRoot.innerHTML = ui.renderEmpty('Select a run to inspect details.');
      return;
    }
    try {
      const detail = await api.resultsRunDetail(runId);
      const summary = detail.summary || {};
      const runManifest = detail.run_manifest || {};

      runDetailRoot.innerHTML = `
        <div class="stack-item">
          <strong>${ui.escapeHtml(runId)}</strong>
          <p>state: ${ui.escapeHtml(detail.state || '')}</p>
          <p>benchmark_profile: ${ui.escapeHtml(runManifest.benchmark_profile || '')}</p>
          <p>dataset_profile: ${ui.escapeHtml(runManifest.dataset_profile || '')}</p>
          <p>scenario: ${ui.escapeHtml(runManifest.scenario || summary.scenario || '')}</p>
          <p>execution_mode: ${ui.escapeHtml(summary.execution_mode || runManifest.execution_mode || 'batch')}</p>
          <p>providers: ${ui.escapeHtml((runManifest.providers || []).join(', '))}</p>
        </div>
        ${ui.renderMetricBars('Quality metrics', summary.quality_metrics || {}, { wer: 'lower', cer: 'lower', sample_accuracy: 'higher' })}
        ${ui.renderMetricBars('Resource metrics', summary.resource_metrics || {}, {
          total_latency_ms: 'lower',
          per_utterance_latency_ms: 'lower',
          real_time_factor: 'lower',
          estimated_cost_usd: 'lower',
          first_partial_latency_ms: 'lower',
          finalization_latency_ms: 'lower',
          partial_count: 'higher',
        })}
        <div class="stack-item">
          <strong>Noise summary</strong>
          <p>${ui.escapeHtml(JSON.stringify(summary.noise_summary || {}, null, 2))}</p>
        </div>
        <div class="stack-item">
          <strong>Artifacts</strong>
          <p>${ui.escapeHtml(JSON.stringify(detail.artifacts || {}, null, 2))}</p>
        </div>
      `;
    } catch (error) {
      runDetailRoot.innerHTML = ui.renderEmpty(`Failed to load run detail: ${error.message}`);
    }
  }

  function renderComparison(payload) {
    const tableRows = payload.table || [];
    if (!tableRows.length) {
      compareRoot.innerHTML = ui.renderEmpty('No comparable metrics found for selected runs.');
      return;
    }

    compareRoot.innerHTML = ui.table(
      [
        { key: 'metric', label: 'Metric', value: (row) => ui.escapeHtml(row.metric) },
        { key: 'pref', label: 'Preference', value: (row) => ui.escapeHtml(row.preference) },
        {
          key: 'values',
          label: 'Values by Run',
          value: (row) =>
            Object.entries(row.values || {})
              .map(([runId, value]) => `<code>${ui.escapeHtml(runId)}=${ui.escapeHtml(String(value ?? 'n/a'))}</code>`)
              .join('<br />'),
        },
        {
          key: 'best',
          label: 'Best Run',
          value: (row) => `<span class="${ui.statusBadgeClass('ok')}">${ui.escapeHtml(row.best_run || '')}</span>`,
        },
      ],
      tableRows
    );
  }

  document.getElementById('resultsLoadRunBtn')?.addEventListener('click', async () => {
    await loadRunDetail(runSelect.value);
  });

  document.getElementById('resultsCompareBtn')?.addEventListener('click', async () => {
    try {
      const runIds = ui.parseCsvInput(compareInput.value);
      if (!runIds.length) {
        throw new Error('Enter at least one run ID');
      }
      const payload = await api.resultsCompare({ run_ids: runIds });
      state.results.lastComparison = payload;
      renderComparison(payload);
      ui.toast('Comparison completed', 'success');
    } catch (error) {
      compareRoot.innerHTML = ui.renderEmpty(`Comparison failed: ${error.message}`);
      ui.toast(`Comparison failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('resultsExportBtn')?.addEventListener('click', async () => {
    try {
      const runIds = ui.parseCsvInput(compareInput.value);
      if (!runIds.length) {
        throw new Error('Enter run IDs for export');
      }

      const formats = [];
      if (document.getElementById('resultsExportJson').checked) formats.push('json');
      if (document.getElementById('resultsExportCsv').checked) formats.push('csv');
      if (document.getElementById('resultsExportMd').checked) formats.push('md');
      if (!formats.length) {
        throw new Error('Select at least one export format');
      }

      const payload = await api.resultsExport({
        run_ids: runIds,
        formats,
        name: document.getElementById('resultsExportName').value,
      });
      ui.setFeedback('resultsExportFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Export completed', 'success');
    } catch (error) {
      ui.setFeedback('resultsExportFeedback', error.message, 'error');
      ui.toast(`Export failed: ${error.message}`, 'error');
    }
  });

  return {
    refresh: async () => {
      await loadOverview();
      if (runSelect.value) {
        await loadRunDetail(runSelect.value);
      }
      if (recentRuns.length) {
        compareInput.value = recentRuns.slice(0, 2).map((row) => row.run_id).join(', ');
      }
    },
    poll: null,
  };
}
