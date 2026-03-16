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

function renderAwsAuthSummary(ui, awsRef) {
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

  const tableRoot = document.getElementById('secretsRefsTable');
  const providerProfileSelect = document.getElementById('secretLinkProviderProfile');
  const awsAuthSummaryRoot = document.getElementById('awsAuthSummary');
  const googleAuthSummaryRoot = document.getElementById('googleAuthSummary');
  const azureAuthSummaryRoot = document.getElementById('azureAuthSummary');
  const awsProfileInput = document.getElementById('awsSsoProfile');
  const awsRefInput = document.getElementById('awsSsoRefName');
  const awsFeedbackId = 'awsSsoLoginFeedback';
  const googleFeedbackId = 'googleSetupFeedback';
  const azureFeedbackId = 'azureSetupFeedback';
  const azureRegionInput = document.getElementById('azureSpeechRegion');
  const azureEndpointInput = document.getElementById('azureSpeechEndpoint');

  let currentRefs = [];
  let awsLoginJobId = '';

  async function refreshProviderProfiles() {
    const profiles = await api.profilesByType('providers');
    ui.updateSelectOptions(providerProfileSelect, profiles.profiles || []);
  }

  function renderRefs(refs) {
    currentRefs = refs;
    if (!refs.length) {
      tableRoot.innerHTML = ui.renderEmpty('No secret refs found in secrets/refs.');
      awsAuthSummaryRoot.innerHTML = ui.renderEmpty('AWS auth state will appear here once `aws_profile` exists.');
      googleAuthSummaryRoot.innerHTML = ui.renderEmpty('Google auth state will appear here once `google_service_account` exists.');
      azureAuthSummaryRoot.innerHTML = ui.renderEmpty('Azure auth state will appear here once `azure_speech_key` exists.');
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
    if (!awsLoginJobId) {
      if (showToast) {
        ui.toast('No AWS login job is active yet.', 'info');
      }
      return null;
    }
    const payload = await api.secretsAwsSsoLoginStatus(awsLoginJobId);
    const job = payload.job || null;
    const awsRef = currentRefs.find((row) => row.name === 'aws_profile') || null;
    const baseHtml = renderAwsAuthSummary(ui, awsRef);
    awsAuthSummaryRoot.innerHTML = `${baseHtml}${renderAwsLoginJob(ui, job)}`;
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

  document.getElementById('secretSaveBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback('secretsFeedback', error.message, 'error');
      ui.toast(`Save ref failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('secretValidateBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.secretsValidateRef({
        ref_name: document.getElementById('secretValidateName').value,
      });
      ui.setFeedback('secretsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Secret ref validated', payload.validation?.valid ? 'success' : 'error');
      await refreshRefs();
    } catch (error) {
      ui.setFeedback('secretsFeedback', error.message, 'error');
      ui.toast(`Validation failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('secretLinkBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.secretsLinkProvider({
        provider_profile: providerProfileSelect.value,
        ref_name: document.getElementById('secretValidateName').value,
      });
      ui.setFeedback('secretsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Credential ref linked to provider profile', 'success');
      await refreshRefs();
    } catch (error) {
      ui.setFeedback('secretsFeedback', error.message, 'error');
      ui.toast(`Link failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('awsSsoLoginBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.secretsAwsSsoLoginStart({
        ref_name: awsRefInput?.value || 'aws_profile',
        profile: awsProfileInput?.value || '',
        use_device_code: Boolean(document.getElementById('awsSsoUseDeviceCode')?.checked),
        no_browser: Boolean(document.getElementById('awsSsoNoBrowser')?.checked),
      });
      awsLoginJobId = payload.job?.job_id || '';
      ui.setFeedback(awsFeedbackId, JSON.stringify(payload.job || payload, null, 2));
      ui.toast('AWS login started. Follow the device/browser instructions below.', 'success', 5000);
      await refreshAwsLoginStatus(false);
    } catch (error) {
      ui.setFeedback(awsFeedbackId, error.message, 'error');
      ui.toast(`AWS login start failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('awsSsoRefreshBtn')?.addEventListener('click', async () => {
    try {
      await refreshAwsLoginStatus(true);
    } catch (error) {
      ui.setFeedback(awsFeedbackId, error.message, 'error');
      ui.toast(`AWS login refresh failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('awsSsoCancelBtn')?.addEventListener('click', async () => {
    try {
      if (!awsLoginJobId) {
        ui.toast('No AWS login job is active.', 'info');
        return;
      }
      const payload = await api.secretsAwsSsoLoginCancel(awsLoginJobId);
      ui.setFeedback(awsFeedbackId, JSON.stringify(payload.job || payload, null, 2));
      ui.toast('AWS login cancelled', 'warning');
      await refreshRefs();
      awsLoginJobId = '';
    } catch (error) {
      ui.setFeedback(awsFeedbackId, error.message, 'error');
      ui.toast(`AWS login cancel failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('googleUploadBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback(googleFeedbackId, error.message, 'error');
      ui.toast(`Google upload failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('googleClearBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.secretsGoogleClear({
        ref_name: document.getElementById('googleRefName').value || 'google_service_account',
      });
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google credential file cleared', 'warning');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    } catch (error) {
      ui.setFeedback(googleFeedbackId, error.message, 'error');
      ui.toast(`Google clear failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('googleValidateProviderBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersValidate({
        provider_profile: document.getElementById('googleProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
      });
      ui.setFeedback(googleFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Google provider validation completed', payload.valid ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshGoogleState()]);
    } catch (error) {
      ui.setFeedback(googleFeedbackId, error.message, 'error');
      ui.toast(`Google validation failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('googleTestProviderBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback(googleFeedbackId, error.message, 'error');
      ui.toast(`Google test failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('azureSaveBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback(azureFeedbackId, error.message, 'error');
      ui.toast(`Azure save failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('azureClearBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback(azureFeedbackId, error.message, 'error');
      ui.toast(`Azure clear failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('azureValidateProviderBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersValidate({
        provider_profile: document.getElementById('azureProviderProfile').value,
        provider_preset: '',
        provider_settings: {},
      });
      ui.setFeedback(azureFeedbackId, JSON.stringify(payload, null, 2));
      ui.toast('Azure provider validation completed', payload.valid ? 'success' : 'error');
      await Promise.all([refreshRefs(), refreshAzureState()]);
    } catch (error) {
      ui.setFeedback(azureFeedbackId, error.message, 'error');
      ui.toast(`Azure validation failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('azureTestProviderBtn')?.addEventListener('click', async () => {
    try {
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
    } catch (error) {
      ui.setFeedback(azureFeedbackId, error.message, 'error');
      ui.toast(`Azure test failed: ${error.message}`, 'error');
    }
  });

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
