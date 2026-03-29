export function initLogsPage(ctx) {
  const { api, ui } = ctx;

  const healthRoot = document.getElementById('diagnosticsHealth');
  const preflightSummaryRoot = document.getElementById('diagnosticsPreflightSummary');
  const preflightDetailsRoot = document.getElementById('diagnosticsPreflightDetails');
  const issuesRoot = document.getElementById('diagnosticsIssues');
  const logsViewer = document.getElementById('logsViewer');

  async function loadHealth() {
    const payload = await api.diagnosticsHealth();
    healthRoot.innerHTML = ui.renderKeyValueList([
      { key: 'Runtime', value: `${payload.runtime?.state || 'unknown'} (${payload.runtime?.backend || 'n/a'})` },
      {
        key: 'Providers',
        value: `${payload.providers?.valid_profiles || 0} valid / ${payload.providers?.invalid_profiles || 0} invalid`,
      },
      {
        key: 'Datasets',
        value: `${payload.datasets?.registered || 0} registered (${payload.datasets?.invalid || 0} invalid)`,
      },
      {
        key: 'Active benchmark runs',
        value: String((payload.benchmark?.active_runs || []).length),
      },
    ]);
  }

  async function loadIssues() {
    const payload = await api.diagnosticsIssues();
    const rows = payload.issues || [];
    if (!rows.length) {
      issuesRoot.innerHTML = ui.renderEmpty('No diagnostic issues found.');
      return;
    }

    issuesRoot.innerHTML = rows
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

  async function loadPreflight() {
    const payload = await api.diagnosticsPreflight();
    const checks = payload.checks || {};
    const modules = checks.modules || {};
    const ros = checks.ros || {};
    const microphone = checks.microphone || {};

    preflightSummaryRoot.innerHTML = ui.renderKeyValueList([
      { key: 'Overall', value: payload.ok ? 'ready' : 'issues detected' },
      {
        key: 'Python modules',
        value: `${Object.values(modules).filter((item) => item?.ok).length}/${Object.keys(modules).length} ok`,
      },
      { key: 'Microphone stack', value: microphone.ok ? 'ok' : microphone.message || 'unavailable' },
      {
        key: 'ROS / build setup',
        value: `${Object.values(ros).filter((item) => item?.ok).length}/${Object.keys(ros).length} ok`,
      },
    ]);

    const detailGroups = [
      {
        title: 'Python Modules',
        rows: Object.entries(modules).map(([name, item]) => ({
          name,
          ok: item?.ok,
          message: item?.message || '',
        })),
      },
      {
        title: 'ROS Stack',
        rows: Object.entries(ros).map(([name, item]) => ({
          name,
          ok: item?.ok,
          message: item?.message || '',
        })),
      },
      {
        title: 'Microphone',
        rows: [
          {
            name: 'microphone',
            ok: microphone.ok,
            message: microphone.message || '',
          },
        ],
      },
    ];

    preflightDetailsRoot.innerHTML = detailGroups
      .map(
        (group) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(group.title)}</strong>
            ${group.rows
              .map(
                (row) => `
                  <p><span class="${ui.statusBadgeClass(row.ok ? 'valid' : 'invalid')}">${row.ok ? 'ok' : 'missing'}</span> ${ui.escapeHtml(
                    row.name
                  )} · ${ui.escapeHtml(row.message)}</p>
                `
              )
              .join('')}
          </div>
        `
      )
      .join('');
  }

  async function loadLogs() {
    const component = document.getElementById('logsComponent').value;
    const severity = document.getElementById('logsSeverity').value;
    const limit = Number(document.getElementById('logsLimit').value || 200);

    const payload = await api.logs({ component, severity, limit: String(limit) });
    const rows = payload.entries || [];
    if (!rows.length) {
      logsViewer.textContent = 'No log entries for selected filters.';
      return;
    }

    logsViewer.textContent = rows
      .map((item) => `[${item.component}] [${item.severity}] ${item.message}`)
      .join('\n');
  }

  document.getElementById('logsRefreshBtn')?.addEventListener('click', async () => {
    try {
      await loadLogs();
      ui.toast('Logs refreshed', 'info');
    } catch (error) {
      logsViewer.textContent = `Failed to load logs: ${error.message}`;
      ui.toast(`Logs refresh failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('diagnosticsPreflightBtn')?.addEventListener('click', async () => {
    try {
      await loadPreflight();
      ui.toast('Preflight completed', 'info');
    } catch (error) {
      preflightSummaryRoot.innerHTML = ui.renderEmpty(`Preflight failed: ${error.message}`);
      preflightDetailsRoot.innerHTML = '';
      ui.toast(`Preflight failed: ${error.message}`, 'error');
    }
  });

  return {
    refresh: async () => {
      preflightSummaryRoot.innerHTML = ui.renderEmpty('Run preflight to check modules, audio devices, ROS setup, and installed gateway/runtime entrypoints.');
      preflightDetailsRoot.innerHTML = '';
      await Promise.all([loadHealth(), loadIssues(), loadLogs()]);
    },
    poll: async () => {
      await Promise.all([loadHealth(), loadIssues()]);
    },
  };
}
