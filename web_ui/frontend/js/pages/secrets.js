import { createActionRunner } from '../action-runner.js';

// Secrets page shows credential readiness and recovery actions without exposing
// raw secret material back to the browser after upload/save operations.
function splitCsv(raw) {
  return String(raw || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderAuthFlag(ui, label, value, tone = '') {
  const state = tone || (value ? 'valid' : 'invalid');
  return `<div class="stack-item"><strong>${ui.escapeHtml(label)}</strong><p><span class="${ui.statusBadgeClass(state)}">${ui.escapeHtml(
    value ? 'yes' : 'no'
  )}</span></p></div>`;
}

function awsDeviceLoginPageUrl(startUrl) {
  const text = String(startUrl || '').trim();
  if (!text) {
    return '';
  }
  if (text.includes('#/device')) {
    return text;
  }
  const normalized = text.replace(/\/+$/, '');
  if (normalized.endsWith('/start')) {
    return `${normalized}/#/device`;
  }
  return text;
}

function currentAwsRef(refs, refName = 'aws_profile') {
  const preferred = String(refName || '').trim() || 'aws_profile';
  return refs.find((row) => row.name === preferred) || refs.find((row) => row.name === 'aws_profile') || null;
}

async function copyText(value) {
  const text = String(value || '').trim();
  if (!text) {
    throw new Error('Nothing to copy');
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const helper = document.createElement('textarea');
  helper.value = text;
  helper.setAttribute('readonly', 'readonly');
  helper.style.position = 'absolute';
  helper.style.left = '-9999px';
  document.body.appendChild(helper);
  helper.select();
  document.execCommand('copy');
  helper.remove();
}

function renderAwsAuthSummary(ui, awsRef) {
  // AWS is modeled as more than "valid/invalid" because SSO sign-in state and
  // short-lived role credentials can expire at different times.
  if (!awsRef) {
    return ui.renderEmpty('AWS secret ref not found. Create or restore `aws_profile` first.');
  }

  const validation = awsRef.validation || {};
  const auth = validation.auth || {};
  if (!Object.keys(auth).length) {
    return ui.renderEmpty('AWS auth details are not available for this ref yet.');
  }

  const summary = [
    { key: 'Overall ref validation', value: validation.valid ? 'valid' : 'invalid', tone: validation.valid ? 'valid' : 'invalid' },
    {
      key: 'Auth state',
      value: auth.status || 'unknown',
      tone: auth.runtime_ready ? (auth.login_recommended ? 'warning' : 'valid') : auth.login_recommended ? 'warning' : 'invalid',
    },
    { key: 'AWS profile', value: auth.profile || 'not set' },
    { key: 'Region', value: auth.region || 'not set' },
    { key: 'Runtime ready', value: auth.runtime_ready ? 'yes' : 'no', tone: auth.runtime_ready ? 'valid' : 'invalid' },
    { key: 'SSO start URL', value: auth.sso_start_url || 'not set' },
    { key: 'SSO sign-in session expires', value: ui.fmtDate(auth.sso_session_expires_at) },
    { key: 'Role credentials expire', value: ui.fmtDate(auth.role_credentials_expires_at) },
    { key: 'Login command', value: auth.login_command || 'n/a' },
  ];

  return `
    <div class="stack-item">
      <strong>${ui.escapeHtml(auth.message || 'AWS auth state')}</strong>
      <p>${ui.escapeHtml(
        auth.runtime_ready
          ? 'Runtime and benchmark requests can use the current role credentials.'
          : 'A new IAM Identity Center / SSO login is needed before AWS-backed runs can start.'
      )}</p>
    </div>
    ${summary
      .map(
        (item) => `
          <div class="stack-item">
            <strong>${ui.escapeHtml(item.key)}</strong>
            <p>${item.tone ? `<span class="${ui.statusBadgeClass(item.tone)}">${ui.escapeHtml(item.value)}</span>` : ui.escapeHtml(item.value)}</p>
          </div>
        `
      )
      .join('')}
    ${renderAuthFlag(ui, 'Uses SSO / IAM Identity Center', Boolean(auth.uses_sso), auth.uses_sso ? 'valid' : 'invalid')}
    ${renderAuthFlag(ui, 'SSO sign-in session valid', Boolean(auth.sso_session_valid), auth.sso_session_valid ? 'valid' : 'warning')}
    ${renderAuthFlag(ui, 'Role credentials valid', Boolean(auth.role_credentials_valid), auth.role_credentials_valid ? 'valid' : 'invalid')}
  `;
}

function renderAwsLoginJob(ui, job) {
  if (!job) {
    return '';
  }
  const lines = Array.isArray(job.lines) ? job.lines : [];
  return `
    <div class="stack-item">
      <strong>AWS login job</strong>
      <p><span class="${ui.statusBadgeClass(job.state || 'idle')}">${ui.escapeHtml(job.state || 'idle')}</span></p>
      <p>profile=${ui.escapeHtml(job.profile || '')}</p>
      <p>started=${ui.escapeHtml(ui.fmtDate(job.started_at))}</p>
      <p>completed=${ui.escapeHtml(ui.fmtDate(job.completed_at))}</p>
      <p>return_code=${ui.escapeHtml(String(job.return_code ?? 'pending'))}</p>
      <p>command=${ui.escapeHtml((job.command || []).join(' '))}</p>
      <p>login_page=${ui.escapeHtml(job.login_page_url || job.verification_uri || 'waiting')}</p>
      <p>device_code=${ui.escapeHtml(job.user_code || 'waiting')}</p>
      <pre>${ui.escapeHtml(lines.join('\n') || 'Waiting for CLI output...')}</pre>
    </div>
  `;
}

function renderGoogleAuthSummary(ui, googleRef) {
  if (!googleRef) {
    return ui.renderEmpty('Google secret ref not found. Create or restore `google_service_account` first.');
  }

  const validation = googleRef.validation || {};
  const auth = validation.auth || {};
  if (!Object.keys(auth).length) {
    return ui.renderEmpty('Google auth details are not available for this ref yet.');
  }

  const tone = auth.runtime_ready ? 'valid' : 'invalid';
  return `
    <div class="stack-item">
      <strong>${ui.escapeHtml(auth.message || 'Google auth state')}</strong>
      <p>${ui.escapeHtml(
        auth.runtime_ready
          ? 'Google service-account credentials are ready for provider validation and runtime use.'
          : 'Google still needs a valid service-account JSON file.'
      )}</p>
    </div>
    <div class="stack-item">
      <strong>Overall state</strong>
      <p><span class="${ui.statusBadgeClass(tone)}">${ui.escapeHtml(auth.runtime_ready ? 'ready' : 'missing_credentials')}</span></p>
    </div>
    <div class="stack-item">
      <strong>Credential file</strong>
      <p>${ui.escapeHtml(auth.file_path || 'not set')}</p>
      <p class="muted">source=${ui.escapeHtml(auth.file_source || 'missing')}</p>
    </div>
    <div class="stack-item">
      <strong>Project</strong>
      <p>${ui.escapeHtml(auth.project_id || 'unknown')}</p>
    </div>
    <div class="stack-item">
      <strong>Service account</strong>
      <p>${ui.escapeHtml(auth.client_email_masked || 'unknown')}</p>
    </div>
    <div class="stack-item">
      <strong>Credential type</strong>
      <p>${ui.escapeHtml(auth.credential_type || 'unknown')}</p>
    </div>
  `;
}

function renderAzureAuthSummary(ui, azureRef) {
  if (!azureRef) {
    return ui.renderEmpty('Azure secret ref not found. Create or restore `azure_speech_key` first.');
  }

  const validation = azureRef.validation || {};
  const auth = validation.auth || {};
  if (!Object.keys(auth).length) {
    return ui.renderEmpty('Azure auth details are not available for this ref yet.');
  }

  const tone = auth.runtime_ready ? 'valid' : 'invalid';
  return `
    <div class="stack-item">
      <strong>${ui.escapeHtml(auth.message || 'Azure auth state')}</strong>
      <p>${ui.escapeHtml(
        auth.runtime_ready
          ? 'Azure credentials are available for provider validation and runtime session startup.'
          : 'Azure still needs a speech key and a region before the provider can start.'
      )}</p>
    </div>
    <div class="stack-item">
      <strong>Overall state</strong>
      <p><span class="${ui.statusBadgeClass(tone)}">${ui.escapeHtml(auth.runtime_ready ? 'ready' : 'missing_credentials')}</span></p>
    </div>
    <div class="stack-item">
      <strong>Speech key</strong>
      <p>${ui.escapeHtml(auth.speech_key_masked || 'not set')}</p>
      <p class="muted">source=${ui.escapeHtml(auth.speech_key_source || 'missing')}</p>
    </div>
    <div class="stack-item">
      <strong>Region</strong>
      <p>${ui.escapeHtml(auth.region || 'not set')}</p>
      <p class="muted">source=${ui.escapeHtml(auth.region_source || 'missing')}</p>
    </div>
    <div class="stack-item">
      <strong>Endpoint</strong>
      <p>${ui.escapeHtml(auth.endpoint || 'not set')}</p>
      <p class="muted">source=${ui.escapeHtml(auth.endpoint_source || 'missing')} · mode=${ui.escapeHtml(auth.endpoint_mode || 'none')}</p>
    </div>
    <div class="stack-item">
      <strong>Local env file</strong>
      <p>${ui.escapeHtml(auth.local_env_file || 'n/a')}</p>
      <p class="muted">${ui.escapeHtml(auth.local_env_file_exists ? 'exists' : 'not created yet')}</p>
    </div>
  `;
}

export function initSecretsPage(ctx) {
  const { api, ui } = ctx;
  const runSecretsAction = createActionRunner({ ui });

  const tableRoot = document.getElementById('secretsRefsTable');
  const providerProfileSelect = document.getElementById('secretLinkProviderProfile');
  const awsAuthSummaryRoot = document.getElementById('awsAuthSummary');
  const googleAuthSummaryRoot = document.getElementById('googleAuthSummary');
  const azureAuthSummaryRoot = document.getElementById('azureAuthSummary');
  const awsProfileInput = document.getElementById('awsSsoProfile');
  const awsRefInput = document.getElementById('awsSsoRefName');
  const awsLoginUrlInput = document.getElementById('awsSsoLoginUrl');
  const awsDeviceCodeInput = document.getElementById('awsSsoDeviceCode');
  const awsAutoOpenCheckbox = document.getElementById('awsSsoAutoOpenPage');
  const awsOpenLoginPageBtn = document.getElementById('awsSsoOpenLoginPageBtn');
  const awsCopyLoginPageBtn = document.getElementById('awsSsoCopyLoginPageBtn');
  const awsCopyDeviceCodeBtn = document.getElementById('awsSsoCopyDeviceCodeBtn');
  const awsFeedbackId = 'awsSsoLoginFeedback';
  const googleFeedbackId = 'googleSetupFeedback';
  const azureFeedbackId = 'azureSetupFeedback';
  const azureRegionInput = document.getElementById('azureSpeechRegion');
  const azureEndpointInput = document.getElementById('azureSpeechEndpoint');

  let currentRefs = [];
  let awsLoginJobId = '';
  let awsLastLoginJob = null;

  function awsLoginHints(job = null, awsRef = null) {
    const auth = awsRef?.validation?.auth || {};
    const loginPageUrl = String(
      job?.login_page_url || awsDeviceLoginPageUrl(auth.sso_start_url) || job?.verification_uri || ''
    ).trim();
    const deviceCode = String(job?.user_code || '').trim();
    return { loginPageUrl, deviceCode };
  }

  function syncAwsLoginFields(job = null, awsRef = null) {
    const { loginPageUrl, deviceCode } = awsLoginHints(job, awsRef);
    if (awsLoginUrlInput) {
      awsLoginUrlInput.value = loginPageUrl;
    }
    if (awsDeviceCodeInput) {
      awsDeviceCodeInput.value = deviceCode;
    }
    if (awsOpenLoginPageBtn) {
      awsOpenLoginPageBtn.disabled = !loginPageUrl;
    }
    if (awsCopyLoginPageBtn) {
      awsCopyLoginPageBtn.disabled = !loginPageUrl;
    }
    if (awsCopyDeviceCodeBtn) {
      awsCopyDeviceCodeBtn.disabled = !deviceCode;
    }
    return { loginPageUrl, deviceCode };
  }

  function openAwsLoginPage(url) {
    const targetUrl = String(url || '').trim();
    if (!targetUrl) {
      ui.toast('AWS login page is not available yet.', 'warning');
      return null;
    }
    return window.open(targetUrl, '_blank', 'noopener');
  }

  async function refreshProviderProfiles() {
    const profiles = await api.profilesByType('providers');
    ui.updateSelectOptions(providerProfileSelect, profiles.profiles || []);
  }

  function renderRefs(refs) {
    // This table is metadata-only on purpose: enough to explain readiness and
    // linkage, but not enough to leak private credential contents.
    currentRefs = refs;
    if (!refs.length) {
      tableRoot.innerHTML = ui.renderEmpty('No secret refs found in secrets/refs.');
      awsAuthSummaryRoot.innerHTML = ui.renderEmpty('AWS auth state will appear here once `aws_profile` exists.');
      googleAuthSummaryRoot.innerHTML = ui.renderEmpty('Google auth state will appear here once `google_service_account` exists.');
      azureAuthSummaryRoot.innerHTML = ui.renderEmpty('Azure auth state will appear here once `azure_speech_key` exists.');
      syncAwsLoginFields(awsLastLoginJob, null);
      return;
    }

    tableRoot.innerHTML = ui.table(
      [
        { key: 'name', label: 'Ref Name', value: (row) => ui.toCode(row.name) },
        { key: 'provider', label: 'Provider', value: (row) => ui.escapeHtml(row.validation?.provider || '') },
        { key: 'kind', label: 'Kind', value: (row) => ui.escapeHtml(row.validation?.kind || '') },
        {
          key: 'valid',
          label: 'Validation',
          value: (row) => {
            const valid = row.validation?.valid;
            return `<span class="${ui.statusBadgeClass(valid ? 'valid' : 'invalid')}">${valid ? 'valid' : 'invalid'}</span>`;
          },
        },
        {
          key: 'state',
          label: 'Auth State',
          value: (row) => {
            const auth = row.validation?.auth || {};
            const state = auth.status || 'n/a';
            const tone = auth.runtime_ready ? (auth.login_recommended ? 'warning' : 'valid') : auth.login_recommended ? 'warning' : row.validation?.valid ? 'valid' : 'invalid';
            return `<span class="${ui.statusBadgeClass(tone)}">${ui.escapeHtml(state)}</span>`;
          },
        },
        {
          key: 'issues',
          label: 'Issues / Message',
          value: (row) => {
            const authMessage = row.validation?.auth?.message || '';
            const issues = (row.validation?.issues || []).join('; ');
            return ui.escapeHtml(issues || authMessage || 'none');
          },
        },
        {
          key: 'linked',
          label: 'Linked Profiles',
          value: (row) => ui.escapeHtml((row.linked_provider_profiles || []).join(', ') || 'none'),
        },
      ],
      refs
    );

    const awsRef = refs.find((row) => row.name === 'aws_profile') || null;
    const googleRef = refs.find((row) => row.name === 'google_service_account') || null;
    const azureRef = refs.find((row) => row.name === 'azure_speech_key') || null;
    awsAuthSummaryRoot.innerHTML = renderAwsAuthSummary(ui, awsRef);
    googleAuthSummaryRoot.innerHTML = renderGoogleAuthSummary(ui, googleRef);
    azureAuthSummaryRoot.innerHTML = renderAzureAuthSummary(ui, azureRef);
    syncAwsLoginFields(awsLastLoginJob, currentAwsRef(refs, awsRefInput?.value || 'aws_profile'));
    if (awsRef?.validation?.auth?.profile && awsProfileInput && !String(awsProfileInput.value || '').trim()) {
      awsProfileInput.value = awsRef.validation.auth.profile;
    }
    if (awsRefInput && !String(awsRefInput.value || '').trim()) {
      awsRefInput.value = 'aws_profile';
    }
    if (azureRef?.validation?.auth?.region && azureRegionInput && !String(azureRegionInput.value || '').trim()) {
      azureRegionInput.value = azureRef.validation.auth.region;
    }
    if (azureRef?.validation?.auth?.endpoint && azureEndpointInput && !String(azureEndpointInput.value || '').trim()) {
      azureEndpointInput.value = azureRef.validation.auth.endpoint;
    }
  }

  async function refreshRefs() {
    const payload = await api.secretsRefs();
    renderRefs(payload.refs || []);
    return payload.refs || [];
  }

  async function refreshGoogleState() {
    const payload = await api.secretsGoogleStatus();
    const googleRef = {
      name: payload.ref_name,
      validation: payload.validation || {},
    };
    googleAuthSummaryRoot.innerHTML = renderGoogleAuthSummary(ui, googleRef);
    return payload;
  }

  async function refreshAzureState() {
    const payload = await api.secretsAzureEnv();
    const azureRef = {
      name: payload.ref_name,
      validation: payload.validation || {},
    };
    azureAuthSummaryRoot.innerHTML = renderAzureAuthSummary(ui, azureRef);
    return payload;
  }

  async function refreshAwsLoginStatus(showToast = false) {
    // AWS login runs as a background job because it may wait on CLI/browser
    // interaction and should remain observable from the UI.
    if (!awsLoginJobId) {
      if (showToast) {
        ui.toast('No AWS login job is active yet.', 'info');
      }
      return null;
    }
    const payload = await api.secretsAwsSsoLoginStatus(awsLoginJobId);
    const job = payload.job || null;
    awsLastLoginJob = job;
    const awsRef = currentAwsRef(currentRefs, awsRefInput?.value || 'aws_profile');
    const baseHtml = renderAwsAuthSummary(ui, awsRef);
    awsAuthSummaryRoot.innerHTML = `${baseHtml}${renderAwsLoginJob(ui, job)}`;
    syncAwsLoginFields(job, awsRef);
    ui.setFeedback(awsFeedbackId, JSON.stringify(job, null, 2));
    if (job && job.state !== 'running') {
      await refreshRefs();
      if (showToast) {
        ui.toast(
          job.state === 'completed' ? 'AWS login completed' : 'AWS login failed',
          job.state === 'completed' ? 'success' : 'error'
        );
      }
    }
    return job;
  }

  document.getElementById('secretSaveBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsSaveRef({
        file_name: document.getElementById('secretFileName').value,
        ref_id: document.getElementById('secretRefId').value,
        provider: document.getElementById('secretProvider').value,
        kind: document.getElementById('secretKind').value,
        path: document.getElementById('secretPath').value,
        env_fallback: document.getElementById('secretEnvFallback').value,
        required: splitCsv(document.getElementById('secretRequired').value),
        optional: splitCsv(document.getElementById('secretOptional').value),
        masked: true,
      });
      ui.setFeedback('secretsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Secret ref saved', 'success');
      await refreshRefs();
    }, {
      feedbackId: 'secretsFeedback',
      errorPrefix: 'Save ref failed',
    })
  );

  document.getElementById('secretValidateBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsValidateRef({
        ref_name: document.getElementById('secretValidateName').value,
      });
      ui.setFeedback('secretsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Secret ref validated', payload.validation?.valid ? 'success' : 'error');
      await refreshRefs();
    }, {
      feedbackId: 'secretsFeedback',
      errorPrefix: 'Validation failed',
    })
  );

  document.getElementById('secretLinkBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsLinkProvider({
        provider_profile: providerProfileSelect.value,
        ref_name: document.getElementById('secretValidateName').value,
      });
      ui.setFeedback('secretsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Credential ref linked to provider profile', 'success');
      await refreshRefs();
    }, {
      feedbackId: 'secretsFeedback',
      errorPrefix: 'Link failed',
    })
  );

  awsOpenLoginPageBtn?.addEventListener('click', () => {
    openAwsLoginPage(awsLoginUrlInput?.value || '');
  });

  awsCopyLoginPageBtn?.addEventListener('click', async () => {
    try {
      await copyText(awsLoginUrlInput?.value || '');
      ui.toast('AWS login URL copied', 'success');
    } catch (error) {
      ui.toast(error instanceof Error ? error.message : String(error), 'warning');
    }
  });

  awsCopyDeviceCodeBtn?.addEventListener('click', async () => {
    try {
      await copyText(awsDeviceCodeInput?.value || '');
      ui.toast('AWS device code copied', 'success');
    } catch (error) {
      ui.toast(error instanceof Error ? error.message : String(error), 'warning');
    }
  });

  document.getElementById('awsSsoLoginBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const refName = awsRefInput?.value || 'aws_profile';
      const awsRef = currentAwsRef(currentRefs, refName);
      const autoOpenEnabled = Boolean(awsAutoOpenCheckbox?.checked);
      const initialUrl = autoOpenEnabled ? awsLoginHints(null, awsRef).loginPageUrl : '';
      const popup = autoOpenEnabled && initialUrl ? openAwsLoginPage(initialUrl) : null;
      const payload = await api.secretsAwsSsoLoginStart({
        ref_name: refName,
        profile: awsProfileInput?.value || '',
        use_device_code: Boolean(document.getElementById('awsSsoUseDeviceCode')?.checked),
        no_browser: true,
      });
      awsLoginJobId = payload.job?.job_id || '';
      awsLastLoginJob = payload.job || null;
      const hints = syncAwsLoginFields(payload.job || null, awsRef);
      if (autoOpenEnabled && hints.loginPageUrl) {
        if (popup && !popup.closed && hints.loginPageUrl !== initialUrl) {
          popup.location.replace(hints.loginPageUrl);
        } else if (!popup) {
          openAwsLoginPage(hints.loginPageUrl);
        }
      }
      ui.setFeedback(awsFeedbackId, JSON.stringify(payload.job || payload, null, 2));
      ui.toast('AWS login started. Follow the device/browser instructions below.', 'success', 5000);
      await refreshAwsLoginStatus(false);
    }, {
      feedbackId: awsFeedbackId,
      errorPrefix: 'AWS login start failed',
    })
  );

  document.getElementById('awsSsoRefreshBtn')?.addEventListener('click', () =>
    runSecretsAction(() => refreshAwsLoginStatus(true), {
      feedbackId: awsFeedbackId,
      errorPrefix: 'AWS login refresh failed',
    })
  );

  document.getElementById('awsSsoCancelBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      if (!awsLoginJobId) {
        ui.toast('No AWS login job is active.', 'info');
        return;
      }
      const payload = await api.secretsAwsSsoLoginCancel(awsLoginJobId);
      awsLastLoginJob = payload.job || null;
      syncAwsLoginFields(payload.job || null, currentAwsRef(currentRefs, awsRefInput?.value || 'aws_profile'));
      ui.setFeedback(awsFeedbackId, JSON.stringify(payload.job || payload, null, 2));
      ui.toast('AWS login cancelled', 'warning');
      await refreshRefs();
      awsLoginJobId = '';
    }, {
      feedbackId: awsFeedbackId,
      errorPrefix: 'AWS login cancel failed',
    })
  );

  document.getElementById('googleUploadBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const fileInput = document.getElementById('googleServiceAccountFile');
      const file = fileInput?.files?.[0] || null;
      if (!file) {
        ui.toast('Choose a Google service-account JSON file first.', 'warning');
        return;
      }
      const payload = await api.secretsGoogleUpload({
        file,
        ref_name: document.getElementById('googleRefName').value || 'google_service_account',
      });
      if (fileInput) {
        fileInput.value = '';
      }
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google service-account JSON uploaded', 'success');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    }, {
      feedbackId: googleFeedbackId,
      errorPrefix: 'Google upload failed',
    })
  );

  document.getElementById('googleClearBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsGoogleClear({
        ref_name: document.getElementById('googleRefName').value || 'google_service_account',
      });
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google credential file cleared', 'warning');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    }, {
      feedbackId: googleFeedbackId,
      errorPrefix: 'Google clear failed',
    })
  );

  document.getElementById('googleValidateProviderBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.providersValidate({
        provider_profile: document.getElementById('googleProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
      });
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google provider validation completed', payload.valid ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    }, {
      feedbackId: googleFeedbackId,
      errorPrefix: 'Google validation failed',
    })
  );

  document.getElementById('googleTestProviderBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.providersTest({
        provider_profile: document.getElementById('googleProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
        wav_path: document.getElementById('googleTestWav').value,
        language: document.getElementById('googleTestLanguage').value,
      });
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google provider test completed', payload.success ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    }, {
      feedbackId: googleFeedbackId,
      errorPrefix: 'Google test failed',
    })
  );

  document.getElementById('azureSaveBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsAzureEnvSave({
        ref_name: 'azure_speech_key',
        speech_key: document.getElementById('azureSpeechKey').value,
        region: document.getElementById('azureSpeechRegion').value,
        endpoint: document.getElementById('azureSpeechEndpoint').value,
      });
      document.getElementById('azureSpeechKey').value = '';
      ui.setFeedback(azureFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Azure credentials saved to local env injection file', 'success');
      await Promise.all([refreshRefs(), refreshAzureState()]);
    }, {
      feedbackId: azureFeedbackId,
      errorPrefix: 'Azure save failed',
    })
  );

  document.getElementById('azureClearBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.secretsAzureEnvSave({
        ref_name: 'azure_speech_key',
        clear_speech_key: true,
        clear_region: true,
        clear_endpoint: true,
      });
      document.getElementById('azureSpeechKey').value = '';
      document.getElementById('azureSpeechRegion').value = '';
      document.getElementById('azureSpeechEndpoint').value = '';
      ui.setFeedback(azureFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Azure local env injection cleared', 'warning');
      await Promise.all([refreshRefs(), refreshAzureState()]);
    }, {
      feedbackId: azureFeedbackId,
      errorPrefix: 'Azure clear failed',
    })
  );

  document.getElementById('azureValidateProviderBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.providersValidate({
        provider_profile: document.getElementById('azureProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
      });
      ui.setFeedback(azureFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Azure provider validation completed', payload.valid ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshAzureState()]);
    }, {
      feedbackId: azureFeedbackId,
      errorPrefix: 'Azure validation failed',
    })
  );

  document.getElementById('azureTestProviderBtn')?.addEventListener('click', () =>
    runSecretsAction(async () => {
      const payload = await api.providersTest({
        provider_profile: document.getElementById('azureProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
        wav_path: document.getElementById('azureTestWav').value,
        language: document.getElementById('azureTestLanguage').value,
      });
      ui.setFeedback(azureFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Azure provider test completed', payload.success ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshAzureState()]);
    }, {
      feedbackId: azureFeedbackId,
      errorPrefix: 'Azure test failed',
    })
  );

  return {
    refresh: async () => {
      await Promise.all([refreshProviderProfiles(), refreshRefs(), refreshGoogleState(), refreshAzureState()]);
      if (awsLoginJobId) {
        await refreshAwsLoginStatus(false);
      }
    },
    poll: async () => {
      if (!awsLoginJobId) {
        return;
      }
      const job = await refreshAwsLoginStatus(false);
      if (job && job.state !== 'running') {
        awsLoginJobId = '';
      }
    },
  };
}
