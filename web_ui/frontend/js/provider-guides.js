// Provider-specific guidance snippets rendered by browser UI pages.
export function renderProviderGuideHtml(ui, row) {
  const providerId = String(row?.provider_id || '').trim();
  if (!providerId) {
    return '';
  }

  if (providerId === 'huggingface_local') {
    const sampleJson = '{"device":"cuda:0","torch_dtype":"float16","chunk_length_s":15.0}';
    return `
      <div class="stack-item">
        <strong>Hugging Face Local Guide</strong>
        <p>Runs local <code>transformers</code> ASR models through the unified adapter. Use this for offline or GPU-backed transcription.</p>
        <p class="muted">HF_TOKEN is optional here. Add it only when you need gated/private models or authenticated Hub downloads.</p>
        <p class="muted">Recommended advanced JSON: <code>${ui.escapeHtml(sampleJson)}</code></p>
      </div>
    `;
  }

  if (providerId === 'huggingface_api') {
    const sampleJson = '{"model_id":"openai/whisper-large-v3","timeout_sec":90,"generation_parameters":{}}';
    return `
      <div class="stack-item">
        <strong>Hugging Face API Guide</strong>
        <p>Uses the hosted Hugging Face inference endpoint over HTTP but keeps the same result contract as local mode.</p>
        <p class="muted">HF_TOKEN is required. Configure it on the Secrets page, then validate or test this provider profile.</p>
        <p class="muted">Recommended advanced JSON: <code>${ui.escapeHtml(sampleJson)}</code></p>
      </div>
    `;
  }

  return '';
}
