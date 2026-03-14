const STORAGE_SELECTED_JOB = "ros2ws_web_gui_selected_job";
const STORAGE_FORM_DRAFT = "ros2ws_web_gui_form_draft_v1";
const FORM_DRAFT_VERSION = 1;
const ACTIVE_JOB_STATUSES = new Set(["running"]);
const STATUS_CLASS_PREFIX = "status-";
const FORM_DRAFT_DEBOUNCE_MS = 350;

const state = {
  options: null,
  files: {
    uploads: [],
    noisy: [],
    results: [],
  },
  allJobs: [],
  jobs: [],
  hiddenJobs: [],
  selectedJobId: localStorage.getItem(STORAGE_SELECTED_JOB) || "",
  jobsPollTimer: null,
  filesPollTimer: null,
  jobsRefreshInFlight: false,
  filesRefreshInFlight: false,
  optionsRefreshInFlight: false,
};

let formDraftSaveTimer = null;

const $ = (id) => document.getElementById(id);

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function uniqueStrings(values) {
  return Array.from(
    new Set(
      (values || [])
        .map((item) => String(item || "").trim())
        .filter((item) => item.length > 0),
    ),
  );
}

function textValue(id) {
  const element = $(id);
  if (!element) {
    return "";
  }
  return String(element.value || "").trim();
}

function setTextValue(id, value) {
  const element = $(id);
  if (!element || value === undefined || value === null) {
    return;
  }
  element.value = String(value);
}

function intValue(id, fallback) {
  const raw = textValue(id);
  if (!raw) {
    return fallback;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function numberValue(id, fallback) {
  const raw = textValue(id);
  if (!raw) {
    return fallback;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function isChecked(id) {
  const element = $(id);
  return Boolean(element && element.checked);
}

function setChecked(id, checked) {
  const element = $(id);
  if (!element) {
    return;
  }
  element.checked = Boolean(checked);
}

function parseCommaList(raw) {
  return uniqueStrings(String(raw || "").split(",").map((item) => item.trim()));
}

function joinComma(values) {
  return uniqueStrings(values).join(",");
}

function fileExt(path) {
  const name = String(path || "").toLowerCase();
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index + 1) : "";
}

function fileBaseName(path) {
  const text = String(path || "");
  const normalized = text.replace(/\\/g, "/");
  const parts = normalized.split("/");
  return parts[parts.length - 1] || normalized;
}

function trimMiddle(text, maxLen = 56) {
  const value = String(text || "");
  if (value.length <= maxLen) {
    return value;
  }
  const keep = Math.max(8, Math.floor((maxLen - 3) / 2));
  return `${value.slice(0, keep)}...${value.slice(value.length - keep)}`;
}

function buildArtifactUrl(path) {
  return `/api/artifacts?path=${encodeURIComponent(String(path || ""))}`;
}

function removeStatusClasses(element) {
  if (!element) {
    return;
  }
  for (const className of Array.from(element.classList)) {
    if (className.startsWith(STATUS_CLASS_PREFIX)) {
      element.classList.remove(className);
    }
  }
}

function setStatusPill(status) {
  const pill = $("status-pill");
  if (!pill) {
    return;
  }
  const normalized = String(status || "idle").trim().toLowerCase() || "idle";
  removeStatusClasses(pill);
  pill.classList.add(`status-${normalized}`);
  pill.textContent = normalized;
}

function loadFormDraft() {
  const raw = localStorage.getItem(STORAGE_FORM_DRAFT);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      localStorage.removeItem(STORAGE_FORM_DRAFT);
      return null;
    }
    if (Number(parsed.version || 0) !== FORM_DRAFT_VERSION) {
      localStorage.removeItem(STORAGE_FORM_DRAFT);
      return null;
    }
    const payload = asObject(parsed.payload);
    if (!payload || Object.keys(payload).length === 0) {
      return null;
    }
    return payload;
  } catch (_err) {
    localStorage.removeItem(STORAGE_FORM_DRAFT);
    return null;
  }
}

function saveFormDraftNow() {
  const payload = buildProfileDocument();
  localStorage.setItem(
    STORAGE_FORM_DRAFT,
    JSON.stringify({
      version: FORM_DRAFT_VERSION,
      saved_at: new Date().toISOString(),
      payload,
    }),
  );
}

function scheduleFormDraftSave() {
  if (formDraftSaveTimer) {
    clearTimeout(formDraftSaveTimer);
  }
  formDraftSaveTimer = window.setTimeout(() => {
    formDraftSaveTimer = null;
    saveFormDraftNow();
  }, FORM_DRAFT_DEBOUNCE_MS);
}

function setBusy(button, busy, busyText = "Working...") {
  if (!button) {
    return;
  }
  if (busy) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent || "";
    }
    button.disabled = true;
    button.textContent = busyText;
    return;
  }
  button.disabled = false;
  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
    delete button.dataset.originalText;
  }
}

function showToast(message, type = "info", timeoutMs = 4200) {
  const stack = $("toast-stack");
  if (!stack) {
    return;
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = String(message || "");
  stack.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, timeoutMs);
}

async function apiRequest(path, options = {}) {
  const request = {
    method: options.method || "GET",
    headers: {},
  };

  if (options.body instanceof FormData) {
    request.body = options.body;
  } else if (options.body !== undefined) {
    request.headers["Content-Type"] = "application/json";
    request.body = JSON.stringify(options.body);
  }

  const response = await fetch(path, request);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      if (payload && payload.detail) {
        detail = String(payload.detail);
      }
    } catch (_err) {
      try {
        const text = await response.text();
        if (text.trim()) {
          detail = text.trim();
        }
      } catch (_ignored) {
        // no-op
      }
    }
    throw new Error(detail);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function normalizeOption(option) {
  if (option && typeof option === "object") {
    const value = String(option.value ?? option.id ?? "").trim();
    const label = String(option.label ?? option.name ?? value).trim();
    return { value, label };
  }
  const value = String(option ?? "").trim();
  return { value, label: value };
}

function fillDatalist(id, values) {
  const datalist = $(id);
  if (!datalist) {
    return;
  }
  datalist.innerHTML = "";
  for (const value of uniqueStrings(values)) {
    const option = document.createElement("option");
    option.value = value;
    datalist.appendChild(option);
  }
}

function fillSelect(id, values, config = {}) {
  const select = $(id);
  if (!select) {
    return;
  }

  const previousValue = String(select.value || "");
  const includeEmpty = Boolean(config.includeEmpty);
  const emptyLabel = String(config.emptyLabel || "");

  const normalized = [];
  for (const raw of values || []) {
    const option = normalizeOption(raw);
    if (!option.value) {
      continue;
    }
    normalized.push(option);
  }

  const known = new Set(normalized.map((item) => item.value));
  if (previousValue && !known.has(previousValue)) {
    normalized.unshift({ value: previousValue, label: previousValue });
  }

  select.innerHTML = "";

  if (includeEmpty) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = emptyLabel;
    select.appendChild(option);
  }

  for (const item of normalized) {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
    select.appendChild(option);
  }

  if (previousValue && Array.from(select.options).some((item) => item.value === previousValue)) {
    select.value = previousValue;
  }
}

function renderCheckboxGroup(containerId, values) {
  const container = $(containerId);
  if (!container) {
    return;
  }

  const previous = new Set(getCheckedValues(containerId));
  container.innerHTML = "";

  for (const value of uniqueStrings(values)) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = value;
    if (previous.has(value)) {
      input.checked = true;
    }
    label.appendChild(input);
    label.appendChild(document.createTextNode(value));
    container.appendChild(label);
  }
}

function getCheckedValues(containerId) {
  const container = $(containerId);
  if (!container) {
    return [];
  }
  return Array.from(container.querySelectorAll('input[type="checkbox"]:checked'))
    .map((item) => String(item.value || "").trim())
    .filter((item) => item.length > 0);
}

function setCheckedValues(containerId, values) {
  const target = new Set(uniqueStrings(Array.isArray(values) ? values : parseCommaList(values)));
  const container = $(containerId);
  if (!container) {
    return;
  }
  for (const checkbox of container.querySelectorAll('input[type="checkbox"]')) {
    checkbox.checked = target.has(String(checkbox.value || "").trim());
  }
}

function pruneValue(value) {
  if (value === undefined || value === null) {
    return undefined;
  }
  if (typeof value === "string") {
    const text = value.trim();
    return text ? text : undefined;
  }
  if (Array.isArray(value)) {
    const items = value
      .map((item) => pruneValue(item))
      .filter((item) => item !== undefined);
    return items.length > 0 ? items : undefined;
  }
  if (typeof value === "object") {
    const result = {};
    for (const [key, item] of Object.entries(value)) {
      const cleaned = pruneValue(item);
      if (cleaned !== undefined) {
        result[key] = cleaned;
      }
    }
    return Object.keys(result).length > 0 ? result : undefined;
  }
  return value;
}

function selectedAwsAuthProfile() {
  const selected = textValue("aws-auth-profile");
  if (selected) {
    return selected;
  }
  const typed = textValue("aws-auth-name");
  if (!typed) {
    return "";
  }
  const options = Array.from($("aws-auth-profile")?.options || []).map((item) => item.value);
  return options.includes(typed) ? typed : "";
}

function buildRuntimeOverrides() {
  const scenarios = parseCommaList(textValue("bench-scenarios"));
  const selectedMetrics = getCheckedValues("metric-select");

  const asr = {
    backend: textValue("asr-backend") || "mock",
    sample_rate: intValue("sample-rate", 16000),
    chunk_ms: intValue("chunk-ms", 800),
    input_mode: textValue("input-mode") || "auto",
  };

  const language = textValue("language");
  if (language) {
    asr.language = language;
  }

  const defaultWav = textValue("bringup-wav") || textValue("use-wav");
  if (defaultWav) {
    asr.wav_path = defaultWav;
  }

  const benchmark = {
    scenarios,
    chunk_sec: numberValue("bench-chunk-sec", 0.8),
    selected_metrics: selectedMetrics,
  };

  const overrides = {
    asr,
    benchmark,
    backends: {
      whisper: {
        model_size: textValue("whisper-model"),
        device: textValue("whisper-device"),
        compute_type: textValue("whisper-compute"),
      },
      vosk: {
        model_path: textValue("vosk-model-path"),
      },
      google: {
        model: textValue("google-model"),
      },
      aws: {
        region: textValue("aws-region"),
        s3_bucket: textValue("aws-bucket"),
      },
      azure: {
        region: textValue("azure-region"),
        endpoint: textValue("azure-endpoint"),
      },
    },
  };

  return pruneValue(overrides) || {};
}

function buildSecrets() {
  const secrets = {
    google_credentials_json: textValue("secret-google-cred"),
    google_project_id: textValue("secret-google-project"),
    aws_access_key_id: textValue("secret-aws-id"),
    aws_secret_access_key: textValue("secret-aws-secret"),
    aws_session_token: textValue("secret-aws-token"),
    aws_region: textValue("aws-region"),
    aws_s3_bucket: textValue("aws-bucket"),
    azure_speech_key: textValue("secret-azure-key"),
    azure_region: textValue("azure-region"),
    azure_endpoint: textValue("azure-endpoint"),
  };
  return pruneValue(secrets) || {};
}

function buildUnifiedPayload() {
  const payload = {
    interfaces: joinComma(getCheckedValues("interfaces")) || "core",
    model_runs: textValue("model-runs"),
    language_mode: textValue("language-mode") || "config",
    language: textValue("language"),
    reference_text: textValue("reference-text"),
    record_sec: numberValue("record-sec", 5),
    sample_rate: intValue("sample-rate", 16000),
    action_chunk_sec: numberValue("action-chunk-sec", 0.8),
    request_timeout_sec: numberValue("request-timeout", 25),
    ros_auto_launch: isChecked("ros-auto-launch"),
    action_streaming: isChecked("action-streaming"),
    use_wav: textValue("use-wav"),
    device: textValue("audio-device"),
    dataset: textValue("dataset"),
    backends: textValue("bench-backends"),
    scenarios: textValue("bench-scenarios"),
    bringup_input_mode: textValue("bringup-input-mode") || "mic",
    bringup_wav: textValue("bringup-wav"),
    bringup_mic_sec: numberValue("bringup-mic-sec", 4),
    bringup_continuous: isChecked("bringup-continuous"),
    bringup_live_enabled: isChecked("bringup-live-enabled"),
    bringup_text_enabled: isChecked("bringup-text-enabled"),
    noise_levels: textValue("noise-levels"),
    aws_auth_profile: selectedAwsAuthProfile(),
  };
  return pruneValue(payload) || {};
}

function buildLivePayload() {
  const source = buildUnifiedPayload();
  const payload = {
    interfaces: source.interfaces || "core",
    model_runs: source.model_runs || source.backends || "mock",
    language_mode: source.language_mode || "config",
    language: source.language,
    reference_text: source.reference_text,
    record_sec: source.record_sec ?? 5,
    sample_rate: source.sample_rate ?? 16000,
    action_chunk_sec: source.action_chunk_sec ?? 0.8,
    request_timeout_sec: source.request_timeout_sec ?? 25,
    ros_auto_launch: source.ros_auto_launch !== false,
    action_streaming: Boolean(source.action_streaming),
    use_wav: source.use_wav,
    device: source.device,
    backends: source.backends,
  };
  return pruneValue(payload) || {};
}

function buildBenchmarkPayload() {
  const source = buildUnifiedPayload();
  const payload = {
    dataset: source.dataset || "data/transcripts/sample_manifest.csv",
    backends: source.backends,
    sample_rate: source.sample_rate ?? 16000,
  };
  return pruneValue(payload) || {};
}

function buildBringupPayload() {
  const source = buildUnifiedPayload();
  const inputMode = source.bringup_input_mode || "mic";
  const payload = {
    input_mode: inputMode,
    wav_path: source.bringup_wav,
    mic_capture_sec: source.bringup_mic_sec ?? 4,
    continuous: source.bringup_continuous !== false,
    live_stream_enabled: source.bringup_live_enabled !== false,
    text_output_enabled: source.bringup_text_enabled !== false,
    sample_rate: source.sample_rate ?? 16000,
    chunk_ms: intValue("chunk-ms", 800),
    device: source.device,
  };
  if (inputMode === "file" && !payload.wav_path) {
    payload.wav_path = textValue("use-wav");
  }
  return pruneValue(payload) || {};
}

function buildRunRequest(payload) {
  return {
    profile_name: textValue("profile-name"),
    base_config: textValue("base-config") || "configs/default.yaml",
    runtime_overrides: buildRuntimeOverrides(),
    payload,
    secrets: buildSecrets(),
    aws_auth_profile: selectedAwsAuthProfile(),
  };
}

function buildProfileDocument() {
  const documentPayload = {
    profile_name: textValue("profile-name"),
    base_config: textValue("base-config") || "configs/default.yaml",
    runtime_overrides: buildRuntimeOverrides(),
    payload: buildUnifiedPayload(),
    aws_auth_profile: selectedAwsAuthProfile(),
    aws_sso_start_url: textValue("secret-aws-sso-start-url"),
    aws_sso_region: textValue("secret-aws-sso-region"),
  };
  if (!documentPayload.aws_auth_profile) {
    delete documentPayload.aws_auth_profile;
  }
  if (!documentPayload.aws_sso_start_url) {
    delete documentPayload.aws_sso_start_url;
  }
  if (!documentPayload.aws_sso_region) {
    delete documentPayload.aws_sso_region;
  }
  return documentPayload;
}

function ensureProfileDatalist() {
  let datalist = $("profile-options");
  if (datalist) {
    return datalist;
  }
  datalist = document.createElement("datalist");
  datalist.id = "profile-options";
  document.body.appendChild(datalist);
  const profileInput = $("profile-name");
  if (profileInput) {
    profileInput.setAttribute("list", "profile-options");
  }
  return datalist;
}

function setProfileOptions(values) {
  const datalist = ensureProfileDatalist();
  datalist.innerHTML = "";
  for (const value of uniqueStrings(values)) {
    const option = document.createElement("option");
    option.value = value;
    datalist.appendChild(option);
  }
}

function setAwsAuthProfileOptions(values) {
  const select = $("aws-auth-profile");
  if (!select) {
    return;
  }
  const current = textValue("aws-auth-profile");
  fillSelect("aws-auth-profile", uniqueStrings(values), {
    includeEmpty: true,
    emptyLabel: "(none)",
  });
  if (current) {
    select.value = current;
  }
}

function populateStaticOptionLists(options) {
  fillSelect("base-config", options.base_configs || []);
  fillSelect("asr-backend", options.backends || []);
  fillSelect("language-mode", options.language_modes || ["config", "manual", "auto"]);

  renderCheckboxGroup("interfaces", options.interfaces || ["core", "ros_service", "ros_action"]);
  if (options.interfaces && options.interfaces.length > 0) {
    setCheckedValues("interfaces", [options.interfaces[0]]);
  }

  renderCheckboxGroup("metric-select", options.metrics || []);
  if (options.metrics && options.metrics.length > 0) {
    setCheckedValues("metric-select", options.metrics.slice(0, 4));
  }

  fillDatalist("language-options", options.languages || []);
  fillDatalist("sample-rate-options", options.sample_rates || []);
  fillDatalist("chunk-ms-options", options.chunk_ms_values || []);
  fillDatalist("model-runs-options", options.model_run_presets || []);
  fillDatalist("whisper-model-options", asObject(options.backend_models).whisper || []);
  fillDatalist("whisper-device-options", options.whisper_devices || []);
  fillDatalist("whisper-compute-options", options.whisper_compute_types || []);
  fillDatalist("vosk-model-path-options", options.vosk_model_paths || []);
  fillDatalist("google-model-options", asObject(options.backend_models).google || []);
  fillDatalist("aws-region-options", options.aws_regions || []);
  fillDatalist("aws-bucket-options", options.aws_bucket_hints || []);
  fillDatalist("azure-region-options", options.azure_regions || []);
  fillDatalist("azure-endpoint-options", options.azure_endpoint_hints || []);
  fillDatalist("dataset-options", options.datasets || []);
  fillDatalist("bench-backends-options", options.benchmark_backend_presets || []);
  fillDatalist("bench-chunk-sec-options", options.benchmark_chunk_sec_values || []);
  fillDatalist("bench-scenarios-options", options.benchmark_scenario_presets || []);
  fillDatalist("noise-levels-options", options.noise_level_presets || []);
  fillDatalist("reference-text-options", options.reference_texts || []);
  fillDatalist("record-sec-options", options.record_sec_values || []);
  fillDatalist("audio-device-options", options.audio_device_hints || []);
  fillDatalist("action-chunk-sec-options", options.action_chunk_sec_values || []);
  fillDatalist("request-timeout-options", options.request_timeout_values || []);
  fillDatalist("bringup-mic-sec-options", options.mic_capture_sec_values || []);
  fillDatalist("aws-sso-start-url-options", options.aws_sso_start_urls || []);
  fillDatalist("aws-sso-region-options", options.aws_sso_regions || []);

  setProfileOptions(options.profiles || []);
  setAwsAuthProfileOptions(options.aws_auth_profiles || []);
}

function applyConfigDefaults(configPath) {
  const defaultsByConfig = asObject(state.options?.defaults_by_config);
  const defaults = asObject(defaultsByConfig[configPath]);
  if (!Object.keys(defaults).length) {
    return;
  }

  const asr = asObject(defaults.asr);
  setTextValue("asr-backend", asr.backend);
  setTextValue("language", asr.language);
  setTextValue("input-mode", asr.input_mode);
  setTextValue("sample-rate", asr.sample_rate);
  setTextValue("chunk-ms", asr.chunk_ms);

  const backends = asObject(defaults.backends);
  const whisper = asObject(backends.whisper);
  setTextValue("whisper-model", whisper.model_size);
  setTextValue("whisper-device", whisper.device);
  setTextValue("whisper-compute", whisper.compute_type);

  const vosk = asObject(backends.vosk);
  setTextValue("vosk-model-path", vosk.model_path);

  const google = asObject(backends.google);
  setTextValue("google-model", google.model);

  const aws = asObject(backends.aws);
  setTextValue("aws-region", aws.region);
  setTextValue("aws-bucket", aws.s3_bucket);

  const azure = asObject(backends.azure);
  setTextValue("azure-region", azure.region);
  setTextValue("azure-endpoint", azure.endpoint);

  const benchmark = asObject(defaults.benchmark);
  if (Array.isArray(benchmark.scenarios)) {
    setTextValue("bench-scenarios", benchmark.scenarios.join(","));
  } else if (typeof benchmark.scenarios === "string") {
    setTextValue("bench-scenarios", benchmark.scenarios);
  }
  if (benchmark.chunk_sec !== undefined) {
    setTextValue("bench-chunk-sec", benchmark.chunk_sec);
  }
  if (Array.isArray(benchmark.selected_metrics)) {
    setCheckedValues("metric-select", benchmark.selected_metrics);
  }

  const web = asObject(defaults.web);
  if (web.interfaces !== undefined) {
    setCheckedValues("interfaces", web.interfaces);
  }
  setTextValue("model-runs", web.model_runs);
  setTextValue("bench-backends", web.benchmark_backends);
  setTextValue("dataset", web.dataset);
  setTextValue("language-mode", web.language_mode);
  setTextValue("record-sec", web.record_sec);
  setTextValue("action-chunk-sec", web.action_chunk_sec);
  setTextValue("request-timeout", web.request_timeout_sec);
  setChecked("ros-auto-launch", web.ros_auto_launch !== false);
  setChecked("action-streaming", Boolean(web.action_streaming));

  setTextValue("bringup-input-mode", web.bringup_input_mode);
  setTextValue("bringup-wav", web.bringup_wav);
  setTextValue("bringup-mic-sec", web.bringup_mic_capture_sec);
  setChecked("bringup-continuous", web.bringup_continuous !== false);
  setChecked("bringup-live-enabled", web.bringup_live_stream_enabled !== false);
  setChecked("bringup-text-enabled", web.bringup_text_output_enabled !== false);

  setTextValue("noise-levels", web.noise_levels);
}

function applyRuntimeOverrides(overrides) {
  const payload = asObject(overrides);

  const asr = asObject(payload.asr);
  setTextValue("asr-backend", asr.backend);
  setTextValue("language", asr.language);
  setTextValue("input-mode", asr.input_mode);
  setTextValue("sample-rate", asr.sample_rate);
  setTextValue("chunk-ms", asr.chunk_ms);

  const backends = asObject(payload.backends);
  const whisper = asObject(backends.whisper);
  setTextValue("whisper-model", whisper.model_size);
  setTextValue("whisper-device", whisper.device);
  setTextValue("whisper-compute", whisper.compute_type);

  const vosk = asObject(backends.vosk);
  setTextValue("vosk-model-path", vosk.model_path);

  const google = asObject(backends.google);
  setTextValue("google-model", google.model);

  const aws = asObject(backends.aws);
  setTextValue("aws-region", aws.region);
  setTextValue("aws-bucket", aws.s3_bucket);

  const azure = asObject(backends.azure);
  setTextValue("azure-region", azure.region);
  setTextValue("azure-endpoint", azure.endpoint);

  const benchmark = asObject(payload.benchmark);
  if (benchmark.scenarios !== undefined) {
    setTextValue("bench-scenarios", Array.isArray(benchmark.scenarios) ? benchmark.scenarios.join(",") : benchmark.scenarios);
  }
  if (benchmark.chunk_sec !== undefined) {
    setTextValue("bench-chunk-sec", benchmark.chunk_sec);
  }
  if (benchmark.selected_metrics !== undefined) {
    setCheckedValues("metric-select", benchmark.selected_metrics);
  }
}

function applyFlatPayload(payload) {
  const values = asObject(payload);
  setTextValue("model-runs", values.model_runs);
  setTextValue("language-mode", values.language_mode);
  setTextValue("language", values.language);
  setTextValue("reference-text", values.reference_text);
  setTextValue("record-sec", values.record_sec);
  setTextValue("sample-rate", values.sample_rate);
  setTextValue("action-chunk-sec", values.action_chunk_sec);
  setTextValue("request-timeout", values.request_timeout_sec);
  setTextValue("use-wav", values.use_wav);
  setTextValue("audio-device", values.device);

  setTextValue("dataset", values.dataset);
  setTextValue("bench-backends", values.backends);
  setTextValue("bench-scenarios", values.scenarios);

  if (values.interfaces !== undefined) {
    setCheckedValues("interfaces", values.interfaces);
  }

  if (values.ros_auto_launch !== undefined) {
    setChecked("ros-auto-launch", Boolean(values.ros_auto_launch));
  }
  if (values.action_streaming !== undefined) {
    setChecked("action-streaming", Boolean(values.action_streaming));
  }

  setTextValue("bringup-input-mode", values.bringup_input_mode);
  setTextValue("bringup-wav", values.bringup_wav);
  setTextValue("bringup-mic-sec", values.bringup_mic_sec);

  if (values.bringup_continuous !== undefined) {
    setChecked("bringup-continuous", Boolean(values.bringup_continuous));
  }
  if (values.bringup_live_enabled !== undefined) {
    setChecked("bringup-live-enabled", Boolean(values.bringup_live_enabled));
  }
  if (values.bringup_text_enabled !== undefined) {
    setChecked("bringup-text-enabled", Boolean(values.bringup_text_enabled));
  }

  setTextValue("noise-levels", values.noise_levels);

  if (values.aws_auth_profile !== undefined) {
    setTextValue("aws-auth-profile", values.aws_auth_profile);
  }
}

function applyLoadedProfile(name, profilePayload) {
  const payload = asObject(profilePayload);

  if (payload.base_config) {
    setTextValue("base-config", payload.base_config);
    applyConfigDefaults(payload.base_config);
  }

  if (payload.runtime_overrides) {
    applyRuntimeOverrides(payload.runtime_overrides);
  }

  if (payload.payload && typeof payload.payload === "object") {
    applyFlatPayload(payload.payload);
  } else {
    applyFlatPayload(payload);
  }

  if (payload.aws_auth_profile) {
    setTextValue("aws-auth-profile", payload.aws_auth_profile);
    setTextValue("aws-auth-name", payload.aws_auth_profile);
  }
  if (payload.aws_sso_start_url) {
    setTextValue("secret-aws-sso-start-url", payload.aws_sso_start_url);
  }
  if (payload.aws_sso_region) {
    setTextValue("secret-aws-sso-region", payload.aws_sso_region);
  }

  setTextValue("profile-name", name || payload.profile_name);
  scheduleFormDraftSave();
}

function updateFileDependentInputs() {
  const options = state.options || {};
  const uploads = state.files.uploads || [];
  const noisy = state.files.noisy || [];

  const uploadWavs = uploads.filter((item) => fileExt(item) === "wav");
  const allWavs = uniqueStrings([...(options.sample_wavs || []), ...uploadWavs, ...noisy]);

  fillSelect("noise-source", allWavs, { includeEmpty: true, emptyLabel: "(select source WAV)" });
  fillSelect("use-wav", allWavs, { includeEmpty: true, emptyLabel: "(record from mic)" });
  fillSelect("bringup-wav", allWavs, { includeEmpty: true, emptyLabel: "(none)" });

  const uploadedCsv = uploads.filter((item) => fileExt(item) === "csv");
  fillDatalist("dataset-options", uniqueStrings([...(options.datasets || []), ...uploadedCsv]));
}

function isInactiveRestoredJob(job) {
  const metadata = asObject(job && job.metadata);
  const restored = Boolean(metadata.restored);
  const status = String((job && job.status) || "").toLowerCase();
  return restored && !ACTIVE_JOB_STATUSES.has(status);
}

function getSelectedJob() {
  return state.allJobs.find((item) => item.job_id === state.selectedJobId) || null;
}

function setSelectedJob(jobId) {
  const normalized = String(jobId || "").trim();
  state.selectedJobId = normalized;

  if (normalized) {
    localStorage.setItem(STORAGE_SELECTED_JOB, normalized);
  } else {
    localStorage.removeItem(STORAGE_SELECTED_JOB);
  }

  renderJobsTable();
  renderHiddenJobsDropdown();
  updateSelectionBanner();
  refreshSelectedJobDetails().catch((err) => {
    showToast(err.message, "error");
  });
}

function updateSelectionBanner() {
  const job = getSelectedJob();
  $("job-count").textContent = String(state.allJobs.length);
  const hiddenCount = $("inactive-jobs-count");
  if (hiddenCount) {
    hiddenCount.textContent = String(state.hiddenJobs.length);
  }

  if (!job) {
    $("selected-job-label").textContent = "none";
    const hasRunning = state.allJobs.some((item) =>
      ACTIVE_JOB_STATUSES.has(String(item.status || "").toLowerCase()),
    );
    setStatusPill(hasRunning ? "running" : "idle");
    return;
  }

  const shortId = String(job.job_id || "").slice(0, 8);
  const status = String(job.status || "unknown").toLowerCase();
  $("selected-job-label").textContent = `${job.kind || "job"}#${shortId} (${status})`;
  setStatusPill(status);
}

function renderHiddenJobsDropdown() {
  const panel = $("inactive-jobs-details");
  const select = $("inactive-jobs-select");
  const openButton = $("inactive-jobs-open");
  if (!panel || !select || !openButton) {
    return;
  }

  if (!state.hiddenJobs.length) {
    panel.hidden = true;
    panel.open = false;
    select.innerHTML = "";
    openButton.disabled = true;
    return;
  }

  panel.hidden = false;
  const previous = String(select.value || "");
  select.innerHTML = "";

  for (const job of state.hiddenJobs) {
    const shortId = String(job.job_id || "").slice(0, 8);
    const status = String(job.status || "unknown").toLowerCase();
    const started = String(job.started_at || job.created_at || "").replace("T", " ");
    const option = document.createElement("option");
    option.value = String(job.job_id || "");
    option.textContent = `${job.kind || "job"}#${shortId} (${status}) ${started}`.trim();
    select.appendChild(option);
  }

  if (state.selectedJobId && state.hiddenJobs.some((item) => item.job_id === state.selectedJobId)) {
    select.value = state.selectedJobId;
  } else if (previous && state.hiddenJobs.some((item) => item.job_id === previous)) {
    select.value = previous;
  } else if (state.hiddenJobs.length > 0) {
    select.value = String(state.hiddenJobs[0].job_id || "");
  }

  openButton.disabled = !textValue("inactive-jobs-select");
}

function renderJobsTable() {
  const tbody = $("jobs-body");
  if (!tbody) {
    return;
  }

  tbody.innerHTML = "";

  for (const job of state.jobs) {
    const row = document.createElement("tr");
    if (job.job_id === state.selectedJobId) {
      row.classList.add("is-selected");
    }

    row.addEventListener("click", () => {
      setSelectedJob(job.job_id);
    });

    const jobCell = document.createElement("td");
    const shortId = String(job.job_id || "").slice(0, 8);
    jobCell.textContent = `${shortId}`;
    jobCell.title = String(job.job_id || "");

    const kindCell = document.createElement("td");
    kindCell.textContent = String(job.kind || "");

    const statusCell = document.createElement("td");
    statusCell.textContent = String(job.status || "");

    const startedCell = document.createElement("td");
    startedCell.textContent = String(job.started_at || job.created_at || "");

    const actionCell = document.createElement("td");
    if (ACTIVE_JOB_STATUSES.has(String(job.status || "").toLowerCase())) {
      const stopButton = document.createElement("button");
      stopButton.type = "button";
      stopButton.className = "btn";
      stopButton.textContent = "Stop";
      stopButton.addEventListener("click", async (event) => {
        event.stopPropagation();
        setBusy(stopButton, true, "Stopping...");
        try {
          await apiRequest(`/api/jobs/${encodeURIComponent(job.job_id)}/stop`, { method: "POST" });
          showToast(`Job ${shortId} stopped`, "info");
          await refreshJobs();
        } catch (err) {
          showToast(err.message, "error");
        } finally {
          setBusy(stopButton, false);
        }
      });
      actionCell.appendChild(stopButton);
    } else {
      actionCell.textContent = "-";
    }

    row.appendChild(jobCell);
    row.appendChild(kindCell);
    row.appendChild(statusCell);
    row.appendChild(startedCell);
    row.appendChild(actionCell);
    tbody.appendChild(row);
  }
}

async function refreshJobs(config = {}) {
  if (state.jobsRefreshInFlight) {
    return;
  }
  state.jobsRefreshInFlight = true;

  try {
    const payload = await apiRequest("/api/jobs");
    const allJobs = Array.isArray(payload.jobs) ? payload.jobs : [];

    state.allJobs = allJobs;
    state.jobs = allJobs.filter((item) => !isInactiveRestoredJob(item));
    state.hiddenJobs = allJobs.filter((item) => isInactiveRestoredJob(item));

    if (state.selectedJobId && !state.allJobs.some((item) => item.job_id === state.selectedJobId)) {
      state.selectedJobId = "";
      localStorage.removeItem(STORAGE_SELECTED_JOB);
    }

    renderJobsTable();
    renderHiddenJobsDropdown();
    updateSelectionBanner();

    if (state.selectedJobId) {
      await refreshSelectedJobDetails();
    }
  } catch (err) {
    if (!config.silent) {
      showToast(err.message, "error");
    }
  } finally {
    state.jobsRefreshInFlight = false;
  }
}

function clearArtifactsAndLogs() {
  const logViewer = $("log-viewer");
  if (logViewer) {
    logViewer.textContent = "Select a job to inspect logs.";
  }

  const artifactList = $("artifact-list");
  if (artifactList) {
    artifactList.innerHTML = "";
  }

  const preview = $("artifact-preview");
  if (preview) {
    preview.textContent = "Select an artifact to preview.";
  }
}

function renderArtifacts(artifacts) {
  const container = $("artifact-list");
  if (!container) {
    return;
  }
  container.innerHTML = "";

  if (!artifacts.length) {
    const muted = document.createElement("div");
    muted.textContent = "No artifacts yet.";
    container.appendChild(muted);
    return;
  }

  for (const artifactPath of artifacts) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "artifact-chip";

    const name = document.createElement("strong");
    name.textContent = fileBaseName(artifactPath);

    const sub = document.createElement("span");
    sub.textContent = trimMiddle(String(artifactPath || ""), 60);
    sub.title = String(artifactPath || "");

    button.appendChild(name);
    button.appendChild(sub);

    button.addEventListener("click", () => {
      previewArtifact(artifactPath).catch((err) => {
        showToast(err.message, "error");
      });
    });

    container.appendChild(button);
  }
}

function appendRawArtifactLink(container, path) {
  const link = document.createElement("a");
  link.href = buildArtifactUrl(path);
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "Open raw artifact";
  container.appendChild(link);
}

async function previewArtifact(path) {
  const preview = $("artifact-preview");
  if (!preview) {
    return;
  }

  preview.textContent = "Loading artifact...";
  const extension = fileExt(path);
  const url = buildArtifactUrl(path);

  preview.innerHTML = "";

  if (["png", "jpg", "jpeg", "gif", "webp"].includes(extension)) {
    const image = document.createElement("img");
    image.src = url;
    image.alt = fileBaseName(path);
    preview.appendChild(image);
    preview.appendChild(document.createElement("br"));
    appendRawArtifactLink(preview, path);
    return;
  }

  if (["wav", "mp3", "ogg", "m4a", "flac"].includes(extension)) {
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = url;
    preview.appendChild(audio);
    preview.appendChild(document.createElement("br"));
    appendRawArtifactLink(preview, path);
    return;
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Artifact preview failed: HTTP ${response.status}`);
  }

  const text = await response.text();
  const pre = document.createElement("pre");
  const maxLength = 200_000;
  if (text.length > maxLength) {
    pre.textContent = `${text.slice(0, maxLength)}\n\n...[truncated ${text.length - maxLength} chars]`;
  } else {
    pre.textContent = text;
  }
  preview.appendChild(pre);
  preview.appendChild(document.createElement("br"));
  appendRawArtifactLink(preview, path);
}

async function refreshSelectedJobDetails() {
  const selected = getSelectedJob();
  if (!selected) {
    clearArtifactsAndLogs();
    return;
  }

  const logsPayload = await apiRequest(
    `/api/jobs/${encodeURIComponent(selected.job_id)}/logs?lines=400`,
  );

  const logViewer = $("log-viewer");
  if (logViewer) {
    const logText = String(logsPayload.log || "").trim();
    logViewer.textContent = logText || "(log is empty)";
    logViewer.scrollTop = logViewer.scrollHeight;
  }

  const artifacts = Array.isArray(selected.artifacts) ? selected.artifacts : [];
  renderArtifacts(artifacts);
}

function collectPreflightFailures(value, prefix = "", output = []) {
  if (!value || typeof value !== "object") {
    return output;
  }
  if (Object.prototype.hasOwnProperty.call(value, "ok") && value.ok === false) {
    const label = prefix || "check";
    const message = value.message ? `: ${String(value.message)}` : "";
    output.push(`${label}${message}`);
    return output;
  }

  for (const [key, item] of Object.entries(value)) {
    const next = prefix ? `${prefix}.${key}` : key;
    collectPreflightFailures(item, next, output);
  }
  return output;
}

async function refreshPreflight(config = {}) {
  const payload = await apiRequest("/api/preflight");
  const failures = collectPreflightFailures(payload.checks || {});

  const summaryNode = $("preflight-summary");
  if (summaryNode) {
    if (payload.ok) {
      summaryNode.textContent = "OK: environment checks passed";
    } else if (failures.length > 0) {
      summaryNode.textContent = `FAIL (${failures.length}): ${failures.slice(0, 2).join(" | ")}`;
    } else {
      summaryNode.textContent = "FAIL: checks returned issues";
    }
  }

  if (config.notify) {
    if (payload.ok) {
      showToast("Preflight passed", "success");
    } else {
      showToast(`Preflight issues: ${failures.slice(0, 2).join(" | ") || "unknown"}`, "error", 6200);
    }
  }
}

async function refreshOptions(config = {}) {
  if (state.optionsRefreshInFlight) {
    return;
  }
  state.optionsRefreshInFlight = true;

  try {
    const optionsPayload = await apiRequest("/api/options");
    state.options = asObject(optionsPayload);
    populateStaticOptionLists(state.options);

    if (!textValue("base-config")) {
      const firstConfig = (state.options.base_configs || [])[0] || "configs/default.yaml";
      setTextValue("base-config", firstConfig);
    }

    if (config.applyConfigDefaults) {
      applyConfigDefaults(textValue("base-config"));
    }
  } catch (err) {
    if (!config.silent) {
      showToast(err.message, "error");
    }
  } finally {
    state.optionsRefreshInFlight = false;
  }
}

async function refreshFiles(config = {}) {
  if (state.filesRefreshInFlight) {
    return;
  }
  state.filesRefreshInFlight = true;

  try {
    const payload = await apiRequest("/api/files");
    state.files = {
      uploads: Array.isArray(payload.uploads) ? payload.uploads : [],
      noisy: Array.isArray(payload.noisy) ? payload.noisy : [],
      results: Array.isArray(payload.results) ? payload.results : [],
    };
    updateFileDependentInputs();
  } catch (err) {
    if (!config.silent) {
      showToast(err.message, "error");
    }
  } finally {
    state.filesRefreshInFlight = false;
  }
}

async function refreshAll(config = {}) {
  await refreshOptions({ silent: config.silent, applyConfigDefaults: Boolean(config.applyConfigDefaults) });
  await refreshFiles({ silent: config.silent });
  await refreshJobs({ silent: config.silent });
}

async function runJob(endpoint, payloadBuilder, buttonId, successLabel) {
  const button = $(buttonId);
  setBusy(button, true);

  try {
    const payload = payloadBuilder();
    const request = buildRunRequest(payload);
    const response = await apiRequest(endpoint, {
      method: "POST",
      body: request,
    });

    if (response.job && response.job.job_id) {
      showToast(successLabel, "success");
      await refreshJobs();
      setSelectedJob(response.job.job_id);
    } else {
      showToast("Job started", "success");
      await refreshJobs();
    }
  } catch (err) {
    showToast(err.message, "error", 6200);
  } finally {
    setBusy(button, false);
  }
}

async function uploadFile(event) {
  event.preventDefault();
  const input = $("upload-file");
  if (!input || !input.files || !input.files[0]) {
    showToast("Select a file first", "error");
    return;
  }

  const button = $("upload-btn");
  setBusy(button, true, "Uploading...");

  try {
    const form = new FormData();
    form.append("file", input.files[0]);
    await apiRequest("/api/upload", {
      method: "POST",
      body: form,
    });
    input.value = "";
    showToast("File uploaded", "success");
    await refreshFiles();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function applyNoise() {
  const button = $("apply-noise");
  setBusy(button, true, "Generating...");

  try {
    const sourceWav = textValue("noise-source");
    if (!sourceWav) {
      throw new Error("Choose a noise source WAV first");
    }

    const snrLevels = parseCommaList(textValue("noise-levels"))
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item));

    if (!snrLevels.length) {
      throw new Error("SNR list is empty");
    }

    const response = await apiRequest("/api/noise/apply", {
      method: "POST",
      body: {
        source_wav: sourceWav,
        snr_levels: snrLevels,
      },
    });

    const count = Array.isArray(response.generated) ? response.generated.length : 0;
    showToast(`Generated ${count} noisy sample(s)`, "success");
    await refreshFiles();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setBusy(button, false);
  }
}

async function saveProfile() {
  const button = $("save-profile");
  setBusy(button, true, "Saving...");

  try {
    const name = textValue("profile-name");
    if (!name) {
      throw new Error("Profile name is required");
    }

    const payload = buildProfileDocument();
    const response = await apiRequest("/api/profiles", {
      method: "POST",
      body: {
        name,
        payload,
      },
    });

    setProfileOptions(response.profiles || []);
    showToast(`Profile '${name}' saved`, "success");
  } catch (err) {
    showToast(err.message, "error", 6200);
  } finally {
    setBusy(button, false);
  }
}

async function loadProfile() {
  const button = $("load-profile");
  setBusy(button, true, "Loading...");

  try {
    const name = textValue("profile-name");
    if (!name) {
      throw new Error("Profile name is required");
    }

    const response = await apiRequest(`/api/profiles/${encodeURIComponent(name)}`);
    applyLoadedProfile(name, response.payload || {});
    showToast(`Profile '${name}' loaded`, "success");
  } catch (err) {
    showToast(err.message, "error", 6200);
  } finally {
    setBusy(button, false);
  }
}

function parseEnvLikeText(raw) {
  const values = {};
  for (const rawLine of String(raw || "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const index = line.indexOf("=");
    if (index <= 0) {
      continue;
    }
    const key = line.slice(0, index).trim();
    const value = line.slice(index + 1).trim();
    if (key) {
      values[key] = value;
    }
  }
  return values;
}

function dumpEnvLikeText(values) {
  const order = [
    "AWS_AUTH_TYPE",
    "AWS_PROFILE",
    "AWS_REGION",
    "AWS_S3_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_SSO_START_URL",
    "AWS_SSO_REGION",
    "AWS_SSO_ACCOUNT_ID",
    "AWS_SSO_ROLE_NAME",
    "AWS_SSO_SESSION_NAME",
  ];

  const normalized = {};
  for (const [key, value] of Object.entries(values || {})) {
    const cleanKey = String(key || "").trim().toUpperCase();
    const cleanValue = String(value || "").trim();
    if (cleanKey && cleanValue) {
      normalized[cleanKey] = cleanValue;
    }
  }

  const lines = [];
  const emitted = new Set();
  for (const key of order) {
    if (normalized[key]) {
      lines.push(`${key}=${normalized[key]}`);
      emitted.add(key);
    }
  }

  for (const key of Object.keys(normalized).sort()) {
    if (emitted.has(key)) {
      continue;
    }
    lines.push(`${key}=${normalized[key]}`);
  }

  return lines.join("\n") + (lines.length ? "\n" : "");
}

function buildAwsAuthTextFromForm() {
  const existing = parseEnvLikeText(textValue("aws-auth-text"));
  const profileName = textValue("aws-auth-name") || textValue("aws-auth-profile") || existing.AWS_PROFILE || "ros2ws";
  const awsRegion = textValue("aws-region") || existing.AWS_REGION || textValue("secret-aws-sso-region") || "us-east-1";
  const startUrl = textValue("secret-aws-sso-start-url");
  const ssoRegion = textValue("secret-aws-sso-region");
  const bucket = textValue("aws-bucket");

  existing.AWS_PROFILE = profileName;
  existing.AWS_REGION = awsRegion;

  if (bucket) {
    existing.AWS_S3_BUCKET = bucket;
  }

  if (startUrl || ssoRegion) {
    existing.AWS_AUTH_TYPE = "sso";
    if (startUrl) {
      existing.AWS_SSO_START_URL = startUrl;
    }
    if (ssoRegion) {
      existing.AWS_SSO_REGION = ssoRegion;
    }
  } else if (!existing.AWS_AUTH_TYPE) {
    existing.AWS_AUTH_TYPE = "access_keys";
  }

  const accessKeyId = textValue("secret-aws-id");
  const secretAccessKey = textValue("secret-aws-secret");
  const sessionToken = textValue("secret-aws-token");
  if (accessKeyId) {
    existing.AWS_ACCESS_KEY_ID = accessKeyId;
  }
  if (secretAccessKey) {
    existing.AWS_SECRET_ACCESS_KEY = secretAccessKey;
  }
  if (sessionToken) {
    existing.AWS_SESSION_TOKEN = sessionToken;
  }

  const dumped = dumpEnvLikeText(existing);
  setTextValue("aws-auth-text", dumped);
  setTextValue("aws-auth-name", profileName);
  return dumped;
}

function applyAwsAuthValues(values) {
  const payload = asObject(values);
  setTextValue("secret-aws-sso-start-url", payload.AWS_SSO_START_URL);
  setTextValue("secret-aws-sso-region", payload.AWS_SSO_REGION);
  setTextValue("aws-region", payload.AWS_REGION);
  setTextValue("aws-bucket", payload.AWS_S3_BUCKET);
  setTextValue("secret-aws-id", payload.AWS_ACCESS_KEY_ID);
  setTextValue("secret-aws-secret", payload.AWS_SECRET_ACCESS_KEY);
  setTextValue("secret-aws-token", payload.AWS_SESSION_TOKEN);
}

async function loadAwsAuthProfile() {
  const button = $("load-aws-auth");
  setBusy(button, true, "Loading...");

  try {
    const name = textValue("aws-auth-profile") || textValue("aws-auth-name");
    if (!name) {
      throw new Error("Choose AWS auth profile first");
    }

    const response = await apiRequest(`/api/aws-auth-profiles/${encodeURIComponent(name)}`);
    setTextValue("aws-auth-text", response.content || "");
    setTextValue("aws-auth-name", response.name || name);
    setTextValue("aws-auth-profile", response.name || name);

    applyAwsAuthValues(response.values || {});
    scheduleFormDraftSave();
    showToast(`AWS auth profile '${name}' loaded`, "success");
  } catch (err) {
    showToast(err.message, "error", 6200);
  } finally {
    setBusy(button, false);
  }
}

async function saveAwsAuthProfile(config = {}) {
  const button = $("save-aws-auth");
  if (!config.silent) {
    setBusy(button, true, "Saving...");
  }

  try {
    const name = textValue("aws-auth-name") || textValue("aws-auth-profile");
    if (!name) {
      throw new Error("AWS auth profile name is required");
    }

    let content = textValue("aws-auth-text");
    if (!content) {
      content = buildAwsAuthTextFromForm();
    }

    const response = await apiRequest("/api/aws-auth-profiles", {
      method: "POST",
      body: {
        name,
        content,
      },
    });

    const profiles = response.profiles || [];
    setAwsAuthProfileOptions(profiles);
    setTextValue("aws-auth-profile", name);
    setTextValue("aws-auth-name", name);
    scheduleFormDraftSave();

    if (!config.silent) {
      showToast(`AWS auth profile '${name}' saved`, "success");
    }

    return name;
  } catch (err) {
    if (!config.silent) {
      showToast(err.message, "error", 6200);
    }
    throw err;
  } finally {
    if (!config.silent) {
      setBusy(button, false);
    }
  }
}

async function runAwsSsoLogin() {
  const button = $("aws-sso-login");
  setBusy(button, true, "Starting...");

  try {
    let profile = textValue("aws-auth-profile");
    if (!profile) {
      profile = await saveAwsAuthProfile({ silent: true });
    }

    const response = await apiRequest("/api/aws-sso-login", {
      method: "POST",
      body: {
        auth_profile: profile,
        use_device_code: true,
        no_browser: false,
      },
    });

    showToast(`AWS SSO login job started (${profile})`, "success");
    await refreshJobs();
    if (response.job && response.job.job_id) {
      setSelectedJob(response.job.job_id);
    }
  } catch (err) {
    showToast(err.message, "error", 6200);
  } finally {
    setBusy(button, false);
  }
}

function bindEvents() {
  $("run-preflight")?.addEventListener("click", () => {
    refreshPreflight({ notify: true }).catch((err) => {
      showToast(err.message, "error");
    });
  });

  $("refresh-all")?.addEventListener("click", () => {
    refreshAll({ applyConfigDefaults: false }).catch((err) => {
      showToast(err.message, "error");
    });
  });

  $("base-config")?.addEventListener("change", () => {
    applyConfigDefaults(textValue("base-config"));
    scheduleFormDraftSave();
    showToast("Base config defaults applied", "info");
  });

  $("upload-form")?.addEventListener("submit", uploadFile);
  $("apply-noise")?.addEventListener("click", applyNoise);

  $("save-profile")?.addEventListener("click", saveProfile);
  $("load-profile")?.addEventListener("click", loadProfile);

  $("build-aws-auth")?.addEventListener("click", () => {
    buildAwsAuthTextFromForm();
    showToast("AWS auth text built", "info");
  });

  $("load-aws-auth")?.addEventListener("click", loadAwsAuthProfile);
  $("save-aws-auth")?.addEventListener("click", () => {
    saveAwsAuthProfile().catch((_err) => {
      // handled in saveAwsAuthProfile
    });
  });
  $("aws-sso-login")?.addEventListener("click", runAwsSsoLogin);

  $("aws-auth-profile")?.addEventListener("change", () => {
    const selected = textValue("aws-auth-profile");
    if (selected) {
      setTextValue("aws-auth-name", selected);
    }
  });

  $("run-live")?.addEventListener("click", () => {
    runJob("/api/jobs/live-sample", buildLivePayload, "run-live", "Live eval job started").catch(
      (_err) => {
        // handled in runJob
      },
    );
  });

  $("run-benchmark")?.addEventListener("click", () => {
    runJob(
      "/api/jobs/benchmark",
      buildBenchmarkPayload,
      "run-benchmark",
      "Benchmark job started",
    ).catch((_err) => {
      // handled in runJob
    });
  });

  $("start-bringup")?.addEventListener("click", () => {
    runJob(
      "/api/jobs/ros-bringup",
      buildBringupPayload,
      "start-bringup",
      "ROS bringup job started",
    ).catch((_err) => {
      // handled in runJob
    });
  });

  const nonPersistedInputs = new Set([
    "secret-azure-key",
    "secret-aws-id",
    "secret-aws-secret",
    "secret-aws-token",
    "aws-auth-text",
    "log-viewer",
  ]);
  const workspace = document.querySelector(".workspace");
  const onFormMutation = (event) => {
    const target = event && event.target ? event.target : null;
    const targetId = target && target.id ? String(target.id) : "";
    if (targetId && nonPersistedInputs.has(targetId)) {
      return;
    }
    scheduleFormDraftSave();
  };
  workspace?.addEventListener("input", onFormMutation);
  workspace?.addEventListener("change", onFormMutation);

  $("inactive-jobs-open")?.addEventListener("click", () => {
    const selected = textValue("inactive-jobs-select");
    if (!selected) {
      showToast("No archived job selected", "error");
      return;
    }
    setSelectedJob(selected);
  });

  $("inactive-jobs-select")?.addEventListener("change", () => {
    const selected = textValue("inactive-jobs-select");
    const openButton = $("inactive-jobs-open");
    if (openButton) {
      openButton.disabled = !selected;
    }
  });
}

function startPolling() {
  if (state.jobsPollTimer) {
    clearInterval(state.jobsPollTimer);
  }
  if (state.filesPollTimer) {
    clearInterval(state.filesPollTimer);
  }

  state.jobsPollTimer = window.setInterval(() => {
    refreshJobs({ silent: true }).catch((_err) => {
      // intentionally silent while polling
    });
  }, 3000);

  state.filesPollTimer = window.setInterval(() => {
    refreshFiles({ silent: true }).catch((_err) => {
      // intentionally silent while polling
    });
  }, 12000);
}

async function init() {
  bindEvents();
  clearArtifactsAndLogs();

  await refreshAll({ applyConfigDefaults: true });
  const savedDraft = loadFormDraft();
  if (savedDraft) {
    applyLoadedProfile(String(savedDraft.profile_name || "draft"), savedDraft);
  }
  await refreshPreflight({ notify: false });

  if (state.selectedJobId) {
    const exists = state.allJobs.some((item) => item.job_id === state.selectedJobId);
    if (!exists) {
      state.selectedJobId = "";
      localStorage.removeItem(STORAGE_SELECTED_JOB);
    }
  }

  updateSelectionBanner();
  if (state.selectedJobId) {
    await refreshSelectedJobDetails();
  }

  if (!savedDraft) {
    saveFormDraftNow();
  }
  startPolling();
}

window.addEventListener("DOMContentLoaded", () => {
  init().catch((err) => {
    showToast(err.message, "error", 7200);
  });
});
