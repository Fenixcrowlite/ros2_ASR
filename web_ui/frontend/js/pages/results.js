// Results page controller for the browser UI.
import {
  metricText,
  renderComparisonSeries,
  renderLatencyStacks,
  renderNoiseHeatmap,
  renderRankingBars,
  renderTradeoffScatter,
} from '../charts.js';

function firstPresent(...values) {
  for (const value of values) {
    if (value != null && value !== '') {
      return value;
    }
  }
  return null;
}

function statisticValue(statistic = {}) {
  return firstPresent(statistic.value, statistic.mean, statistic.sum);
}

function mutedLabel(ui, text) {
  return `<span class="muted">${ui.escapeHtml(text)}</span>`;
}

function normalizeQualityText(text) {
  const normalizedChars = [];
  for (const char of String(text || '').trim().toLowerCase()) {
    if (/\s/u.test(char)) {
      normalizedChars.push(' ');
      continue;
    }
    if (/[\p{L}\p{N}]/u.test(char)) {
      normalizedChars.push(char);
    }
  }
  return normalizedChars.join('').split(/\s+/u).filter(Boolean).join(' ');
}

function levenshtein(a, b) {
  if (!a.length) {
    return b.length;
  }
  if (!b.length) {
    return a.length;
  }

  const dp = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i += 1) {
    dp[i][0] = i;
  }
  for (let j = 0; j <= b.length; j += 1) {
    dp[0][j] = j;
  }

  for (let i = 1; i <= a.length; i += 1) {
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length];
}

function buildQualitySupport(referenceText, hypothesisText) {
  const normalizedReference = normalizeQualityText(referenceText);
  const normalizedHypothesis = normalizeQualityText(hypothesisText);
  const referenceWords = normalizedReference ? normalizedReference.split(' ') : [];
  const hypothesisWords = normalizedHypothesis ? normalizedHypothesis.split(' ') : [];
  const referenceChars = Array.from(normalizedReference.replaceAll(' ', ''));
  const hypothesisChars = Array.from(normalizedHypothesis.replaceAll(' ', ''));
  const referenceWordCount = referenceWords.length;
  const referenceCharCount = referenceChars.length;
  const wordEdits = levenshtein(referenceWords, hypothesisWords);
  const charEdits = levenshtein(referenceChars, hypothesisChars);

  return {
    normalized_reference: normalizedReference,
    normalized_hypothesis: normalizedHypothesis,
    reference_has_content: normalizedReference.length > 0,
    hypothesis_has_content: normalizedHypothesis.length > 0,
    reference_word_count: referenceWordCount,
    reference_char_count: referenceCharCount,
    word_edits: wordEdits,
    char_edits: charEdits,
    exact_match: normalizedReference.length > 0 && normalizedReference === normalizedHypothesis,
    wer: referenceWordCount > 0 ? wordEdits / referenceWordCount : 0,
    cer: referenceCharCount > 0 ? charEdits / referenceCharCount : 0,
  };
}

function getQualitySupport(row) {
  if (row?.quality_support && typeof row.quality_support === 'object') {
    return row.quality_support;
  }
  if (!row?.reference_text) {
    return null;
  }
  return buildQualitySupport(row.reference_text, row.text || '');
}

function providerLabel(row) {
  const base = row?.provider_profile || row?.provider_id || row?.provider_key || 'provider';
  return row?.provider_preset ? `${base} [${row.provider_preset}]` : base;
}

function noiseKey(row) {
  const noiseLevel = String(row?.noise_level || 'clean').trim().toLowerCase() || 'clean';
  const noiseMode = String(row?.noise_mode || 'none').trim().toLowerCase() || 'none';
  if (noiseLevel === 'clean' || noiseMode === 'none') {
    return 'clean';
  }
  return `${noiseMode}:${noiseLevel}`;
}

function noiseLabel(row) {
  const key = noiseKey(row);
  return key === 'clean' ? 'clean' : key;
}

function metricValue(row, metricName, fallbacks = []) {
  const sectionOrder = [
    'quality_metrics',
    'latency_metrics',
    'reliability_metrics',
    'cost_metrics',
    'cost_totals',
    'streaming_metrics',
    'resource_metrics',
    'diagnostic_metrics',
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
    const direct = Number(row?.metrics?.[candidate]);
    if (Number.isFinite(direct)) {
      return direct;
    }
  }
  return null;
}

function renderCodeBlock(ui, value, emptyLabel = 'Not stored in this artifact.') {
  const text = String(value || '').trim();
  return `<pre class="metric-details__code">${ui.escapeHtml(text || emptyLabel)}</pre>`;
}

function renderMetaGrid(ui, items) {
  const visibleItems = items.filter((item) => item.value != null && item.value !== '');
  if (!visibleItems.length) {
    return '';
  }
  return `
    <div class="metric-details__meta">
      ${visibleItems
        .map(
          (item) => `
            <div class="metric-details__meta-item">
              <strong>${ui.escapeHtml(item.label)}</strong>
              <span>${ui.escapeHtml(String(item.value))}</span>
            </div>
          `
        )
        .join('')}
    </div>
  `;
}

function renderProviderMetricDetail(ui, metricName, statistic = {}, metadata = {}, fallbackValue = null) {
  const label = metadata.display_name || metricName;
  const aggregator = String(statistic.aggregator || metadata.summary_aggregator || '');
  const resolvedValue = statistic.value ?? statistic.mean ?? (fallbackValue == null ? null : Number(fallbackValue));
  let formula = '';

  if (['corpus_rate', 'rate'].includes(aggregator) && statistic.denominator != null) {
    formula = `${label} = ${metricText(statistic.numerator ?? 0)} / ${metricText(statistic.denominator)} = ${metricText(resolvedValue)}`;
  } else if (aggregator === 'mean' && statistic.sum != null && statistic.count != null && Number(statistic.count) > 0) {
    formula = `${label} = ${metricText(statistic.sum)} / ${metricText(statistic.count)} = ${metricText(resolvedValue)}`;
  } else if (resolvedValue != null) {
    formula = `${label} = ${metricText(resolvedValue)}`;
  }

  const summaryBits = [];
  if (aggregator) {
    summaryBits.push(`aggregator: ${aggregator}`);
  }
  if (statistic.count != null) {
    summaryBits.push(`count: ${metricText(statistic.count)}`);
  }
  if (statistic.min != null && statistic.max != null) {
    summaryBits.push(`min/max: ${metricText(statistic.min)} / ${metricText(statistic.max)}`);
  }
  if (statistic.p95 != null) {
    summaryBits.push(`p95: ${metricText(statistic.p95)}`);
  }

  return `
    <div class="metric-details__section">
      <strong>${ui.escapeHtml(label)}</strong>
      ${metadata.description ? `<p class="helper">${ui.escapeHtml(metadata.description)}</p>` : ''}
      ${formula ? `<div class="metric-details__formula"><code>${ui.escapeHtml(formula)}</code></div>` : ''}
      ${summaryBits.length ? `<p class="helper">${ui.escapeHtml(summaryBits.join(' | '))}</p>` : ''}
    </div>
  `;
}

function renderWordTimeline(ui, row) {
  const words = Array.isArray(row.normalized_result?.words) ? row.normalized_result.words : [];
  if (!words.length) {
    return '';
  }
  return `
    <div class="metric-details__section">
      <strong>Word Timing</strong>
      <div class="metric-details__timeline">
        ${words
          .map((word) => {
            const timing = `${metricText(word.start_sec)}s -> ${metricText(word.end_sec)}s`;
            const confidence = word.confidence_available ? ` | conf ${metricText(word.confidence)}` : '';
            return `
              <div class="metric-details__word">
                <code>${ui.escapeHtml(word.word || '')}</code>
                <span>${ui.escapeHtml(`${timing}${confidence}`)}</span>
              </div>
            `;
          })
          .join('')}
      </div>
    </div>
  `;
}

function replayDefaultDuration(row) {
  const value = Number(row.audio_duration_sec);
  if (!Number.isFinite(value) || value <= 0) {
    return 5.0;
  }
  return Math.max(0.5, Math.min(value, 5.0));
}

const REPLAY_RANGE_STEP_SEC = 0.1;
const REPLAY_MIN_CLIP_SEC = 0.5;

function replayTotalDuration(row) {
  const value = Number(row.audio_duration_sec);
  if (Number.isFinite(value) && value > 0) {
    return value;
  }
  return Math.max(15.0, replayDefaultDuration(row));
}

function replayRangeDefaults(row) {
  const totalSec = replayTotalDuration(row);
  const minimumSpanSec = Math.min(REPLAY_MIN_CLIP_SEC, Math.max(REPLAY_RANGE_STEP_SEC, totalSec));
  const endSec = Math.min(totalSec, Math.max(minimumSpanSec, replayDefaultDuration(row)));
  return {
    totalSec,
    minimumSpanSec,
    startSec: 0.0,
    endSec,
  };
}

function formatReplaySeconds(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return '—';
  }
  return `${numeric.toFixed(1)} s`;
}

function replayDefaultNoiseMode(row) {
  const mode = String(row.noise_mode || '').trim().toLowerCase();
  return mode && mode !== 'none' ? mode : 'white';
}

function replayDefaultSnrDb(row) {
  const value = Number(row.noise_snr_db);
  return Number.isFinite(value) ? value : 20.0;
}

async function loadAudioBlobIntoPlayer(player, url, { statusNode, loadingText, readyText }) {
  if (!player) {
    return;
  }
  if (statusNode) {
    statusNode.textContent = loadingText;
  }
  const previousUrl = player.dataset.objectUrl || '';
  if (previousUrl) {
    URL.revokeObjectURL(previousUrl);
    delete player.dataset.objectUrl;
  }

  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try {
        const payload = await response.json();
        detail = payload?.detail || payload?.message || detail;
      } catch (_error) {
        // Keep fallback detail.
      }
      if (response.status === 404 && String(detail).trim() === 'Not Found') {
        detail = 'Replay endpoint is unavailable in the running gateway. Restart the web UI/gateway to load the latest API.';
      }
      throw new Error(detail);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    player.dataset.objectUrl = objectUrl;
    player.src = objectUrl;
    player.load();
    if (statusNode) {
      statusNode.textContent = readyText;
    }
  } catch (error) {
    player.removeAttribute('src');
    player.load();
    if (statusNode) {
      statusNode.textContent = error.message;
    }
  }
}

function renderReplaySection(ui, row, runId) {
  const replay = row.replay || {};
  if (replay.row_index == null || (!replay.has_evaluated_audio && !replay.has_clean_audio) || !runId) {
    return '';
  }
  const rangeDefaults = replayRangeDefaults(row);

  const sourceOptions = [];
  if (replay.has_evaluated_audio) {
    sourceOptions.push('<option value="evaluated">Evaluated input</option>');
  }
  if (replay.has_clean_audio) {
    sourceOptions.push(`<option value="clean"${replay.has_evaluated_audio ? '' : ' selected'}>Clean source</option>`);
  }

  return `
    <div class="metric-details__section result-replay" data-run-id="${ui.escapeHtml(runId)}" data-row-index="${ui.escapeHtml(String(replay.row_index))}">
      <strong>Audio Replay</strong>
      <p class="helper">Render a short clip from the evaluated input or the clean dataset source. Preview noise is generated on demand.</p>
      <div class="result-replay__controls">
        <label>
          Source
          <select class="result-replay__source">${sourceOptions.join('')}</select>
        </label>
        <label class="checkbox-line">
          <input class="result-replay__noise-enabled" type="checkbox" ${row.noise_level && row.noise_level !== 'clean' ? 'checked' : ''} />
          Preview with noise
        </label>
        <div
          class="result-replay__range-panel"
          data-total-sec="${ui.escapeHtml(rangeDefaults.totalSec.toFixed(1))}"
          data-min-span-sec="${ui.escapeHtml(rangeDefaults.minimumSpanSec.toFixed(1))}"
        >
          <div class="result-replay__range-head">
            <strong>Clip Range</strong>
            <code class="result-replay__range-value">${ui.escapeHtml(
              `${formatReplaySeconds(rangeDefaults.startSec)} -> ${formatReplaySeconds(rangeDefaults.endSec)} (${formatReplaySeconds(
                rangeDefaults.endSec - rangeDefaults.startSec
              )} clip)`
            )}</code>
          </div>
          <div class="result-replay__range-track" aria-hidden="true">
            <span class="result-replay__range-selection"></span>
          </div>
          <div class="result-replay__range-sliders">
            <label>
              Start
              <div class="result-replay__range-meta">
                <span class="helper">Clip begins</span>
                <code class="result-replay__start-value">${ui.escapeHtml(formatReplaySeconds(rangeDefaults.startSec))}</code>
              </div>
              <input
                class="result-replay__start"
                type="range"
                min="0"
                max="${ui.escapeHtml(rangeDefaults.totalSec.toFixed(1))}"
                step="${ui.escapeHtml(String(REPLAY_RANGE_STEP_SEC))}"
                value="${ui.escapeHtml(rangeDefaults.startSec.toFixed(1))}"
              />
            </label>
            <label>
              End
              <div class="result-replay__range-meta">
                <span class="helper">Clip ends</span>
                <code class="result-replay__end-value">${ui.escapeHtml(formatReplaySeconds(rangeDefaults.endSec))}</code>
              </div>
              <input
                class="result-replay__end"
                type="range"
                min="0"
                max="${ui.escapeHtml(rangeDefaults.totalSec.toFixed(1))}"
                step="${ui.escapeHtml(String(REPLAY_RANGE_STEP_SEC))}"
                value="${ui.escapeHtml(rangeDefaults.endSec.toFixed(1))}"
              />
            </label>
          </div>
        </div>
        <div class="result-replay__noise-controls">
          <label>
            Noise mode
            <select class="result-replay__noise-mode">
              ${['white', 'pink', 'brown', 'babble', 'hum']
                .map((mode) => `<option value="${ui.escapeHtml(mode)}"${mode === replayDefaultNoiseMode(row) ? ' selected' : ''}>${ui.escapeHtml(mode)}</option>`)
                .join('')}
            </select>
          </label>
          <label>
            SNR dB
            <input class="result-replay__snr" type="number" min="-5" max="60" step="0.1" value="${ui.escapeHtml(
              replayDefaultSnrDb(row).toFixed(1)
            )}" />
          </label>
        </div>
      </div>
      <div class="actions-row">
        <button type="button" class="btn-secondary result-replay__load">Load Replay</button>
      </div>
      <audio class="result-replay__player" controls preload="none"></audio>
      <p class="helper result-replay__status">Replay is generated on demand from stored artifacts.</p>
    </div>
  `;
}

function renderProviderInspector(ui, row, metricMetadata = {}) {
  const metricStatistics = row.metric_statistics || {};
  const orderedMetrics = [
    'wer',
    'cer',
    'sample_accuracy',
    'provider_compute_latency_ms',
    'end_to_end_latency_ms',
    'total_latency_ms',
    'provider_compute_rtf',
    'end_to_end_rtf',
    'real_time_factor',
    'time_to_first_result_ms',
    'time_to_final_result_ms',
    'success_rate',
    'failure_rate',
    'estimated_cost_usd',
    'finalization_latency_ms',
    'partial_count',
  ];
  return `
    <div class="stack-item">
      <strong>${ui.escapeHtml(providerLabel(row))}</strong>
      <p class="muted">samples=${ui.escapeHtml(String(row.total_samples || 0))} · warnings=${ui.escapeHtml(String(row.warning_samples || 0))}</p>
      ${renderMetaGrid(ui, [
        { label: 'WER', value: metricText(metricValue(row, 'wer')) },
        { label: 'CER', value: metricText(metricValue(row, 'cer')) },
        { label: 'Latency ms', value: metricText(metricValue(row, 'end_to_end_latency_ms', ['total_latency_ms'])) },
        { label: 'RTF', value: metricText(metricValue(row, 'end_to_end_rtf', ['real_time_factor'])) },
        { label: 'Cost USD', value: metricText(metricValue(row, 'estimated_cost_usd'), 4) },
      ])}
    </div>
    <div class="metric-details__body">
      ${orderedMetrics
        .filter((metricName) => metricStatistics[metricName] || metricValue(row, metricName) != null)
        .map((metricName) =>
          renderProviderMetricDetail(
            ui,
            metricName,
            metricStatistics[metricName] || {},
            metricMetadata[metricName] || {},
            metricValue(row, metricName)
          )
        )
        .join('')}
    </div>
  `;
}

function renderSampleInspector(ui, api, row, runId) {
  const support = getQualitySupport(row);
  const metrics = row.metrics || {};
  const diffRows = support
    ? [
        { label: 'Word edits', value: support.word_edits },
        { label: 'Reference words', value: support.reference_word_count },
        { label: 'Character edits', value: support.char_edits },
        { label: 'Reference chars', value: support.reference_char_count },
      ]
    : [];
  return `
    <div class="stack-item">
      <strong>${ui.escapeHtml(row.sample_id || 'sample')}</strong>
      <p>${ui.escapeHtml(providerLabel(row))}</p>
      <p class="muted">noise=${ui.escapeHtml(noiseLabel(row))}</p>
      ${renderMetaGrid(ui, [
        { label: 'WER', value: metricText(metrics.wer) },
        { label: 'CER', value: metricText(metrics.cer) },
        { label: 'Latency ms', value: metricText(firstPresent(metrics.end_to_end_latency_ms, metrics.time_to_final_result_ms, metrics.total_latency_ms)) },
        { label: 'RTF', value: metricText(firstPresent(metrics.end_to_end_rtf, metrics.real_time_factor)) },
        { label: 'Success', value: String(Boolean(row.success)) },
      ])}
    </div>
    <div class="stack-item">
      <strong>Transcript diff</strong>
      <p class="helper">Reference transcript used for quality metrics.</p>
      ${renderCodeBlock(ui, row.reference_text)}
      <p class="helper">Recognized transcript stored in benchmark results.</p>
      ${renderCodeBlock(ui, row.text)}
      ${support ? `<p class="helper">normalized reference=${ui.escapeHtml(support.normalized_reference || '')}</p>` : ''}
      ${support ? `<p class="helper">normalized hypothesis=${ui.escapeHtml(support.normalized_hypothesis || '')}</p>` : ''}
    </div>
    ${
      support
        ? `
          <div class="stack-item">
            <strong>WER / CER Breakdown</strong>
            ${renderMetaGrid(ui, diffRows)}
            <div class="metric-details__section">
              <code>WER = ${ui.escapeHtml(metricText(support.word_edits))} / ${ui.escapeHtml(metricText(support.reference_word_count))} = ${ui.escapeHtml(metricText(support.wer))}</code>
            </div>
            <div class="metric-details__section">
              <code>CER = ${ui.escapeHtml(metricText(support.char_edits))} / ${ui.escapeHtml(metricText(support.reference_char_count))} = ${ui.escapeHtml(metricText(support.cer))}</code>
            </div>
          </div>
        `
        : ''
    }
    <div class="stack-item">
      <strong>Sample metadata</strong>
      ${renderMetaGrid(ui, [
        { label: 'Execution', value: row.execution_mode || 'batch' },
        { label: 'Streaming', value: row.streaming_mode || 'none' },
        { label: 'Audio Sec', value: metricText(row.audio_duration_sec) },
        { label: 'Provider ms', value: metricText(firstPresent(metrics.provider_compute_latency_ms, metrics.total_latency_ms)) },
        { label: 'Confidence', value: row.normalized_result?.confidence_available ? metricText(row.normalized_result?.confidence) : 'n/a' },
        { label: 'Language', value: row.normalized_result?.language || 'n/a' },
      ])}
    </div>
    ${renderReplaySection(ui, row, runId)}
    ${renderWordTimeline(ui, row)}
  `;
}

function bindReplayControls(root, api) {
  root.querySelectorAll('.result-replay').forEach((container) => {
    const sourceSelect = container.querySelector('.result-replay__source');
    const rangePanel = container.querySelector('.result-replay__range-panel');
    const startInput = container.querySelector('.result-replay__start');
    const endInput = container.querySelector('.result-replay__end');
    const rangeValue = container.querySelector('.result-replay__range-value');
    const startValue = container.querySelector('.result-replay__start-value');
    const endValue = container.querySelector('.result-replay__end-value');
    const noiseEnabled = container.querySelector('.result-replay__noise-enabled');
    const noiseControls = container.querySelector('.result-replay__noise-controls');
    const noiseModeSelect = container.querySelector('.result-replay__noise-mode');
    const snrInput = container.querySelector('.result-replay__snr');
    const loadButton = container.querySelector('.result-replay__load');
    const player = container.querySelector('.result-replay__player');
    const status = container.querySelector('.result-replay__status');

    if (
      !sourceSelect ||
      !rangePanel ||
      !startInput ||
      !endInput ||
      !rangeValue ||
      !startValue ||
      !endValue ||
      !noiseEnabled ||
      !noiseControls ||
      !noiseModeSelect ||
      !snrInput ||
      !loadButton ||
      !player ||
      !status
    ) {
      return;
    }

    const totalSec = Math.max(REPLAY_RANGE_STEP_SEC, Number(rangePanel.dataset.totalSec) || 0);
    const minimumSpanSec = Math.min(totalSec, Math.max(REPLAY_RANGE_STEP_SEC, Number(rangePanel.dataset.minSpanSec) || REPLAY_MIN_CLIP_SEC));

    const syncRangeState = (changedControl = 'start') => {
      let startSec = Number(startInput.value);
      let endSec = Number(endInput.value);

      if (!Number.isFinite(startSec)) {
        startSec = 0.0;
      }
      if (!Number.isFinite(endSec)) {
        endSec = totalSec;
      }

      startSec = Math.max(0.0, Math.min(startSec, totalSec));
      endSec = Math.max(0.0, Math.min(endSec, totalSec));

      if (totalSec > minimumSpanSec && endSec - startSec < minimumSpanSec) {
        if (changedControl === 'end') {
          startSec = Math.max(0.0, endSec - minimumSpanSec);
        } else {
          endSec = Math.min(totalSec, startSec + minimumSpanSec);
        }
      }

      if (endSec < startSec) {
        if (changedControl === 'end') {
          startSec = endSec;
        } else {
          endSec = startSec;
        }
      }

      if (totalSec <= minimumSpanSec) {
        startSec = 0.0;
        endSec = totalSec;
      }

      startInput.value = startSec.toFixed(1);
      endInput.value = endSec.toFixed(1);

      const startPercent = totalSec > 0 ? (startSec / totalSec) * 100 : 0;
      const endPercent = totalSec > 0 ? (endSec / totalSec) * 100 : 100;
      rangePanel.style.setProperty('--range-start', `${startPercent}%`);
      rangePanel.style.setProperty('--range-end', `${endPercent}%`);
      rangeValue.textContent = `${formatReplaySeconds(startSec)} -> ${formatReplaySeconds(endSec)} (${formatReplaySeconds(endSec - startSec)} clip)`;
      startValue.textContent = formatReplaySeconds(startSec);
      endValue.textContent = formatReplaySeconds(endSec);
    };

    const syncNoiseControls = () => {
      noiseControls.hidden = !noiseEnabled.checked;
    };

    const buildReplayUrl = () =>
      api.resultsReplayAudioUrl(container.dataset.runId, container.dataset.rowIndex, {
        source: sourceSelect.value || 'evaluated',
        start_sec: startInput.value || '0',
        duration_sec: Math.max(
          REPLAY_RANGE_STEP_SEC,
          (Number(endInput.value) || totalSec) - (Number(startInput.value) || 0.0)
        ).toFixed(1),
        noise_mode: noiseEnabled.checked ? noiseModeSelect.value || 'white' : null,
        snr_db: noiseEnabled.checked ? snrInput.value || '20' : null,
      });

    noiseEnabled.addEventListener('change', syncNoiseControls);
    startInput.addEventListener('input', () => {
      syncRangeState('start');
    });
    endInput.addEventListener('input', () => {
      syncRangeState('end');
    });
    syncRangeState('start');
    syncNoiseControls();

    loadButton.addEventListener('click', () => {
      void loadAudioBlobIntoPlayer(player, buildReplayUrl(), {
        statusNode: status,
        loadingText: 'Loading replay clip...',
        readyText: `Replay ready: ${sourceSelect.value || 'evaluated'} source`,
      });
    });
  });
}

export function initResultsPage(ctx) {
  const { api, ui, state } = ctx;

  const overviewRoot = document.getElementById('resultsOverview');
  const runSelect = document.getElementById('resultsRunSelect');
  const runDetailRoot = document.getElementById('resultsRunDetail');
  const chartDeckRoot = document.getElementById('resultsChartDeck');
  const providerTableRoot = document.getElementById('resultsProviderTable');
  const inspectorRoot = document.getElementById('resultsInspector');
  const sampleFiltersRoot = document.getElementById('resultsSampleFilters');
  const sampleBucketCardsRoot = document.getElementById('resultsSampleBucketCards');
  const sampleTableRoot = document.getElementById('resultsSampleTable');
  const samplePagerRoot = document.getElementById('resultsSamplePager');
  const compareInput = document.getElementById('resultsCompareRuns');
  const compareMetricSelect = document.getElementById('resultsComparisonMetric');
  const compareChartRoot = document.getElementById('resultsComparisonChart');
  const compareRoot = document.getElementById('resultsComparisonTable');

  let recentRuns = [];

  function renderInspectorEmpty(message = 'Select a provider or sample row to inspect formulas, transcript diffs, timing, and replay.') {
    inspectorRoot.innerHTML = `<div class="stack-item inspector-empty"><strong>Inspector</strong><p>${ui.escapeHtml(message)}</p></div>`;
  }

  function setInspector(kind, payload) {
    state.results.selectedInspector = { kind, payload };
    const detail = state.results.lastDetail;
    if (!detail) {
      renderInspectorEmpty();
      return;
    }
    if (kind === 'provider') {
      inspectorRoot.innerHTML = renderProviderInspector(ui, payload, detail.summary?.metric_metadata || {});
      return;
    }
    if (kind === 'sample') {
      inspectorRoot.innerHTML = renderSampleInspector(ui, api, payload, detail.run_id || '');
      bindReplayControls(inspectorRoot, api);
      return;
    }
    renderInspectorEmpty();
  }

  function renderOverview(payload) {
    recentRuns = payload.recent_runs || [];
    overviewRoot.innerHTML = ui.statCards([
      {
        label: 'Latest Completed',
        value: payload.latest_completed?.run_id || 'none',
        badge: payload.latest_completed?.state || 'unknown',
        tone: payload.latest_completed?.state || 'unknown',
        hint: 'Most recent completed run ready for analysis',
      },
      {
        label: 'Recent Runs',
        value: String(recentRuns.length),
        badge: 'history',
        tone: 'info',
        hint: 'Stored under artifacts/benchmark_runs',
      },
      {
        label: 'Comparison Ready',
        value: String((payload.comparison_ready_runs || []).length),
        badge: 'compare',
        tone: 'ok',
        hint: 'Can be used for cross-run metric charts',
      },
    ]);
    ui.updateSelectOptions(
      runSelect,
      recentRuns.map((row) => row.run_id),
      state.results.selectedRunId || recentRuns[0]?.run_id || ''
    );
  }

  function renderRunOverview(detail) {
    const summary = detail.summary || {};
    const runManifest = detail.run_manifest || {};
    const bestProvider = (summary.provider_tradeoff_snapshot || [])[0];
    runDetailRoot.innerHTML = `
      ${ui.statCards([
        {
          label: 'Run',
          value: detail.run_id || 'unknown',
          badge: detail.state || 'unknown',
          tone: detail.state || 'unknown',
          hint: 'Current result workspace',
        },
        {
          label: 'Samples',
          value: String(summary.total_samples || detail.results_count || 0),
          badge: `${summary.successful_samples || 0} ok / ${summary.failed_samples || 0} failed`,
          tone: summary.failed_samples ? 'warning' : 'ok',
          hint: 'Stored rows in this run',
        },
        {
          label: 'Providers',
          value: String((summary.provider_summaries || []).length || 0),
          badge: summary.execution_mode || runManifest.execution_mode || 'batch',
          tone: 'info',
          hint: 'Provider comparison scope',
        },
        {
          label: 'Noise',
          value: (summary.noise_modes || []).join(', ') || 'none',
          badge: (summary.noise_levels || []).join(', ') || 'clean',
          tone: (summary.noise_levels || []).length > 1 ? 'warning' : 'ok',
          hint: 'Noise modes and levels in this run',
        },
      ])}
      <div class="stack-item">
        <strong>Run context</strong>
        <p>benchmark_profile=${ui.escapeHtml(runManifest.benchmark_profile || summary.benchmark_profile || '')}</p>
        <p>dataset_profile=${ui.escapeHtml(runManifest.dataset_profile || '')}</p>
        <p>scenario=${ui.escapeHtml(runManifest.scenario || summary.scenario || '')}</p>
        <p>metrics_semantics=${ui.escapeHtml(String(summary.metrics_semantics_version || 1))}${summary.legacy_metrics ? ' · legacy' : ''}</p>
      </div>
      ${
        bestProvider
          ? `
            <div class="stack-item">
              <strong>Current best tradeoff</strong>
              <p>${ui.escapeHtml(providerLabel(bestProvider))}</p>
              <p class="muted">wer=${ui.escapeHtml(metricText(bestProvider.wer))} · latency=${ui.escapeHtml(metricText(bestProvider.end_to_end_latency_ms))} ms · cost=${ui.escapeHtml(metricText(bestProvider.estimated_cost_usd, 4))}</p>
            </div>
          `
          : ''
      }
      <div class="stack-item">
        <strong>Artifacts</strong>
        <p class="helper">${ui.escapeHtml(JSON.stringify(detail.artifacts || {}, null, 2))}</p>
      </div>
    `;
  }

  function renderChartDeck(detail) {
    const analysis = detail.analysis || {};
    const charts = [];
    charts.push(renderRankingBars(ui, analysis.provider_rankings || []));
    charts.push(renderTradeoffScatter(ui, analysis.tradeoff_points || []));
    charts.push(renderLatencyStacks(ui, analysis.latency_breakdown || []));
    charts.push(renderNoiseHeatmap(ui, analysis.provider_noise_matrix || [], 'wer'));
    chartDeckRoot.innerHTML = charts.join('');
  }

  function renderProviderTable(detail) {
    const summary = detail.summary || {};
    const rows = summary.provider_summaries || [];
    if (!rows.length) {
      providerTableRoot.innerHTML = ui.renderEmpty('No per-provider summary available for this run.');
      return;
    }
    providerTableRoot.innerHTML = ui.table(
      [
        { key: 'provider', label: 'Provider', value: (row) => ui.escapeHtml(providerLabel(row)) },
        { key: 'samples', label: 'Samples', value: (row) => ui.escapeHtml(metricText(row.total_samples)) },
        { key: 'wer', label: 'WER', value: (row) => ui.escapeHtml(metricText(metricValue(row, 'wer'))) },
        { key: 'cer', label: 'CER', value: (row) => ui.escapeHtml(metricText(metricValue(row, 'cer'))) },
        {
          key: 'exact',
          label: 'Exact Match',
          value: (row) => ui.escapeHtml(metricText(metricValue(row, 'sample_accuracy'))),
        },
        {
          key: 'latency',
          label: 'End-to-End ms',
          value: (row) => ui.escapeHtml(metricText(metricValue(row, 'end_to_end_latency_ms', ['total_latency_ms']))),
        },
        {
          key: 'rtf',
          label: 'RTF',
          value: (row) => ui.escapeHtml(metricText(metricValue(row, 'end_to_end_rtf', ['real_time_factor']))),
        },
        {
          key: 'cost',
          label: 'Cost USD',
          value: (row) => ui.escapeHtml(metricText(metricValue(row, 'estimated_cost_usd'), 4)),
        },
      ],
      rows,
      [{ id: 'inspect_provider', label: 'Inspect', rowKey: (row) => row.provider_key || providerLabel(row) }],
      { className: 'table--compact', stickyFirstColumn: true }
    );

    providerTableRoot.querySelectorAll('button[data-action="inspect_provider"]').forEach((button) => {
      button.addEventListener('click', () => {
        const key = button.getAttribute('data-row');
        const row = rows.find((item) => (item.provider_key || providerLabel(item)) === key);
        if (row) {
          setInspector('provider', row);
        }
      });
    });
  }

  function renderSampleBucketCards(detail) {
    const buckets = detail.analysis?.sample_error_buckets?.bucket_cards || [];
    sampleBucketCardsRoot.innerHTML = buckets.length
      ? ui.statCards(
          buckets.map((bucket) => ({
            label: bucket.label,
            value: String(bucket.count || 0),
            badge: bucket.id,
            tone: bucket.tone || 'info',
            hint: 'Sample explorer quick signal',
          }))
        )
      : '';
  }

  function renderSampleFilters(detail, rowsPayload) {
    const filters = rowsPayload?.available_filters || {};
    const explorer = state.results.explorer;
    sampleFiltersRoot.innerHTML = `
      <label>
        Provider
        <select id="resultsFilterProvider">
          <option value="">all</option>
          ${(filters.providers || []).map((value) => `<option value="${ui.escapeHtml(value)}"${value === explorer.provider ? ' selected' : ''}>${ui.escapeHtml(value)}</option>`).join('')}
        </select>
      </label>
      <label>
        Preset
        <select id="resultsFilterPreset">
          <option value="">all</option>
          ${(filters.presets || []).map((value) => `<option value="${ui.escapeHtml(value)}"${value === explorer.preset ? ' selected' : ''}>${ui.escapeHtml(value)}</option>`).join('')}
        </select>
      </label>
      <label>
        Noise
        <select id="resultsFilterNoise">
          <option value="">all</option>
          ${(filters.noise || []).map((value) => `<option value="${ui.escapeHtml(value)}"${value === explorer.noise ? ' selected' : ''}>${ui.escapeHtml(value)}</option>`).join('')}
        </select>
      </label>
      <label>
        Success
        <select id="resultsFilterSuccess">
          <option value="">all</option>
          <option value="true"${explorer.success === 'true' ? ' selected' : ''}>true</option>
          <option value="false"${explorer.success === 'false' ? ' selected' : ''}>false</option>
        </select>
      </label>
      <label>
        Search
        <input id="resultsFilterSearch" value="${ui.escapeHtml(explorer.search || '')}" placeholder="sample id, transcript, error code" />
      </label>
      <label>
        Sort
        <select id="resultsFilterSort">
          ${[
            ['sample_id', 'sample_id'],
            ['provider', 'provider'],
            ['noise', 'noise'],
            ['success', 'success'],
            ['wer', 'wer'],
            ['cer', 'cer'],
            ['end_to_end_latency_ms', 'latency'],
            ['estimated_cost_usd', 'cost'],
          ]
            .map(([value, label]) => `<option value="${ui.escapeHtml(value)}"${explorer.sort === value ? ' selected' : ''}>${ui.escapeHtml(label)}</option>`)
            .join('')}
        </select>
      </label>
      <label>
        Direction
        <select id="resultsFilterDirection">
          <option value="asc"${explorer.direction === 'asc' ? ' selected' : ''}>asc</option>
          <option value="desc"${explorer.direction === 'desc' ? ' selected' : ''}>desc</option>
        </select>
      </label>
    `;

    const controls = [
      'resultsFilterProvider',
      'resultsFilterPreset',
      'resultsFilterNoise',
      'resultsFilterSuccess',
      'resultsFilterSort',
      'resultsFilterDirection',
    ];
    controls.forEach((id) => {
      document.getElementById(id)?.addEventListener('change', () => {
        state.results.explorer.page = 1;
        state.results.explorer.provider = document.getElementById('resultsFilterProvider')?.value || '';
        state.results.explorer.preset = document.getElementById('resultsFilterPreset')?.value || '';
        state.results.explorer.noise = document.getElementById('resultsFilterNoise')?.value || '';
        state.results.explorer.success = document.getElementById('resultsFilterSuccess')?.value || '';
        state.results.explorer.sort = document.getElementById('resultsFilterSort')?.value || 'sample_id';
        state.results.explorer.direction = document.getElementById('resultsFilterDirection')?.value || 'asc';
        void loadSampleExplorer(detail.run_id);
      });
    });
    document.getElementById('resultsFilterSearch')?.addEventListener('change', () => {
      state.results.explorer.page = 1;
      state.results.explorer.search = document.getElementById('resultsFilterSearch')?.value || '';
      void loadSampleExplorer(detail.run_id);
    });
  }

  function renderSampleTable(detail, rowsPayload) {
    const rows = rowsPayload?.items || [];
    if (!rows.length) {
      sampleTableRoot.innerHTML = ui.renderEmpty('No sample rows match the current filters.');
      samplePagerRoot.innerHTML = '';
      return;
    }
    sampleTableRoot.innerHTML = ui.table(
      [
        { key: 'provider', label: 'Provider', value: (row) => ui.escapeHtml(providerLabel(row)) },
        { key: 'sample', label: 'Sample', value: (row) => ui.escapeHtml(row.sample_id || '—') },
        {
          key: 'noise',
          label: 'Noise',
          value: (row) => ui.escapeHtml(noiseLabel(row)),
        },
        {
          key: 'success',
          label: 'Success',
          value: (row) => ui.badge(String(Boolean(row.success)), row.success ? 'ok' : 'error'),
        },
        { key: 'wer', label: 'WER', value: (row) => ui.escapeHtml(metricText(metricValue(row, 'wer'))) },
        { key: 'cer', label: 'CER', value: (row) => ui.escapeHtml(metricText(metricValue(row, 'cer'))) },
        {
          key: 'latency',
          label: 'Latency ms',
          value: (row) =>
            ui.escapeHtml(metricText(metricValue(row, 'end_to_end_latency_ms', ['time_to_final_result_ms', 'total_latency_ms']))),
        },
        { key: 'text', label: 'Text', value: (row) => ui.escapeHtml(row.text || '') },
      ],
      rows,
      [{ id: 'inspect_sample', label: 'Inspect', rowKey: (row) => String(row.row_index) }],
      { className: 'table--compact', stickyFirstColumn: true }
    );
    sampleTableRoot.querySelectorAll('button[data-action="inspect_sample"]').forEach((button) => {
      button.addEventListener('click', () => {
        const rowIndex = Number(button.getAttribute('data-row'));
        const row = rows.find((item) => Number(item.row_index) === rowIndex);
        if (row) {
          setInspector('sample', row);
        }
      });
    });

    const page = Number(rowsPayload.page || 1);
    const pageSize = Number(rowsPayload.page_size || 25);
    const total = Number(rowsPayload.total || 0);
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    samplePagerRoot.className = 'actions-row sample-pager';
    samplePagerRoot.innerHTML = `
      <button id="resultsSamplePrev" class="btn-secondary" ${page <= 1 ? 'disabled' : ''}>Previous</button>
      <span class="muted">page ${ui.escapeHtml(String(page))} / ${ui.escapeHtml(String(totalPages))} · ${ui.escapeHtml(String(total))} row(s)</span>
      <button id="resultsSampleNext" class="btn-secondary" ${page >= totalPages ? 'disabled' : ''}>Next</button>
    `;
    document.getElementById('resultsSamplePrev')?.addEventListener('click', () => {
      state.results.explorer.page = Math.max(1, page - 1);
      void loadSampleExplorer(detail.run_id);
    });
    document.getElementById('resultsSampleNext')?.addEventListener('click', () => {
      state.results.explorer.page = Math.min(totalPages, page + 1);
      void loadSampleExplorer(detail.run_id);
    });
  }

  async function loadSampleExplorer(runId) {
    const detail = state.results.lastDetail;
    if (!runId || !detail) {
      return;
    }
    try {
      const rowsPayload = await api.resultsRunRows(runId, state.results.explorer);
      renderSampleFilters(detail, rowsPayload);
      renderSampleTable(detail, rowsPayload);
    } catch (error) {
      sampleTableRoot.innerHTML = ui.renderEmpty(`Sample explorer failed: ${error.message}`);
    }
  }

  async function loadRunDetail(runId) {
    if (!runId) {
      runDetailRoot.innerHTML = ui.renderEmpty('Select a run to inspect details.');
      chartDeckRoot.innerHTML = '';
      providerTableRoot.innerHTML = '';
      sampleTableRoot.innerHTML = '';
      renderInspectorEmpty();
      return;
    }
    try {
      const detail = await api.resultsRunDetail(runId);
      state.results.selectedRunId = runId;
      state.results.lastDetail = detail;
      renderRunOverview(detail);
      renderChartDeck(detail);
      renderProviderTable(detail);
      renderSampleBucketCards(detail);
      renderInspectorEmpty();
      await loadSampleExplorer(runId);
    } catch (error) {
      runDetailRoot.innerHTML = ui.renderEmpty(`Failed to load run detail: ${error.message}`);
      chartDeckRoot.innerHTML = '';
      providerTableRoot.innerHTML = '';
      sampleTableRoot.innerHTML = '';
      renderInspectorEmpty(`Failed to load run detail: ${error.message}`);
    }
  }

  function renderComparison(payload) {
    const tableRows = payload.table || [];
    if (!tableRows.length) {
      compareChartRoot.innerHTML = ui.renderEmpty('No comparable metrics found for selected runs.');
      compareRoot.innerHTML = '';
      compareMetricSelect.innerHTML = '';
      return;
    }
    const subjectIndex = Object.fromEntries((payload.subjects || []).map((item) => [item.entity_id, item]));
    compareMetricSelect.innerHTML = (payload.chart_series || [])
      .map((series) => `<option value="${ui.escapeHtml(series.metric)}">${ui.escapeHtml(series.display_name || series.metric)}</option>`)
      .join('');
    const selectedMetric = compareMetricSelect.value || payload.chart_series?.[0]?.metric || '';
    if (selectedMetric && compareMetricSelect.value !== selectedMetric) {
      compareMetricSelect.value = selectedMetric;
    }
    compareChartRoot.innerHTML = renderComparisonSeries(ui, payload.chart_series || [], selectedMetric);
    compareRoot.innerHTML = ui.table(
      [
        { key: 'metric', label: 'Metric', value: (row) => ui.escapeHtml(row.display_name || row.metric) },
        { key: 'preference', label: 'Preference', value: (row) => ui.escapeHtml(row.preference) },
        {
          key: 'best',
          label: 'Best',
          value: (row) => {
            if (!row.best_run) {
              return mutedLabel(ui, 'n/a');
            }
            const subject = subjectIndex[row.best_run] || {};
            return ui.badge(providerLabel(subject) || row.best_run, 'ok');
          },
        },
        {
          key: 'values',
          label: 'Values',
          value: (row) =>
            Object.entries(row.values || {})
              .map(([entityId, value]) => {
                const subject = subjectIndex[entityId] || {};
                return `<code>${ui.escapeHtml(providerLabel(subject) || entityId)}=${ui.escapeHtml(metricText(value))}</code>`;
              })
              .join('<br />'),
        },
      ],
      tableRows,
      null,
      { className: 'table--compact', stickyFirstColumn: true }
    );
  }

  async function runComparison() {
    const runIds = ui.parseCsvInput(compareInput.value);
    if (!runIds.length) {
      compareChartRoot.innerHTML = ui.renderEmpty('Enter one or more run IDs to compare.');
      compareRoot.innerHTML = '';
      return;
    }
    try {
      const payload = await api.resultsCompare({ run_ids: runIds, metrics: [] });
      state.results.lastComparison = payload;
      renderComparison(payload);
      ui.toast('Comparison completed', 'success');
    } catch (error) {
      compareChartRoot.innerHTML = ui.renderEmpty(`Comparison failed: ${error.message}`);
      compareRoot.innerHTML = '';
      ui.toast(`Comparison failed: ${error.message}`, 'error');
    }
  }

  async function exportComparison() {
    const runIds = ui.parseCsvInput(compareInput.value);
    if (!runIds.length) {
      ui.setFeedback('resultsExportFeedback', 'Enter run IDs before exporting.', 'error');
      return;
    }
    const formats = [];
    if (document.getElementById('resultsExportJson')?.checked) {
      formats.push('json');
    }
    if (document.getElementById('resultsExportCsv')?.checked) {
      formats.push('csv');
    }
    if (document.getElementById('resultsExportMd')?.checked) {
      formats.push('md');
    }
    try {
      const payload = await api.resultsExport({
        run_ids: runIds,
        formats,
        name: document.getElementById('resultsExportName')?.value || '',
      });
      ui.setFeedback('resultsExportFeedback', `Exported to ${payload.directory}`, 'success');
      ui.toast(`Export ready: ${payload.name}`, 'success');
    } catch (error) {
      ui.setFeedback('resultsExportFeedback', `Export failed: ${error.message}`, 'error');
      ui.toast(`Export failed: ${error.message}`, 'error');
    }
  }

  async function loadOverview() {
    const payload = await api.resultsOverview();
    renderOverview(payload);
  }

  document.getElementById('resultsLoadRunBtn')?.addEventListener('click', async () => {
    state.results.explorer.page = 1;
    await loadRunDetail(runSelect.value);
  });

  document.getElementById('resultsCompareBtn')?.addEventListener('click', () => {
    void runComparison();
  });

  document.getElementById('resultsExportBtn')?.addEventListener('click', () => {
    void exportComparison();
  });

  compareMetricSelect?.addEventListener('change', () => {
    if (state.results.lastComparison) {
      compareChartRoot.innerHTML = renderComparisonSeries(ui, state.results.lastComparison.chart_series || [], compareMetricSelect.value);
    }
  });

  return {
    refresh: async () => {
      await loadOverview();
      const runId = state.results.selectedRunId || runSelect.value || recentRuns[0]?.run_id || '';
      if (runId) {
        await loadRunDetail(runId);
      } else {
        renderInspectorEmpty();
      }
      if (state.results.lastComparison?.table?.length) {
        renderComparison(state.results.lastComparison);
      }
    },
    poll: loadOverview,
  };
}
