function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function fmtDate(value) {
  if (!value) {
    return '—';
  }
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) {
    return String(value);
  }
  return dt.toLocaleString();
}

function statusBadgeClass(state) {
  const value = String(state || '').toLowerCase();
  if (['ok', 'ready', 'running', 'completed', 'healthy', 'valid'].includes(value)) {
    return 'badge badge-ok';
  }
  if (['warning', 'warn', 'degraded', 'queued', 'idle'].includes(value)) {
    return 'badge badge-warn';
  }
  if (['error', 'failed', 'invalid', 'unavailable'].includes(value)) {
    return 'badge badge-error';
  }
  return 'badge badge-muted';
}

function setFeedback(targetId, message, tone = 'info') {
  const node = document.getElementById(targetId);
  if (!node) {
    return;
  }
  node.textContent = message || '';
  node.dataset.tone = tone;
}

function renderEmpty(message) {
  return `<div class="stack-item"><strong>Empty</strong><p>${escapeHtml(message)}</p></div>`;
}

function renderKeyValueList(pairs) {
  return pairs
    .map(
      (item) => `
      <div class="stack-item">
        <strong>${escapeHtml(item.key)}</strong>
        <p>${escapeHtml(item.value)}</p>
      </div>`
    )
    .join('');
}

function toCode(value) {
  return `<code>${escapeHtml(value)}</code>`;
}

function table(columns, rows, actions = null) {
  const headers = columns
    .map((col) => `<th>${escapeHtml(col.label)}</th>`)
    .join('');

  const body = rows
    .map((row) => {
      const cols = columns
        .map((col) => {
          const raw = typeof col.value === 'function' ? col.value(row) : row[col.key];
          return `<td>${raw ?? '—'}</td>`;
        })
        .join('');

      const actionCell = actions
        ? `<td>${actions
            .map(
              (action) =>
                `<button class="btn-secondary" data-action="${escapeHtml(action.id)}" data-row="${escapeHtml(
                  action.rowKey(row)
                )}">${escapeHtml(action.label)}</button>`
            )
            .join(' ')}</td>`
        : '';

      return `<tr>${cols}${actionCell}</tr>`;
    })
    .join('');

  const actionHead = actions ? '<th>Actions</th>' : '';
  return `
    <div class="table-wrap">
      <table class="table">
        <thead><tr>${headers}${actionHead}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;
}

function toast(message, tone = 'info', ttlMs = 3000) {
  const host = document.getElementById('toastHost');
  if (!host) {
    return;
  }
  const item = document.createElement('div');
  item.className = `toast ${tone}`;
  item.textContent = message;
  host.appendChild(item);
  window.setTimeout(() => {
    item.remove();
  }, ttlMs);
}

function patchPulse(id, text, state) {
  const el = document.getElementById(id);
  if (!el) {
    return;
  }
  el.className = statusBadgeClass(state);
  el.id = id;
  el.textContent = text;
}

function updateSelectOptions(selectEl, values, selectedValue = '') {
  if (!selectEl) {
    return;
  }
  const current = selectedValue || selectEl.value;
  selectEl.innerHTML = values
    .map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`)
    .join('');
  if (current && values.includes(current)) {
    selectEl.value = current;
  }
}

function parseCsvInput(raw) {
  return String(raw || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export {
  escapeHtml,
  fmtDate,
  parseCsvInput,
  patchPulse,
  renderEmpty,
  renderKeyValueList,
  setFeedback,
  statusBadgeClass,
  table,
  toast,
  toCode,
  updateSelectOptions,
};
