const CHART_COLORS = ['#0d7f71', '#2a6fb0', '#b07a00', '#8c6fce', '#c05621', '#1d8f59', '#a23b72', '#5b7c99'];

function metricText(value, digits = 3) {
  if (value == null || value === '') {
    return '—';
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  if (Math.abs(numeric) >= 1000) {
    return numeric.toFixed(1);
  }
  if (Number.isInteger(numeric)) {
    return String(numeric);
  }
  return numeric.toFixed(digits);
}

function emptyState(ui, message) {
  return ui.renderEmpty(message);
}

function safeNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function valueBounds(values, fallbackMin = 0, fallbackMax = 1) {
  const numeric = values.map(safeNumber).filter((value) => value != null);
  if (!numeric.length) {
    return { min: fallbackMin, max: fallbackMax };
  }
  const min = Math.min(...numeric);
  const max = Math.max(...numeric);
  if (min === max) {
    const padding = Math.abs(min || fallbackMax || 1) * 0.1 || 0.1;
    return { min: min - padding, max: max + padding };
  }
  return { min, max };
}

function chartBounds(values, fallbackMin = 0, fallbackMax = 1) {
  const bounds = valueBounds(values, fallbackMin, fallbackMax);
  if (bounds.min === bounds.max) {
    return bounds;
  }
  const padding = (bounds.max - bounds.min) * 0.1;
  return {
    min: Math.max(0, bounds.min - padding),
    max: bounds.max + padding,
  };
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function shortLabel(label, limit = 42) {
  const text = String(label || '');
  if (text.length <= limit) {
    return text;
  }
  return `${text.slice(0, Math.max(1, limit - 1))}…`;
}

function preferenceTone(preference) {
  return preference === 'lower' ? 'warning' : 'ok';
}

function normalizedBarWidth(value, values, preference) {
  const numeric = safeNumber(value);
  const finiteValues = values.map(safeNumber).filter((item) => item != null);
  if (numeric == null || !finiteValues.length) {
    return 0;
  }
  const bounds = valueBounds(finiteValues, 0, 1);
  const range = bounds.max - bounds.min;
  if (!range) {
    return 100;
  }
  const score = preference === 'lower' ? (bounds.max - numeric) / range : (numeric - bounds.min) / range;
  return clamp(12 + score * 88, 12, 100);
}

function prefersLower(metric) {
  return ['wer', 'cer', 'latency', 'rtf', 'cost'].some((token) => String(metric || '').toLowerCase().includes(token));
}

function metricUnitSuffix(unit) {
  return unit ? ` ${unit}` : '';
}

function buildTicks(bounds, count = 4) {
  const ticks = [];
  const steps = Math.max(2, count);
  const range = bounds.max - bounds.min || 1;
  for (let index = 0; index <= steps; index += 1) {
    const ratio = index / steps;
    ticks.push({
      ratio,
      value: bounds.min + range * ratio,
    });
  }
  return ticks;
}

function colorForIndex(index) {
  return CHART_COLORS[index % CHART_COLORS.length];
}

function renderLegendList(ui, items = []) {
  if (!items.length) {
    return '';
  }
  return `
    <div class="chart-legend-list">
      ${items
        .map(
          (item) => `
            <div class="chart-legend-item">
              <span class="chart-swatch chart-swatch--numbered" style="--chart-color:${ui.escapeHtml(item.color)}">${ui.escapeHtml(
                String(item.index)
              )}</span>
              <div class="chart-legend-item__body">
                <strong title="${ui.escapeHtml(item.label)}">${ui.escapeHtml(shortLabel(item.label, 54))}</strong>
                <span>${ui.escapeHtml(item.detail)}</span>
              </div>
            </div>
          `
        )
        .join('')}
    </div>
  `;
}

function renderRankingBars(ui, rankings = []) {
  if (!rankings.length) {
    return emptyState(ui, 'No provider rankings available for this run.');
  }

  return `
    <div class="chart-grid chart-grid--rankings">
      ${rankings
        .map((ranking) => {
          const entries = ranking.entries || [];
          const values = entries.map((entry) => entry.value);
          return `
            <div class="chart-card">
              <div class="chart-card__head">
                <strong>${ui.escapeHtml(ranking.display_name || ranking.metric || 'Metric')}</strong>
                <span class="${ui.statusBadgeClass(preferenceTone(ranking.preference))}">
                  ${ui.escapeHtml(`${ranking.preference || 'higher'} is better`)}
                </span>
              </div>
              <p class="helper">Bars are normalized so the best provider stays visually longest even when lower values win.</p>
              <div class="ranking-list">
                ${entries
                  .map((entry) => `
                    <div class="ranking-row">
                      <div class="ranking-row__meta">
                        <div class="ranking-row__meta-main">
                          <span class="ranking-row__rank">#${ui.escapeHtml(String(entry.rank || '—'))}</span>
                          <span class="ranking-row__label" title="${ui.escapeHtml(entry.label || entry.provider_profile || 'provider')}">${ui.escapeHtml(
                            shortLabel(entry.label || entry.provider_profile || 'provider')
                          )}</span>
                        </div>
                        <code>${ui.escapeHtml(metricText(entry.value))}${ui.escapeHtml(metricUnitSuffix(ranking.unit))}</code>
                      </div>
                      <div class="metric-bar__track" aria-hidden="true">
                        <span
                          class="metric-bar__fill ${entry.rank === 1 ? 'higher' : 'lower'}"
                          style="width:${normalizedBarWidth(entry.value, values, ranking.preference)}%"
                        ></span>
                      </div>
                    </div>
                  `)
                  .join('')}
              </div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
}

function renderTradeoffScatter(ui, points = []) {
  if (!points.length) {
    return emptyState(ui, 'No quality-vs-latency points available.');
  }

  const width = 640;
  const height = 360;
  const padding = { top: 22, right: 26, bottom: 52, left: 72 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const xBounds = chartBounds(points.map((point) => point.latency_ms), 0, 100);
  const yBounds = chartBounds(points.map((point) => point.quality_score), 0, 1);
  const xTicks = buildTicks(xBounds, 4);
  const yTicks = buildTicks(yBounds, 4);

  const xAt = (value) => padding.left + ((value - xBounds.min) / (xBounds.max - xBounds.min || 1)) * plotWidth;
  const yAt = (value) => padding.top + plotHeight - ((value - yBounds.min) / (yBounds.max - yBounds.min || 1)) * plotHeight;

  const legendItems = points.map((point, index) => {
    const angle = ((index * 137.5) / 180) * Math.PI;
    const offsetX = Math.cos(angle) * 6;
    const offsetY = Math.sin(angle) * 6;
    const x = clamp(xAt(safeNumber(point.latency_ms) ?? xBounds.min) + offsetX, padding.left + 12, width - padding.right - 12);
    const y = clamp(yAt(safeNumber(point.quality_score) ?? yBounds.min) + offsetY, padding.top + 12, height - padding.bottom - 12);
    return {
      index: index + 1,
      label: point.label || 'provider',
      detail: `latency ${metricText(point.latency_ms)} ms | quality ${metricText(point.quality_score)} | cost ${metricText(point.cost_usd, 4)}`,
      color: colorForIndex(index),
      x,
      y,
    };
  });

  return `
    <div class="chart-card">
      <div class="chart-card__head">
        <strong>Quality vs Latency</strong>
        <span class="badge badge-info">upper-left is best</span>
      </div>
      <p class="helper">Markers are numbered in the plot and expanded below so long provider names never collide with the SVG.</p>
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Provider tradeoff scatter plot">
        <rect x="${padding.left}" y="${padding.top}" width="${plotWidth}" height="${plotHeight}" class="chart-plot-bg" />
        ${yTicks
          .map((tick) => {
            const y = padding.top + plotHeight - tick.ratio * plotHeight;
            return `
              <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" class="chart-grid-line" />
              <text x="${padding.left - 10}" y="${y + 4}" class="chart-axis-tick">${ui.escapeHtml(metricText(tick.value))}</text>
            `;
          })
          .join('')}
        ${xTicks
          .map((tick) => {
            const x = padding.left + tick.ratio * plotWidth;
            return `
              <line x1="${x}" y1="${padding.top}" x2="${x}" y2="${height - padding.bottom}" class="chart-grid-line" />
              <text x="${x}" y="${height - padding.bottom + 18}" class="chart-axis-tick chart-axis-tick--center">${ui.escapeHtml(metricText(tick.value))}</text>
            `;
          })
          .join('')}
        <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" class="chart-axis" />
        <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" class="chart-axis" />
        ${legendItems
          .map(
            (point) => `
              <circle cx="${point.x}" cy="${point.y}" r="12" fill="${ui.escapeHtml(point.color)}" class="chart-point" />
              <text x="${point.x}" y="${point.y + 4}" class="chart-point-index">${ui.escapeHtml(String(point.index))}</text>
            `
          )
          .join('')}
        <text x="${padding.left + plotWidth / 2}" y="${height - 10}" class="chart-caption">Latency (ms)</text>
        <text x="20" y="${padding.top + plotHeight / 2}" class="chart-caption chart-caption--vertical">Quality score</text>
      </svg>
      ${renderLegendList(ui, legendItems)}
    </div>
  `;
}

function renderLatencyStacks(ui, entries = []) {
  if (!entries.length) {
    return emptyState(ui, 'No latency breakdown is available for this run.');
  }

  const maxTotal = Math.max(...entries.map((entry) => Number(entry.end_to_end_latency_ms) || 0), 1);
  const segments = [
    ['preprocess_ms', 'Preprocess', 'latency-stack__segment--preprocess'],
    ['inference_ms', 'Inference', 'latency-stack__segment--inference'],
    ['postprocess_ms', 'Postprocess', 'latency-stack__segment--postprocess'],
    ['orchestration_overhead_ms', 'Overhead', 'latency-stack__segment--orchestration_overhead'],
  ];

  return `
    <div class="chart-card">
      <div class="chart-card__head">
        <strong>Latency Pipeline</strong>
        <span class="badge badge-info">scaled to slowest provider</span>
      </div>
      <p class="helper">Segment labels are rendered below each bar so narrow phases stay readable instead of spilling outside the stack.</p>
      <div class="stack-list">
        ${entries
          .map((entry) => `
            <div class="stack-item compact">
              <div class="chart-row-head">
                <strong title="${ui.escapeHtml(entry.label || 'provider')}">${ui.escapeHtml(shortLabel(entry.label || 'provider', 52))}</strong>
                <code>${ui.escapeHtml(metricText(entry.end_to_end_latency_ms))} ms total</code>
              </div>
              <div class="latency-stack" aria-hidden="true">
                ${segments
                  .map(([key, _label, className]) => {
                    const value = Number(entry[key]) || 0;
                    const width = Math.max(1, Math.min(100, (value / maxTotal) * 100));
                    return `<span class="latency-stack__segment ${className}" style="width:${width}%" title="${ui.escapeHtml(
                      `${key.replace(/_ms$/, '')}: ${metricText(value)} ms`
                    )}"></span>`;
                  })
                  .join('')}
              </div>
              <div class="chart-chip-row">
                ${segments
                  .map(([key, label, className]) => {
                    const value = Number(entry[key]);
                    if (!Number.isFinite(value)) {
                      return '';
                    }
                    return `
                      <span class="chart-chip">
                        <span class="chart-swatch ${ui.escapeHtml(className)}"></span>
                        ${ui.escapeHtml(label)} ${ui.escapeHtml(metricText(value))} ms
                      </span>
                    `;
                  })
                  .join('')}
              </div>
            </div>
          `)
          .join('')}
      </div>
    </div>
  `;
}

function heatColor(value, bounds, preference) {
  const numeric = safeNumber(value);
  if (numeric == null) {
    return { background: 'transparent', color: 'inherit' };
  }
  const range = bounds.max - bounds.min || 1;
  const normalized = clamp((numeric - bounds.min) / range, 0, 1);
  const severity = preference === 'lower' ? normalized : 1 - normalized;
  const hue = 148 - severity * 148;
  const saturation = 58;
  const lightness = 94 - severity * 32;
  return {
    background: `hsl(${hue} ${saturation}% ${lightness}%)`,
    color: severity > 0.58 ? '#ffffff' : 'var(--text)',
  };
}

function renderNoiseHeatmap(ui, matrix = [], metric = 'wer') {
  if (!matrix.length) {
    return emptyState(ui, 'No provider-by-noise metrics are available for this run.');
  }

  const providers = [...new Set(matrix.map((row) => row.label || row.provider_profile || 'provider'))];
  const noiseKeys = [...new Set(matrix.map((row) => row.noise_key || 'clean'))];
  const values = matrix.map((row) => safeNumber(row[metric])).filter((value) => value != null);
  const preference = prefersLower(metric) ? 'lower' : 'higher';
  const bounds = valueBounds(values, 0, 1);

  function cell(providerLabel, currentNoiseKey) {
    const row = matrix.find((item) => (item.label || item.provider_profile || 'provider') === providerLabel && (item.noise_key || 'clean') === currentNoiseKey);
    const value = safeNumber(row?.[metric]);
    if (value == null) {
      return '<td class="heatmap-cell heatmap-cell--empty"><span>n/a</span></td>';
    }
    const color = heatColor(value, bounds, preference);
    return `<td class="heatmap-cell" style="background:${color.background};color:${color.color}"><span>${ui.escapeHtml(metricText(value))}</span></td>`;
  }

  return `
    <div class="chart-card">
      <div class="chart-card__head">
        <strong>Noise Robustness</strong>
        <span class="badge badge-info">${ui.escapeHtml(metric.toUpperCase())}</span>
      </div>
      <p class="helper">Green cells are better and warm cells are worse for this metric. Headers stay sticky so the matrix remains readable while scrolling.</p>
      <div class="table-wrap">
        <table class="table table--compact table--sticky-first heatmap-table">
          <thead>
            <tr>
              <th>Provider</th>
              ${noiseKeys.map((noiseKey) => `<th title="${ui.escapeHtml(noiseKey)}">${ui.escapeHtml(shortLabel(noiseKey, 18))}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
            ${providers
              .map((providerLabel) => `
                <tr>
                  <td class="table__cell--sticky" title="${ui.escapeHtml(providerLabel)}">${ui.escapeHtml(shortLabel(providerLabel, 34))}</td>
                  ${noiseKeys.map((currentNoiseKey) => cell(providerLabel, currentNoiseKey)).join('')}
                </tr>
              `)
              .join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderComparisonSeries(ui, chartSeries = [], selectedMetric = '') {
  if (!chartSeries.length) {
    return emptyState(ui, 'No cross-run comparison chart is available.');
  }
  const series = chartSeries.find((item) => item.metric === selectedMetric) || chartSeries[0];
  const points = series.points || [];
  const values = points.map((point) => point.value);

  return `
    <div class="chart-card">
      <div class="chart-card__head">
        <strong>${ui.escapeHtml(series.display_name || series.metric || 'Metric')}</strong>
        <span class="${ui.statusBadgeClass(preferenceTone(series.preference))}">${ui.escapeHtml(
          `${series.preference || 'higher'} is better`
        )}</span>
      </div>
      <p class="helper">The comparison view uses the same best-is-longest normalization as provider rankings, while keeping raw values visible on the right.</p>
      <div class="ranking-list">
        ${points
          .map((point) => `
            <div class="ranking-row">
              <div class="ranking-row__meta">
                <div class="ranking-row__meta-main">
                  <span class="ranking-row__rank">#${ui.escapeHtml(String(point.rank || '—'))}</span>
                  <span class="ranking-row__label" title="${ui.escapeHtml(point.label || point.entity_id || 'entity')}">${ui.escapeHtml(
                    shortLabel(point.label || point.entity_id || 'entity')
                  )}</span>
                </div>
                <code>${ui.escapeHtml(metricText(point.value))}${ui.escapeHtml(metricUnitSuffix(series.unit))}</code>
              </div>
              <div class="metric-bar__track" aria-hidden="true">
                <span
                  class="metric-bar__fill ${point.rank === 1 ? 'higher' : 'lower'}"
                  style="width:${normalizedBarWidth(point.value, values, series.preference)}%"
                ></span>
              </div>
            </div>
          `)
          .join('')}
      </div>
    </div>
  `;
}

export {
  metricText,
  renderComparisonSeries,
  renderLatencyStacks,
  renderNoiseHeatmap,
  renderRankingBars,
  renderTradeoffScatter,
};
