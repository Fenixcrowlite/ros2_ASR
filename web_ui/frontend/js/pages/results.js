export function initResultsPage(ctx) {
  const { api, ui, state } = ctx;

  const overviewRoot = document.getElementById('resultsOverview');
  const runSelect = document.getElementById('resultsRunSelect');
  const runDetailRoot = document.getElementById('resultsRunDetail');
  const compareInput = document.getElementById('resultsCompareRuns');
  const compareRoot = document.getElementById('resultsComparisonTable');

  let recentRuns = [];

  function metricText(value) {
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
    return numeric.toFixed(4);
  }

  function fmtMetric(value) {
    return ui.escapeHtml(metricText(value));
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
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,
          dp[i][j - 1] + 1,
          dp[i - 1][j - 1] + cost
        );
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
    const referenceHasContent = normalizedReference.length > 0;
    const hypothesisHasContent = normalizedHypothesis.length > 0;
    const referenceWordCount = referenceWords.length;
    const referenceCharCount = referenceChars.length;
    const wordEdits = levenshtein(referenceWords, hypothesisWords);
    const charEdits = levenshtein(referenceChars, hypothesisChars);

    return {
      normalized_reference: normalizedReference,
      normalized_hypothesis: normalizedHypothesis,
      reference_has_content: referenceHasContent,
      hypothesis_has_content: hypothesisHasContent,
      reference_word_count: referenceWordCount,
      reference_char_count: referenceCharCount,
      word_edits: wordEdits,
      char_edits: charEdits,
      exact_match: referenceHasContent && normalizedReference === normalizedHypothesis,
      wer: referenceWordCount > 0 ? wordEdits / referenceWordCount : 0,
      cer: referenceCharCount > 0 ? charEdits / referenceCharCount : 0,
    };
  }

  function getQualitySupport(row) {
    const stored = row.quality_support;
    if (stored && typeof stored === 'object') {
      const normalizedReference = String(
        row.normalized_reference_text || stored.normalized_reference || normalizeQualityText(row.reference_text || '')
      );
      const normalizedHypothesis = String(
        row.normalized_hypothesis_text || stored.normalized_hypothesis || normalizeQualityText(row.text || '')
      );
      const referenceWords = normalizedReference ? normalizedReference.split(' ') : [];
      const hypothesisWords = normalizedHypothesis ? normalizedHypothesis.split(' ') : [];
      const referenceChars = Array.from(normalizedReference.replaceAll(' ', ''));
      const hypothesisChars = Array.from(normalizedHypothesis.replaceAll(' ', ''));
      const referenceHasContent = Boolean(
        stored.reference_has_content ?? (normalizedReference.length > 0)
      );
      const hypothesisHasContent = Boolean(
        stored.hypothesis_has_content ?? (normalizedHypothesis.length > 0)
      );
      const referenceWordCount = Number(stored.reference_word_count ?? referenceWords.length);
      const referenceCharCount = Number(stored.reference_char_count ?? referenceChars.length);
      const wordEdits = Number(stored.word_edits ?? levenshtein(referenceWords, hypothesisWords));
      const charEdits = Number(stored.char_edits ?? levenshtein(referenceChars, hypothesisChars));
      const hasStoredExactMatch = Object.prototype.hasOwnProperty.call(stored, 'exact_match');

      return {
        normalized_reference: normalizedReference,
        normalized_hypothesis: normalizedHypothesis,
        reference_has_content: referenceHasContent,
        hypothesis_has_content: hypothesisHasContent,
        reference_word_count: referenceWordCount,
        reference_char_count: referenceCharCount,
        word_edits: wordEdits,
        char_edits: charEdits,
        exact_match: hasStoredExactMatch
          ? Boolean(stored.exact_match)
          : referenceHasContent && normalizedReference === normalizedHypothesis,
        wer: referenceWordCount > 0 ? wordEdits / referenceWordCount : 0,
        cer: referenceCharCount > 0 ? charEdits / referenceCharCount : 0,
      };
    }

    if (!row.reference_text) {
      return null;
    }
    return buildQualitySupport(row.reference_text, row.text || '');
  }

  function renderCodeBlock(value, emptyLabel = 'Not stored in this artifact.') {
    const text = String(value || '').trim();
    return `<pre class="metric-details__code">${ui.escapeHtml(text || emptyLabel)}</pre>`;
  }

  function renderMetaGrid(items) {
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

  function renderProviderMetricDetail(metricName, statistic = {}, metadata = {}, fallbackValue = null) {
    const label = metadata.display_name || metricName;
    const aggregator = String(statistic.aggregator || metadata.summary_aggregator || '');
    const resolvedValue =
      statistic.value ?? statistic.mean ?? (fallbackValue == null ? null : Number(fallbackValue));
    let formula = '';

    if (['corpus_rate', 'rate'].includes(aggregator) && statistic.denominator != null) {
      formula = `${label} = ${metricText(statistic.numerator ?? 0)} / ${metricText(statistic.denominator)} = ${metricText(
        resolvedValue
      )}`;
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

  function renderProviderBreakdown(row, metricMetadata = {}) {
    const metricStatistics = row.metric_statistics || {};
    const meanMetrics = row.mean_metrics || {};
    const orderedMetrics = [
      'wer',
      'cer',
      'sample_accuracy',
      'total_latency_ms',
      'real_time_factor',
      'success_rate',
      'failure_rate',
      'estimated_cost_usd',
      'first_partial_latency_ms',
      'finalization_latency_ms',
      'partial_count',
    ];
    const metricNames = orderedMetrics.filter(
      (metricName) => metricStatistics[metricName] || meanMetrics[metricName] != null
    );

    if (!metricNames.length) {
      return '<span class="muted">n/a</span>';
    }

    return `
      <details class="metric-details">
        <summary>Breakdown</summary>
        <div class="metric-details__body">
          ${metricNames
            .map((metricName) =>
              renderProviderMetricDetail(
                metricName,
                metricStatistics[metricName] || {},
                metricMetadata[metricName] || {},
                meanMetrics[metricName]
              )
            )
            .join('')}
        </div>
      </details>
    `;
  }

  function renderWordTimeline(row) {
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

  function renderSampleBreakdown(row) {
    const support = getQualitySupport(row);
    const normalizedReference = String(row.normalized_reference_text || support?.normalized_reference || '');
    const normalizedHypothesis = String(row.normalized_hypothesis_text || support?.normalized_hypothesis || normalizeQualityText(row.text || ''));
    const referenceWords = normalizedReference ? normalizedReference.split(' ') : [];
    const hypothesisWords = normalizedHypothesis ? normalizedHypothesis.split(' ') : [];
    const referenceChars = normalizedReference.replaceAll(' ', '');
    const hypothesisChars = normalizedHypothesis.replaceAll(' ', '');

    return `
      <details class="metric-details">
        <summary>Inspect</summary>
        <div class="metric-details__body">
          <div class="metric-details__section">
            <strong>Transcript Pair</strong>
            <p class="helper">Reference transcript used for quality metrics.</p>
            ${renderCodeBlock(row.reference_text)}
            <p class="helper">Recognized transcript returned by the provider.</p>
            ${renderCodeBlock(row.text, 'Empty transcript.')}
          </div>
          ${
            support
              ? `
                <div class="metric-details__section">
                  <strong>Normalized Representation</strong>
                  <p class="helper">Lowercase + punctuation/symbol stripping before WER/CER.</p>
                  <p class="helper">reference_normalized</p>
                  ${renderCodeBlock(normalizedReference)}
                  <p class="helper">hypothesis_normalized</p>
                  ${renderCodeBlock(normalizedHypothesis, 'Empty transcript after normalization.')}
                </div>
                <div class="metric-details__section">
                  <strong>WER / CER Breakdown</strong>
                  <p class="helper">Calculated from the normalized texts above.</p>
                  <div class="metric-details__formula">
                    <code>${ui.escapeHtml(
                      `WER = word_edits / reference_word_count = ${metricText(support.word_edits)} / ${metricText(
                        support.reference_word_count
                      )} = ${metricText(support.wer)}`
                    )}</code>
                  </div>
                  <div class="metric-details__formula">
                    <code>${ui.escapeHtml(
                      `CER = char_edits / reference_char_count = ${metricText(support.char_edits)} / ${metricText(
                        support.reference_char_count
                      )} = ${metricText(support.cer)}`
                    )}</code>
                  </div>
                  ${renderMetaGrid([
                    { label: 'Exact Match', value: support.exact_match ? 'true' : 'false' },
                    { label: 'Word Edits', value: metricText(support.word_edits) },
                    { label: 'Word Count', value: metricText(support.reference_word_count) },
                    { label: 'Char Edits', value: metricText(support.char_edits) },
                    { label: 'Char Count', value: metricText(support.reference_char_count) },
                  ])}
                </div>
                <div class="metric-details__section">
                  <strong>Mathematical View</strong>
                  <p class="helper">word_vector(reference)</p>
                  ${renderCodeBlock(JSON.stringify(referenceWords))}
                  <p class="helper">word_vector(hypothesis)</p>
                  ${renderCodeBlock(JSON.stringify(hypothesisWords))}
                  <p class="helper">char_stream(reference)</p>
                  ${renderCodeBlock(referenceChars)}
                  <p class="helper">char_stream(hypothesis)</p>
                  ${renderCodeBlock(hypothesisChars, 'Empty transcript after normalization.')}
                </div>
              `
              : `
                <div class="metric-details__section">
                  <strong>WER / CER Breakdown</strong>
                  <p class="helper">
                    Reference transcript is missing in this stored row, so the exact WER/CER formula cannot be reconstructed here.
                  </p>
                </div>
              `
          }
          <div class="metric-details__section">
            <strong>ASR Metadata</strong>
            ${renderMetaGrid([
              { label: 'Execution', value: row.execution_mode || 'batch' },
              { label: 'Streaming', value: row.streaming_mode || 'none' },
              { label: 'Audio Sec', value: metricText(row.audio_duration_sec) },
              { label: 'Latency ms', value: metricText(row.metrics?.total_latency_ms ?? row.normalized_result?.latency?.total_ms) },
              { label: 'Confidence', value: row.normalized_result?.confidence_available ? metricText(row.normalized_result?.confidence) : 'n/a' },
              { label: 'Language', value: row.normalized_result?.language || 'n/a' },
            ])}
          </div>
          ${renderWordTimeline(row)}
        </div>
      </details>
    `;
  }

  function renderProviderSummaryTable(summary = {}) {
    const providerSummaries = summary.provider_summaries || [];
    if (!providerSummaries.length) {
      return ui.renderEmpty('No per-provider summary available for this run.');
    }

    return ui.table(
      [
        {
          key: 'provider',
          label: 'Provider',
          value: (row) => ui.escapeHtml(row.provider_profile || row.provider_id || row.provider_key || 'unknown'),
        },
        {
          key: 'preset',
          label: 'Preset',
          value: (row) => ui.escapeHtml(row.provider_preset || 'default'),
        },
        { key: 'samples', label: 'Samples', value: (row) => fmtMetric(row.total_samples) },
        { key: 'success', label: 'Success', value: (row) => fmtMetric(row.successful_samples) },
        { key: 'failed', label: 'Failed', value: (row) => fmtMetric(row.failed_samples) },
        { key: 'wer', label: 'WER', value: (row) => fmtMetric(row.quality_metrics?.wer) },
        { key: 'cer', label: 'CER', value: (row) => fmtMetric(row.quality_metrics?.cer) },
        { key: 'acc', label: 'Exact Match Rate', value: (row) => fmtMetric(row.quality_metrics?.sample_accuracy) },
        { key: 'lat', label: 'Latency ms', value: (row) => fmtMetric(row.latency_metrics?.total_latency_ms) },
        { key: 'rtf', label: 'RTF', value: (row) => fmtMetric(row.latency_metrics?.real_time_factor) },
        { key: 'succ_rate', label: 'Success Rate', value: (row) => fmtMetric(row.reliability_metrics?.success_rate) },
        { key: 'fail_rate', label: 'Failure Rate', value: (row) => fmtMetric(row.reliability_metrics?.failure_rate) },
        { key: 'cost_mean', label: 'Mean Cost USD', value: (row) => fmtMetric(row.cost_metrics?.estimated_cost_usd) },
        {
          key: 'cost_total',
          label: 'Total Cost USD',
          value: (row) => fmtMetric(row.metric_statistics?.estimated_cost_usd?.sum),
        },
        {
          key: 'first_partial',
          label: 'First Partial ms',
          value: (row) => fmtMetric(row.streaming_metrics?.first_partial_latency_ms),
        },
        {
          key: 'finalization',
          label: 'Finalization ms',
          value: (row) => fmtMetric(row.streaming_metrics?.finalization_latency_ms),
        },
        {
          key: 'partials',
          label: 'Partial Count',
          value: (row) => fmtMetric(row.streaming_metrics?.partial_count),
        },
        {
          key: 'detail',
          label: 'Details',
          value: (row) => renderProviderBreakdown(row, summary.metric_metadata || {}),
        },
      ],
      providerSummaries
    );
  }

  function renderResultsHeadTable(detail = {}) {
    const rows = detail.results_head || [];
    if (!rows.length) {
      return ui.renderEmpty('No sample-level rows stored for this run.');
    }

    return ui.table(
      [
        {
          key: 'provider',
          label: 'Provider',
          value: (row) => ui.escapeHtml(row.provider_profile || row.provider_id || row.backend || 'unknown'),
        },
        {
          key: 'preset',
          label: 'Preset',
          value: (row) => ui.escapeHtml(row.provider_preset || 'default'),
        },
        {
          key: 'sample',
          label: 'Sample',
          value: (row) => ui.escapeHtml(row.sample_id || row.audio_id || '—'),
        },
        {
          key: 'success',
          label: 'Success',
          value: (row) =>
            `<span class="${ui.statusBadgeClass(row.success ? 'ok' : 'failed')}">${ui.escapeHtml(String(Boolean(row.success)))}</span>`,
        },
        {
          key: 'text',
          label: 'Result Text',
          value: (row) => ui.escapeHtml(row.text || ''),
        },
        { key: 'wer', label: 'WER', value: (row) => fmtMetric(row.metrics?.wer) },
        { key: 'cer', label: 'CER', value: (row) => fmtMetric(row.metrics?.cer) },
        { key: 'latency', label: 'Latency ms', value: (row) => fmtMetric(row.metrics?.total_latency_ms) },
        { key: 'rtf', label: 'RTF', value: (row) => fmtMetric(row.metrics?.real_time_factor) },
        { key: 'cost', label: 'Cost USD', value: (row) => fmtMetric(row.metrics?.estimated_cost_usd) },
        { key: 'error', label: 'Error', value: (row) => ui.escapeHtml(row.error_code || '') },
        {
          key: 'detail',
          label: 'Details',
          value: (row) => renderSampleBreakdown(row),
        },
      ],
      rows
    );
  }

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
        <div class="stack-item">
          <strong>Per-provider metrics</strong>
          <p class="helper">
            Each row is one provider/preset inside the run. Open Breakdown to inspect corpus-level numerators, denominators,
            and aggregators behind the summary metrics.
          </p>
          ${renderProviderSummaryTable(summary)}
        </div>
        <div class="stack-item">
          <strong>Sample results preview</strong>
          <p class="helper">
            Showing ${ui.escapeHtml(String(detail.results_head?.length || 0))} of ${ui.escapeHtml(String(detail.results_count || 0))}
            stored rows. Open Inspect to see reference text, normalized forms, WER/CER formula inputs, and word timing.
          </p>
          ${renderResultsHeadTable(detail)}
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
    const subjectIndex = Object.fromEntries((payload.subjects || []).map((item) => [item.entity_id, item]));

    compareRoot.innerHTML = ui.table(
      [
        { key: 'metric', label: 'Metric', value: (row) => ui.escapeHtml(row.metric) },
        { key: 'pref', label: 'Preference', value: (row) => ui.escapeHtml(row.preference) },
        {
          key: 'values',
          label: 'Values by Provider',
          value: (row) =>
            Object.entries(row.values || {})
              .map(([entityId, value]) => {
                const subject = subjectIndex[entityId] || {};
                const label = subject.provider_profile
                  ? `${subject.run_id} :: ${subject.provider_profile}${subject.provider_preset ? ` [${subject.provider_preset}]` : ''}`
                  : entityId;
                return `<code>${ui.escapeHtml(label)}=${ui.escapeHtml(String(value ?? 'n/a'))}</code>`;
              })
              .join('<br />'),
        },
        {
          key: 'best',
          label: 'Best Provider',
          value: (row) => {
            const subject = subjectIndex[row.best_run] || {};
            const label = subject.provider_profile
              ? `${subject.run_id} :: ${subject.provider_profile}${subject.provider_preset ? ` [${subject.provider_preset}]` : ''}`
              : row.best_run || '';
            return `<span class="${ui.statusBadgeClass('ok')}">${ui.escapeHtml(label)}</span>`;
          },
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
