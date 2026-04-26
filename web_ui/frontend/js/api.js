// Tiny fetch wrapper used by all page modules. The browser never talks to ROS
// directly; everything flows through gateway HTTP endpoints defined here.
async function request(path, opts = {}) {
  const isFormData = opts.body instanceof FormData;
  const response = await fetch(path, {
    headers: isFormData
      ? { ...(opts.headers || {}) }
      : {
          'Content-Type': 'application/json',
          ...(opts.headers || {}),
        },
    ...opts,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (_err) {
    payload = null;
  }

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }
  return payload;
}

function jsonBody(value) {
  return JSON.stringify(value ?? {});
}

function formBody(entries) {
  // Use FormData for uploads like WAV samples and Google service-account files.
  const form = new FormData();
  Object.entries(entries || {}).forEach(([key, value]) => {
    if (value == null) {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => form.append(key, item));
      return;
    }
    form.append(key, value);
  });
  return form;
}

function buildPathWithQuery(path, params = {}) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value == null || value === '') {
      return;
    }
    search.set(key, String(value));
  });
  return search.size ? `${path}?${search.toString()}` : path;
}

export function createApiClient() {
  return {
    // Dashboard/system overview
    health: () => request('/api/health'),
    dashboard: () => request('/api/dashboard'),
    systemStatus: () => request('/api/system/status'),

    // Runtime control and live status
    runtimeStatus: () => request('/api/runtime/status'),
    runtimeLive: () => request('/api/runtime/live'),
    runtimeBackends: () => request('/api/runtime/backends'),
    runtimeSamples: () => request('/api/runtime/samples'),
    noiseCatalog: () => request('/api/noise/catalog'),
    runtimeUploadSample: (payload) => request('/api/runtime/upload_sample', { method: 'POST', body: formBody(payload) }),
    runtimeGenerateNoise: (payload) => request('/api/runtime/generate_noise', { method: 'POST', body: jsonBody(payload) }),
    runtimeStart: (payload) => request('/api/runtime/start', { method: 'POST', body: jsonBody(payload) }),
    runtimeStop: (payload) => request('/api/runtime/stop', { method: 'POST', body: jsonBody(payload) }),
    runtimeReconfigure: (payload) => request('/api/runtime/reconfigure', { method: 'POST', body: jsonBody(payload) }),
    runtimeRecognizeOnce: (payload) =>
      request('/api/runtime/recognize_once', { method: 'POST', body: jsonBody(payload) }),

    // Provider catalog/profile inspection
    providersCatalog: () => request('/api/providers/catalog'),
    providersProfiles: () => request('/api/providers/profiles'),
    providersValidate: (payload) => request('/api/providers/validate', { method: 'POST', body: jsonBody(payload) }),
    providersTest: (payload) => request('/api/providers/test', { method: 'POST', body: jsonBody(payload) }),
    providersImportHuggingFaceModel: (payload) =>
      request('/api/providers/huggingface/import_model', { method: 'POST', body: jsonBody(payload) }),

    // Generic profile browsing/editing
    profilesAll: () => request('/api/profiles'),
    profilesByType: (type, detailed = false) => request(`/api/profiles/${type}?detailed=${String(detailed)}`),
    profileDetail: (type, id) => request(`/api/profiles/${type}/${encodeURIComponent(id)}`),
    profileSave: (type, id, payload) =>
      request(`/api/profiles/${type}/${encodeURIComponent(id)}`, { method: 'PUT', body: jsonBody(payload) }),
    validateConfig: (payload) => request('/api/config/validate', { method: 'POST', body: jsonBody(payload) }),

    // Dataset import and registry
    datasetsList: () => request('/api/datasets'),
    datasetDetail: (id) => request(`/api/datasets/${encodeURIComponent(id)}`),
    datasetImport: (payload) => request('/api/datasets/import', { method: 'POST', body: jsonBody(payload) }),
    datasetImportUpload: (payload) =>
      request('/api/datasets/import_upload', { method: 'POST', body: formBody(payload) }),
    datasetRegister: (payload) => request('/api/datasets/register', { method: 'POST', body: jsonBody(payload) }),
    datasetValidateManifest: (payload) =>
      request('/api/datasets/validate_manifest', { method: 'POST', body: jsonBody(payload) }),

    // Benchmark execution and history
    benchmarkRun: (payload) => request('/api/benchmark/run', { method: 'POST', body: jsonBody(payload) }),
    benchmarkStatus: (runId) => request(`/api/benchmark/status/${encodeURIComponent(runId)}`),
    benchmarkHistory: (limit = 30) => request(`/api/benchmark/history?limit=${limit}`),
    benchmarkPreviewAudioUrl: (params = {}) => buildPathWithQuery('/api/benchmark/preview_audio', params),

    // Result browsing/comparison/export
    resultsOverview: () => request('/api/results/overview'),
    resultsRunDetail: (runId) => request(`/api/results/runs/${encodeURIComponent(runId)}`),
    resultsRunRows: (runId, params = {}) =>
      request(buildPathWithQuery(`/api/results/runs/${encodeURIComponent(runId)}/rows`, params)),
    resultsReplayAudioUrl: (runId, rowIndex, params = {}) =>
      buildPathWithQuery(`/api/results/runs/${encodeURIComponent(runId)}/rows/${encodeURIComponent(rowIndex)}/audio`, params),
    resultsCompare: (payload) => request('/api/results/compare', { method: 'POST', body: jsonBody(payload) }),
    resultsExport: (payload) => request('/api/results/export', { method: 'POST', body: jsonBody(payload) }),

    // Diagnostics and logs
    diagnosticsHealth: () => request('/api/diagnostics/health'),
    diagnosticsPreflight: () => request('/api/diagnostics/preflight'),
    diagnosticsIssues: () => request('/api/diagnostics/issues'),
    logs: (params) => {
      const search = new URLSearchParams(params);
      return request(`/api/logs?${search.toString()}`);
    },

    // Secret metadata and cloud auth helpers
    secretsRefs: () => request('/api/secrets/refs'),
    secretsSaveRef: (payload) => request('/api/secrets/refs', { method: 'POST', body: jsonBody(payload) }),
    secretsValidateRef: (payload) =>
      request('/api/secrets/validate', { method: 'POST', body: jsonBody(payload) }),
    secretsGoogleStatus: () => request('/api/secrets/google_service_account'),
    secretsGoogleUpload: (payload) =>
      request('/api/secrets/google_service_account/upload', { method: 'POST', body: formBody(payload) }),
    secretsGoogleClear: (payload) =>
      request('/api/secrets/google_service_account/clear', { method: 'POST', body: jsonBody(payload) }),
    secretsAzureEnv: () => request('/api/secrets/azure_env'),
    secretsAzureEnvSave: (payload) =>
      request('/api/secrets/azure_env', { method: 'POST', body: jsonBody(payload) }),
    secretsHuggingFaceStatus: (refName = 'huggingface_api_token') =>
      request(`/api/secrets/huggingface_token?ref_name=${encodeURIComponent(refName)}`),
    secretsHuggingFaceTokenSave: (payload) =>
      request('/api/secrets/huggingface_token', { method: 'POST', body: jsonBody(payload) }),
    secretsAwsSsoLoginStart: (payload) =>
      request('/api/secrets/aws_sso_login', { method: 'POST', body: jsonBody(payload) }),
    secretsAwsSsoLoginStatus: (jobId) =>
      request(`/api/secrets/aws_sso_login/${encodeURIComponent(jobId)}`),
    secretsAwsSsoLoginCancel: (jobId) =>
      request(`/api/secrets/aws_sso_login/${encodeURIComponent(jobId)}/cancel`, { method: 'POST', body: jsonBody({}) }),
    secretsLinkProvider: (payload) =>
      request('/api/secrets/link_provider', { method: 'POST', body: jsonBody(payload) }),

    // Artifact browser
    artifacts: () => request('/api/artifacts'),
  };
}
