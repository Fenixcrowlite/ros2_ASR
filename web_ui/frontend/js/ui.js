// Shared browser UI rendering and utility helpers.
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
  if (['warning', 'warn', 'degraded', 'queued', 'idle', 'interrupted', 'incomplete', 'partial'].includes(value)) {
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

function formatNumber(value, digits = 3) {
  if (value == null || value === '') {
    return '—';
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  if (Number.isInteger(numeric)) {
    return String(numeric);
  }
  return numeric.toFixed(digits);
}

function badge(text, tone = '') {
  return `<span class="${statusBadgeClass(tone || text)}">${escapeHtml(text)}</span>`;
}

function statCards(cards) {
  return `
    <div class="cards-grid">
      ${(cards || [])
        .map(
          (card) => `
            <div class="panel stat-card ${escapeHtml(card.tone || '')}">
              <div class="stat-card__meta">
                <span class="stat-card__label">${escapeHtml(card.label || '')}</span>
                ${card.badge ? badge(card.badge, card.tone || card.badge) : ''}
              </div>
              <div class="stat-card__value">${escapeHtml(card.value || '—')}</div>
              ${card.hint ? `<p class="helper">${escapeHtml(card.hint)}</p>` : ''}
            </div>
          `
        )
        .join('')}
    </div>
  `;
}

function table(columns, rows, actions = null, options = {}) {
  if (!rows?.length) {
    return renderEmpty(options.emptyMessage || 'No rows to display.');
  }
  const headers = columns
    .map((col) => `<th>${escapeHtml(col.label)}</th>`)
    .join('');

  const body = rows
    .map((row) => {
      const rowAttrs = typeof options.rowAttributes === 'function' ? options.rowAttributes(row) : {};
      const rowAttrText = Object.entries(rowAttrs || {})
        .map(([key, value]) => `${escapeHtml(key)}="${escapeHtml(value)}"`)
        .join(' ');
      const cols = columns
        .map((col, index) => {
          const raw = typeof col.value === 'function' ? col.value(row) : row[col.key];
          const tdClass = [
            index === 0 && options.stickyFirstColumn ? 'table__cell--sticky' : '',
            typeof col.className === 'function' ? col.className(row) : col.className || '',
          ]
            .filter(Boolean)
            .join(' ');
          return `<td class="${escapeHtml(tdClass)}">${raw ?? '—'}</td>`;
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

      return `<tr ${rowAttrText}>${cols}${actionCell}</tr>`;
    })
    .join('');

  const actionHead = actions ? `<th>${escapeHtml(options.actionsHeaderLabel || 'Actions')}</th>` : '';
  const tableClass = ['table', options.className || '', options.stickyFirstColumn ? 'table--sticky-first' : '']
    .filter(Boolean)
    .join(' ');
  return `
    <div class="table-wrap">
      <table class="${escapeHtml(tableClass)}">
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

function renderMetricBars(title, metrics, preferenceMap = {}) {
  const entries = Object.entries(metrics || {});
  if (!entries.length) {
    return renderEmpty(`No ${title.toLowerCase()} metrics yet.`);
  }
  const maxValue = Math.max(
    ...entries.map(([, value]) => {
      const numeric = Number(value);
      return Number.isFinite(numeric) ? Math.abs(numeric) : 0;
    }),
    1
  );
  return `
    <div class="stack-item">
      <strong>${escapeHtml(title)}</strong>
      ${entries
        .map(([key, value]) => {
          const numeric = Number(value) || 0;
          const width = Math.max(6, Math.min(100, (Math.abs(numeric) / maxValue) * 100));
          const pref = preferenceMap[key] || 'lower';
          return `
            <div class="metric-bar">
              <div class="metric-bar__head">
                <span>${escapeHtml(key)}</span>
                <code>${escapeHtml(String(value))}</code>
              </div>
              <div class="metric-bar__track">
                <span class="metric-bar__fill ${pref === 'higher' ? 'higher' : 'lower'}" style="width:${width}%"></span>
              </div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
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
  statCards,
  table,
  toast,
  toCode,
  updateSelectOptions,
  renderMetricBars,
  formatNumber,
  badge,
};
