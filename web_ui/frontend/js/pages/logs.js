export function initLogsPage(ctx) {
  const { api, ui } = ctx;

  const healthRoot = document.getElementById('diagnosticsHealth');
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

  return {
    refresh: async () => {
      await Promise.all([loadHealth(), loadIssues(), loadLogs()]);
    },
    poll: async () => {
      await Promise.all([loadHealth(), loadIssues()]);
    },
  };
}
