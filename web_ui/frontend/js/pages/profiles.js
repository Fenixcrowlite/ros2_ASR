function getPathValue(payload, path, fallback = '') {
  const parts = path.split('.');
  let cursor = payload;
  for (const part of parts) {
    if (!cursor || typeof cursor !== 'object' || !(part in cursor)) {
      return fallback;
    }
    cursor = cursor[part];
  }
  return cursor;
}

function setPathValue(payload, path, value) {
  const parts = path.split('.');
  let cursor = payload;
  for (const part of parts.slice(0, -1)) {
    if (!cursor[part] || typeof cursor[part] !== 'object') {
      cursor[part] = {};
    }
    cursor = cursor[part];
  }
  cursor[parts[parts.length - 1]] = value;
}

function guidedFieldsForType(type) {
  if (type === 'runtime') {
    return [
      { id: 'orchestrator.language', label: 'Language', type: 'text' },
      { id: 'orchestrator.provider_profile', label: 'Provider profile', type: 'text' },
      { id: 'audio.source', label: 'Audio source', type: 'text' },
      { id: 'audio.file_path', label: 'Audio file path', type: 'text' },
      { id: 'vad.energy_threshold', label: 'VAD energy threshold', type: 'number' },
      { id: 'orchestrator.enable_partials', label: 'Enable partials', type: 'checkbox' },
    ];
  }
  if (type === 'providers') {
    return [
      { id: 'provider_id', label: 'Provider ID', type: 'text' },
      { id: 'credentials_ref', label: 'Credential ref path', type: 'text' },
      { id: 'settings.model_size', label: 'Model size', type: 'text' },
      { id: 'settings.device', label: 'Device', type: 'text' },
    ];
  }
  if (type === 'benchmark') {
    return [
      { id: 'dataset_profile', label: 'Dataset profile', type: 'text' },
      { id: 'providers', label: 'Providers (comma separated)', type: 'csv' },
      { id: 'metric_profiles', label: 'Metric profiles (comma separated)', type: 'csv' },
      { id: 'batch.timeout_sec', label: 'Batch timeout sec', type: 'number' },
    ];
  }
  if (type === 'datasets') {
    return [
      { id: 'dataset_id', label: 'Dataset ID', type: 'text' },
      { id: 'manifest_path', label: 'Manifest path', type: 'text' },
      { id: 'default_language', label: 'Default language', type: 'text' },
    ];
  }
  if (type === 'metrics') {
    return [{ id: 'metrics', label: 'Metrics (comma separated)', type: 'csv' }];
  }
  if (type === 'deployment') {
    return [
      { id: 'runtime_defaults.namespace_prefix', label: 'Namespace prefix', type: 'text' },
      { id: 'runtime_defaults.log_level', label: 'Log level', type: 'text' },
    ];
  }
  return [];
}

function parseGuidedValue(field, input) {
  if (field.type === 'number') {
    return Number(input.value);
  }
  if (field.type === 'checkbox') {
    return Boolean(input.checked);
  }
  if (field.type === 'csv') {
    return String(input.value || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return input.value;
}

export function initProfilesPage(ctx) {
  const { api, ui, state } = ctx;

  const typeSelect = document.getElementById('profilesTypeSelect');
  const listRoot = document.getElementById('profilesList');
  const guidedRoot = document.getElementById('profilesGuidedForm');
  const rawEditor = document.getElementById('profileRawEditor');

  let listCache = [];
  let guidedFields = [];

  function currentType() {
    return typeSelect.value;
  }

  function renderList() {
    if (!listCache.length) {
      listRoot.innerHTML = ui.renderEmpty('No profiles found for selected type.');
      return;
    }

    listRoot.innerHTML = listCache
      .map(
        (item) => `
          <div class="stack-item">
            <div class="actions-row">
              <strong>${ui.escapeHtml(item.profile_id)}</strong>
              <span class="${ui.statusBadgeClass(item.valid ? 'valid' : 'invalid')}">${item.valid ? 'valid' : 'invalid'}</span>
              <button class="btn-secondary" data-open-profile="${ui.escapeHtml(item.profile_id)}">Open</button>
            </div>
            <p>${ui.escapeHtml(item.validation_message || '')}</p>
            <p class="muted">updated: ${ui.fmtDate(item.last_modified)}</p>
          </div>
        `
      )
      .join('');

    listRoot.querySelectorAll('button[data-open-profile]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const profileId = btn.getAttribute('data-open-profile');
        if (!profileId) {
          return;
        }
        await openProfile(currentType(), profileId);
      });
    });
  }

  function renderGuidedForm(payload) {
    guidedFields = guidedFieldsForType(currentType());
    if (!guidedFields.length) {
      guidedRoot.innerHTML = ui.renderEmpty('Guided fields are not defined for this profile type. Use Advanced editor.');
      return;
    }

    guidedRoot.innerHTML = guidedFields
      .map((field) => {
        const value = getPathValue(payload, field.id, field.type === 'checkbox' ? false : '');
        if (field.type === 'checkbox') {
          return `
            <label class="checkbox-line">
              <input type="checkbox" data-guided-field="${ui.escapeHtml(field.id)}" ${value ? 'checked' : ''} />
              ${ui.escapeHtml(field.label)}
            </label>
          `;
        }
        const renderedValue = field.type === 'csv' ? (Array.isArray(value) ? value.join(', ') : value) : value;
        return `
          <label>
            ${ui.escapeHtml(field.label)}
            <input data-guided-field="${ui.escapeHtml(field.id)}" value="${ui.escapeHtml(String(renderedValue ?? ''))}" />
          </label>
        `;
      })
      .join('');
  }

  async function openProfile(type, profileId) {
    const detail = await api.profileDetail(type, profileId);
    state.profiles.currentType = type;
    state.profiles.currentId = detail.profile_id;
    state.profiles.currentPayload = detail.payload || {};

    rawEditor.value = JSON.stringify(state.profiles.currentPayload, null, 2);
    renderGuidedForm(state.profiles.currentPayload);
    ui.setFeedback(
      'profileFeedback',
      `${detail.profile_id}: ${detail.valid ? 'valid' : 'invalid'} (${detail.validation_message})`
    );
  }

  function payloadFromEditor() {
    try {
      const parsed = JSON.parse(rawEditor.value || '{}');
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Profile JSON must be an object');
      }
      return parsed;
    } catch (error) {
      throw new Error(`Invalid JSON in advanced editor: ${error.message}`);
    }
  }

  function applyGuidedFields(payload) {
    for (const field of guidedFields) {
      const input = guidedRoot.querySelector(`[data-guided-field="${field.id}"]`);
      if (!input) {
        continue;
      }
      const value = parseGuidedValue(field, input);
      setPathValue(payload, field.id, value);
    }
    return payload;
  }

  async function refreshListAndOpenFirst() {
    const type = currentType();
    const payload = await api.profilesByType(type, true);
    listCache = payload.summaries || [];
    renderList();

    const preferred = state.profiles.currentId && listCache.some((item) => item.profile_id === state.profiles.currentId)
      ? state.profiles.currentId
      : listCache[0]?.profile_id;

    if (preferred) {
      await openProfile(type, preferred);
    } else {
      rawEditor.value = '{}';
      guidedRoot.innerHTML = ui.renderEmpty('Select or create a profile to begin editing.');
    }
  }

  typeSelect.addEventListener('change', async () => {
    state.profiles.currentType = currentType();
    state.profiles.currentId = '';
    await refreshListAndOpenFirst();
  });

  document.getElementById('profilesReloadBtn')?.addEventListener('click', async () => {
    try {
      await refreshListAndOpenFirst();
      ui.toast('Profiles reloaded', 'info');
    } catch (error) {
      ui.toast(`Failed to reload profiles: ${error.message}`, 'error');
    }
  });

  document.getElementById('profileValidateBtn')?.addEventListener('click', async () => {
    if (!state.profiles.currentId) {
      ui.toast('Select a profile first', 'error');
      return;
    }
    try {
      const result = await api.validateConfig({
        profile_type: currentType(),
        profile_id: state.profiles.currentId,
      });
      ui.setFeedback('profileFeedback', JSON.stringify(result, null, 2));
      ui.toast('Profile validation finished', 'success');
    } catch (error) {
      ui.setFeedback('profileFeedback', error.message, 'error');
      ui.toast(`Validation failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('profileSaveBtn')?.addEventListener('click', async () => {
    if (!state.profiles.currentId) {
      ui.toast('Select a profile first', 'error');
      return;
    }
    try {
      const payload = applyGuidedFields(payloadFromEditor());
      const saveResult = await api.profileSave(currentType(), state.profiles.currentId, {
        payload,
        replace: true,
      });
      rawEditor.value = JSON.stringify(payload, null, 2);
      ui.setFeedback('profileFeedback', JSON.stringify(saveResult, null, 2));
      ui.toast('Profile saved', saveResult.valid ? 'success' : 'error');
      await refreshListAndOpenFirst();
    } catch (error) {
      ui.setFeedback('profileFeedback', error.message, 'error');
      ui.toast(`Save failed: ${error.message}`, 'error');
    }
  });

  return {
    refresh: refreshListAndOpenFirst,
    poll: null,
  };
}
