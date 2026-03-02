const state = {
  options: null,
  files: null,
  selectedJobId: null,
};

const $ = (id) => document.getElementById(id);

function splitCsv(raw) {
  return String(raw || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function asNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function setStatus(text) {
  const pill = $("status-pill");
  pill.textContent = text;
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function renderCheckboxGroup(container, options, prefix, checkedValues) {
  container.innerHTML = "";
  for (const value of options) {
    const id = `${prefix}-${value}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" id="${id}" value="${value}"> ${value}`;
    container.appendChild(label);
    if (checkedValues.includes(value)) {
      const input = label.querySelector("input");
      input.checked = true;
    }
  }
}

function checkedValues(containerId) {
  const container = $(containerId);
  return Array.from(container.querySelectorAll("input[type='checkbox']"))
    .filter((item) => item.checked)
    .map((item) => item.value);
}

function populateSelect(selectId, values, selected = "") {
  const select = $(selectId);
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (selected && values.includes(selected)) {
    select.value = selected;
  }
}

function collectRuntimeOverrides() {
  const language = $("language").value.trim();
  const runtime = {
    asr: {
      backend: $("asr-backend").value,
      sample_rate: asNumber($("sample-rate").value, 16000),
      chunk_ms: asNumber($("chunk-ms").value, 800),
      input_mode: $("input-mode").value,
    },
    benchmark: {
      scenarios: splitCsv($("bench-scenarios").value),
      chunk_sec: asNumber($("bench-chunk-sec").value, 0.8),
      selected_metrics: checkedValues("metric-select"),
    },
    backends: {
      whisper: {
        model_size: $("whisper-model").value.trim(),
        device: $("whisper-device").value.trim(),
        compute_type: $("whisper-compute").value.trim(),
      },
      vosk: {
        model_path: $("vosk-model-path").value.trim(),
      },
      google: {
        model: $("google-model").value.trim(),
      },
      aws: {
        region: $("aws-region").value.trim(),
        s3_bucket: $("aws-bucket").value.trim(),
      },
      azure: {
        region: $("azure-region").value.trim(),
        endpoint: $("azure-endpoint").value.trim(),
      },
    },
  };

  if (language) {
    runtime.asr.language = language;
  }
  return runtime;
}

function collectSecrets() {
  return {
    google_credentials_json: $("secret-google-cred").value.trim(),
    google_project_id: $("secret-google-project").value.trim(),
    aws_access_key_id: $("secret-aws-id").value.trim(),
    aws_secret_access_key: $("secret-aws-secret").value.trim(),
    aws_session_token: $("secret-aws-token").value.trim(),
    aws_region: $("aws-region").value.trim(),
    azure_speech_key: $("secret-azure-key").value.trim(),
    azure_region: $("azure-region").value.trim(),
  };
}

function commonRequestEnvelope(payload) {
  return {
    profile_name: $("profile-name").value.trim(),
    base_config: $("base-config").value,
    runtime_overrides: collectRuntimeOverrides(),
    secrets: collectSecrets(),
    payload,
  };
}

function selectedFileOrEmpty(selectId) {
  const select = $(selectId);
  return select && select.value ? select.value : "";
}

async function runLiveSample() {
  setStatus("Starting live sample job...");
  const payload = {
    interfaces: checkedValues("interfaces").join(",") || "core",
    model_runs: $("model-runs").value.trim(),
    language_mode: $("language-mode").value,
    language: $("language").value.trim(),
    reference_text: $("reference-text").value.trim(),
    record_sec: asNumber($("record-sec").value, 5),
    sample_rate: asNumber($("sample-rate").value, 16000),
    use_wav: selectedFileOrEmpty("use-wav"),
    device: $("audio-device").value.trim(),
    ros_auto_launch: $("ros-auto-launch").checked,
    action_streaming: $("action-streaming").checked,
    action_chunk_sec: asNumber($("action-chunk-sec").value, 0.8),
    request_timeout_sec: asNumber($("request-timeout").value, 25),
  };
  const response = await postJSON("/api/jobs/live-sample", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`Live sample job started: ${response.job.job_id}`);
}

async function runBenchmark() {
  setStatus("Starting benchmark job...");
  const payload = {
    dataset: $("dataset").value.trim(),
    backends: $("bench-backends").value.trim(),
  };
  const response = await postJSON("/api/jobs/benchmark", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`Benchmark job started: ${response.job.job_id}`);
}

async function startBringup() {
  setStatus("Starting ROS bringup...");
  const payload = {
    input_mode: $("bringup-input-mode").value,
    wav_path: selectedFileOrEmpty("bringup-wav"),
    mic_capture_sec: asNumber($("bringup-mic-sec").value, 4.0),
    continuous: $("bringup-continuous").checked,
    live_stream_enabled: $("bringup-live-enabled").checked,
    text_output_enabled: $("bringup-text-enabled").checked,
    sample_rate: asNumber($("sample-rate").value, 16000),
    chunk_ms: asNumber($("chunk-ms").value, 800),
    device: $("audio-device").value.trim(),
  };
  const response = await postJSON("/api/jobs/ros-bringup", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`ROS bringup started: ${response.job.job_id}`);
}

async function stopJob(jobId) {
  await postJSON(`/api/jobs/${jobId}/stop`, {});
  await refreshJobs();
  if (state.selectedJobId === jobId) {
    await loadSelectedJob();
  }
  setStatus(`Job ${jobId} stopped`);
}

function renderArtifacts(artifacts) {
  const list = $("artifact-list");
  const preview = $("artifact-preview");
  list.innerHTML = "";
  preview.innerHTML = "";

  artifacts.forEach((item) => {
    const row = document.createElement("div");
    row.className = "artifact-item";

    const link = document.createElement("a");
    link.href = `/api/artifacts?path=${encodeURIComponent(item)}`;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = item;
    row.appendChild(link);

    if (item.endsWith(".png")) {
      const btn = document.createElement("button");
      btn.className = "btn btn-secondary";
      btn.style.marginLeft = "0.5rem";
      btn.textContent = "Preview";
      btn.onclick = () => {
        preview.innerHTML = `<img src="/api/artifacts?path=${encodeURIComponent(item)}" alt="artifact">`;
      };
      row.appendChild(btn);
    }
    list.appendChild(row);
  });
}

async function loadSelectedJob() {
  if (!state.selectedJobId) {
    return;
  }
  const payload = await fetchJSON(`/api/jobs/${state.selectedJobId}`);
  const job = payload.job;
  const logs = await fetchJSON(`/api/jobs/${state.selectedJobId}/logs?lines=300`);
  $("log-viewer").value = logs.log || "";
  renderArtifacts(job.artifacts || []);
}

async function refreshJobs() {
  const payload = await fetchJSON("/api/jobs");
  const jobs = payload.jobs || [];
  const tbody = $("jobs-table").querySelector("tbody");
  tbody.innerHTML = "";

  jobs.forEach((job) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${job.job_id}</td>
      <td>${job.kind}</td>
      <td>${job.status}</td>
      <td>${job.started_at}</td>
      <td></td>
    `;

    row.onclick = async () => {
      state.selectedJobId = job.job_id;
      await loadSelectedJob();
      setStatus(`Selected job ${job.job_id}`);
    };

    const actions = row.querySelector("td:last-child");
    if (job.status === "running") {
      const stopBtn = document.createElement("button");
      stopBtn.className = "btn btn-secondary";
      stopBtn.textContent = "Stop";
      stopBtn.onclick = async (event) => {
        event.stopPropagation();
        await stopJob(job.job_id);
      };
      actions.appendChild(stopBtn);
    } else {
      actions.textContent = "-";
    }
    tbody.appendChild(row);
  });
}

async function runPreflight() {
  const payload = await fetchJSON("/api/preflight");
  if (payload.ok) {
    setStatus("Preflight: all checks passed");
    return;
  }

  const failed = [];
  const checks = payload.checks || {};
  Object.entries(checks.modules || {}).forEach(([name, item]) => {
    if (!item.ok) {
      failed.push(`module:${name}`);
    }
  });
  if (checks.microphone && !checks.microphone.ok) {
    failed.push("microphone");
  }
  Object.entries(checks.ros || {}).forEach(([name, item]) => {
    if (!item.ok) {
      failed.push(`ros:${name}`);
    }
  });
  setStatus(`Preflight issues: ${failed.join(", ")}`);
}

async function refreshFiles() {
  const payload = await fetchJSON("/api/files");
  state.files = payload;
  const sourceValues = ["", ...(payload.uploads || []), ...(payload.noisy || [])];
  const displayValues = sourceValues.map((item) => item || "(none)");

  const mapForSelect = (id) => {
    const select = $(id);
    select.innerHTML = "";
    sourceValues.forEach((value, idx) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = displayValues[idx];
      select.appendChild(option);
    });
  };

  mapForSelect("noise-source");
  mapForSelect("use-wav");
  mapForSelect("bringup-wav");
}

async function uploadFile(event) {
  event.preventDefault();
  const input = $("upload-file");
  if (!input.files || !input.files.length) {
    return;
  }
  const formData = new FormData();
  formData.append("file", input.files[0]);
  const response = await fetch("/api/upload", { method: "POST", body: formData });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  await refreshFiles();
  setStatus(`Uploaded: ${input.files[0].name}`);
  input.value = "";
}

async function applyNoise() {
  const source = $("noise-source").value;
  if (!source) {
    throw new Error("Select source WAV first");
  }
  const levels = splitCsv($("noise-levels").value).map((item) => Number(item));
  const validLevels = levels.filter((item) => Number.isFinite(item));
  if (!validLevels.length) {
    throw new Error("Provide at least one valid SNR value");
  }
  await postJSON("/api/noise/apply", {
    source_wav: source,
    snr_levels: validLevels,
  });
  await refreshFiles();
  setStatus("Noisy samples generated");
}

function exportCurrentProfilePayload() {
  return {
    profile_name: $("profile-name").value.trim(),
    base_config: $("base-config").value,
    runtime_overrides: collectRuntimeOverrides(),
    payload: {
      interfaces: checkedValues("interfaces").join(","),
      model_runs: $("model-runs").value.trim(),
      language_mode: $("language-mode").value,
      language: $("language").value.trim(),
      reference_text: $("reference-text").value.trim(),
      record_sec: asNumber($("record-sec").value, 5),
      sample_rate: asNumber($("sample-rate").value, 16000),
      action_chunk_sec: asNumber($("action-chunk-sec").value, 0.8),
      request_timeout_sec: asNumber($("request-timeout").value, 25),
      ros_auto_launch: $("ros-auto-launch").checked,
      action_streaming: $("action-streaming").checked,
      dataset: $("dataset").value.trim(),
      backends: $("bench-backends").value.trim(),
      scenarios: $("bench-scenarios").value.trim(),
    },
  };
}

function applyProfilePayload(payload) {
  $("profile-name").value = payload.profile_name || "";
  if (payload.base_config) {
    $("base-config").value = payload.base_config;
  }

  const runtime = payload.runtime_overrides || {};
  const asr = runtime.asr || {};
  const benchmark = runtime.benchmark || {};
  const backends = runtime.backends || {};

  if (asr.backend) $("asr-backend").value = asr.backend;
  if (asr.language) $("language").value = asr.language;
  if (asr.sample_rate) $("sample-rate").value = asr.sample_rate;
  if (asr.chunk_ms) $("chunk-ms").value = asr.chunk_ms;
  if (asr.input_mode) $("input-mode").value = asr.input_mode;

  if (benchmark.chunk_sec) $("bench-chunk-sec").value = benchmark.chunk_sec;
  if (benchmark.scenarios) $("bench-scenarios").value = benchmark.scenarios.join(",");

  const whisper = backends.whisper || {};
  if (whisper.model_size) $("whisper-model").value = whisper.model_size;
  if (whisper.device) $("whisper-device").value = whisper.device;
  if (whisper.compute_type) $("whisper-compute").value = whisper.compute_type;

  const vosk = backends.vosk || {};
  if (vosk.model_path) $("vosk-model-path").value = vosk.model_path;

  const google = backends.google || {};
  if (google.model) $("google-model").value = google.model;

  const aws = backends.aws || {};
  if (aws.region) $("aws-region").value = aws.region;
  if (aws.s3_bucket) $("aws-bucket").value = aws.s3_bucket;

  const azure = backends.azure || {};
  if (azure.region) $("azure-region").value = azure.region;
  if (azure.endpoint) $("azure-endpoint").value = azure.endpoint;

  const run = payload.payload || {};
  if (run.model_runs) $("model-runs").value = run.model_runs;
  if (run.language_mode) $("language-mode").value = run.language_mode;
  if (run.reference_text) $("reference-text").value = run.reference_text;
  if (run.record_sec) $("record-sec").value = run.record_sec;
  if (run.action_chunk_sec) $("action-chunk-sec").value = run.action_chunk_sec;
  if (run.request_timeout_sec) $("request-timeout").value = run.request_timeout_sec;
  if (run.dataset) $("dataset").value = run.dataset;
  if (run.backends) $("bench-backends").value = run.backends;
  if (run.scenarios) $("bench-scenarios").value = run.scenarios;

  if (run.interfaces) {
    const selected = splitCsv(run.interfaces);
    const nodes = $("interfaces").querySelectorAll("input[type='checkbox']");
    nodes.forEach((item) => {
      item.checked = selected.includes(item.value);
    });
  }
}

async function saveProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  await postJSON("/api/profiles", {
    name,
    payload: exportCurrentProfilePayload(),
  });
  setStatus(`Profile saved: ${name}`);
}

async function loadProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  const response = await fetchJSON(`/api/profiles/${encodeURIComponent(name)}`);
  applyProfilePayload(response.payload || {});
  setStatus(`Profile loaded: ${name}`);
}

async function bootstrap() {
  setStatus("Loading options...");
  const options = await fetchJSON("/api/options");
  state.options = options;

  populateSelect("base-config", options.base_configs || ["configs/default.yaml"], "configs/default.yaml");
  populateSelect("asr-backend", options.backends || ["mock"], "mock");

  renderCheckboxGroup($("interfaces"), options.interfaces || [], "iface", ["core"]);
  renderCheckboxGroup($("metric-select"), options.metrics || [], "metric", [
    "wer",
    "cer",
    "latency_ms",
    "rtf",
  ]);

  await refreshFiles();
  await refreshJobs();
  setStatus("Ready");
}

function bindEvents() {
  $("run-preflight").onclick = async () => {
    try {
      await runPreflight();
    } catch (error) {
      setStatus(`Preflight failed: ${error.message}`);
    }
  };

  $("refresh-all").onclick = async () => {
    await refreshFiles();
    await refreshJobs();
    await loadSelectedJob();
    setStatus("Refreshed");
  };

  $("run-live").onclick = async () => {
    try {
      await runLiveSample();
    } catch (error) {
      setStatus(`Live run failed: ${error.message}`);
    }
  };

  $("run-benchmark").onclick = async () => {
    try {
      await runBenchmark();
    } catch (error) {
      setStatus(`Benchmark failed: ${error.message}`);
    }
  };

  $("start-bringup").onclick = async () => {
    try {
      await startBringup();
    } catch (error) {
      setStatus(`Bringup failed: ${error.message}`);
    }
  };

  $("upload-form").addEventListener("submit", async (event) => {
    try {
      await uploadFile(event);
    } catch (error) {
      setStatus(`Upload failed: ${error.message}`);
    }
  });

  $("apply-noise").onclick = async () => {
    try {
      await applyNoise();
    } catch (error) {
      setStatus(`Noise failed: ${error.message}`);
    }
  };

  $("save-profile").onclick = async () => {
    try {
      await saveProfile();
    } catch (error) {
      setStatus(`Save profile failed: ${error.message}`);
    }
  };

  $("load-profile").onclick = async () => {
    try {
      await loadProfile();
    } catch (error) {
      setStatus(`Load profile failed: ${error.message}`);
    }
  };
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await bootstrap();
    await runPreflight();
  } catch (error) {
    setStatus(`Init failed: ${error.message}`);
  }

  setInterval(async () => {
    try {
      await refreshJobs();
      await loadSelectedJob();
    } catch (_error) {
      // Keep polling resilient.
    }
  }, 3000);
});
