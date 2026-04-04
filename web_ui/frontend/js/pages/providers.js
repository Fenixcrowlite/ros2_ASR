import { renderProviderGuideHtml } from '../provider-guides.js';

export function initProvidersPage(ctx) {
  const { api, ui } = ctx;

  const catalogRoot = document.getElementById('providersCatalogTable');
  const profilesRoot = document.getElementById('providerProfilesTable');
  const profileSelect = document.getElementById('providerTestProfile');
  const hfImportProviderProfile = document.getElementById('hfImportProviderProfile');
  const hfImportModelRef = document.getElementById('hfImportModelRef');
  const hfImportPresetId = document.getElementById('hfImportPresetId');
  const hfImportLabel = document.getElementById('hfImportLabel');
  const hfImportDescription = document.getElementById('hfImportDescription');
  const hfImportSetDefault = document.getElementById('hfImportSetDefault');
  const hfImportUpdateBaseSettings = document.getElementById('hfImportUpdateBaseSettings');
  const hfImportSettings = document.getElementById('hfImportSettings');

  let profileRows = [];

  function currentRow() {
    return profileRows.find((row) => row.provider_profile === profileSelect.value) || null;
  }

  function providerPayload() {
    const row = currentRow();
    const presetSelect = document.getElementById('providerTestPreset');
    const settingsEditor = document.getElementById('providerTestSettings');
    let providerSettings = {};
    const raw = String(settingsEditor?.value || '').trim();
    if (raw) {
      providerSettings = JSON.parse(raw);
      if (!providerSettings || typeof providerSettings !== 'object' || Array.isArray(providerSettings)) {
        throw new Error('Provider advanced settings must be a JSON object');
      }
    }
    return {
      provider_profile: profileSelect.value,
      provider_preset: presetSelect?.value || row?.default_preset || '',
      provider_settings: providerSettings,
    };
  }

  function parseObjectJson(raw, label) {
    const text = String(raw || '').trim();
    if (!text) {
      return {};
    }
    const parsed = JSON.parse(text);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error(`${label} must be a JSON object`);
    }
    return parsed;
  }

  function renderCatalog(rows) {
    if (!rows.length) {
      catalogRoot.innerHTML = ui.renderEmpty('No providers discovered. Check runtime backend service availability.');
      return;
    }

    catalogRoot.innerHTML = ui.table(
      [
        { key: 'name', label: 'Provider', value: (row) => ui.escapeHtml(row.name) },
        { key: 'kind', label: 'Kind', value: (row) => `<span class="${ui.statusBadgeClass(row.kind)}">${ui.escapeHtml(row.kind)}</span>` },
        {
          key: 'caps',
          label: 'Capabilities',
          value: (row) => {
            const caps = row.capabilities || {};
            const items = [
              `stream=${caps.supports_streaming}`,
              `stream_mode=${caps.streaming_mode || 'none'}`,
              `partials=${caps.supports_partials}`,
              `timestamps=${caps.supports_word_timestamps}`,
              `confidence=${caps.supports_confidence}`,
              `network=${caps.requires_network}`,
            ];
            return items.map((item) => `<code>${ui.escapeHtml(item)}</code>`).join('<br />');
          },
        },
        {
          key: 'status',
          label: 'Status',
          value: (row) => `<span class="${ui.statusBadgeClass(row.status)}">${ui.escapeHtml(row.status)}</span>`,
        },
        { key: 'profiles_count', label: 'Profiles', value: (row) => String(row.profiles_count ?? 0) },
      ],
      rows
    );
  }

  function renderProfiles(rows) {
    profileRows = rows;
    if (!rows.length) {
      profilesRoot.innerHTML = ui.renderEmpty('No provider profiles found in configs/providers.');
      ui.updateSelectOptions(profileSelect, []);
      return;
    }

    ui.updateSelectOptions(profileSelect, rows.map((row) => row.provider_profile), rows[0].provider_profile);
    renderPresetSelect();

    profilesRoot.innerHTML = ui.table(
      [
        { key: 'provider_profile', label: 'Profile', value: (row) => ui.toCode(row.provider_profile) },
        { key: 'provider_id', label: 'Provider', value: (row) => ui.escapeHtml(row.provider_id) },
        {
          key: 'valid',
          label: 'Validation',
          value: (row) =>
            `<span class="${ui.statusBadgeClass(row.valid ? 'valid' : 'invalid')}">${row.valid ? 'valid' : 'invalid'}</span>`,
        },
        {
          key: 'default_preset',
          label: 'Default model',
          value: (row) => ui.escapeHtml(row.default_preset || 'default'),
        },
        {
          key: 'credentials_ref',
          label: 'Credential Ref',
          value: (row) => ui.escapeHtml(row.credentials_ref || 'none'),
        },
        {
          key: 'message',
          label: 'Message',
          value: (row) => ui.escapeHtml(row.message || ''),
        },
      ],
      rows,
      [
        { id: 'validate', label: 'Validate', rowKey: (row) => row.provider_profile },
        { id: 'test', label: 'Test', rowKey: (row) => row.provider_profile },
      ]
    );

    profilesRoot.querySelectorAll('button[data-action]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const action = event.currentTarget.getAttribute('data-action');
        const profile = event.currentTarget.getAttribute('data-row');
        if (!profile) {
          return;
        }
        profileSelect.value = profile;
        renderPresetSelect();
        try {
          if (action === 'validate') {
            const payload = await api.providersValidate(providerPayload());
            ui.setFeedback('providerTestResult', JSON.stringify(payload, null, 2));
            ui.toast(`Validation completed for ${profile}`, payload.valid ? 'success' : 'error');
          }
          if (action === 'test') {
            const payload = await api.providersTest({
              ...providerPayload(),
              wav_path: document.getElementById('providerTestWav').value,
              language: 'en-US',
            });
            ui.setFeedback('providerTestResult', JSON.stringify(payload, null, 2));
            ui.toast(`Provider test completed for ${profile}`, payload.success ? 'success' : 'error');
          }
          await refresh();
        } catch (error) {
          ui.setFeedback('providerTestResult', error.message, 'error');
          ui.toast(`Provider action failed: ${error.message}`, 'error');
        }
      });
    });
  }

  function renderPresetSelect() {
    const row = currentRow();
    const presetSelect = document.getElementById('providerTestPreset');
    const presetMeta = document.getElementById('providerPresetMeta');
    const presets = row?.model_presets || [];
    if (!presetSelect || !presetMeta) {
      return;
    }
    if (!presets.length) {
      ui.updateSelectOptions(presetSelect, ['default'], 'default');
      presetSelect.disabled = true;
      presetMeta.innerHTML = ui.renderEmpty('This provider profile does not expose named model presets.');
      return;
    }
    presetSelect.disabled = false;
    ui.updateSelectOptions(presetSelect, presets.map((item) => item.preset_id), row.default_preset || presets[0].preset_id);
    const current = presets.find((item) => item.preset_id === presetSelect.value) || presets[0];
    presetMeta.innerHTML = `
      <div class="stack-item">
        <strong>${ui.escapeHtml(current.label)}</strong>
        <p>${ui.escapeHtml(current.description || '')}</p>
        <p class="muted">quality=${ui.escapeHtml(current.quality_tier || 'n/a')} resource=${ui.escapeHtml(current.resource_tier || 'n/a')}</p>
      </div>
      ${renderProviderGuideHtml(ui, row)}
    `;
  }

  document.getElementById('providerTestProfile')?.addEventListener('change', renderPresetSelect);
  document.getElementById('providerTestPreset')?.addEventListener('change', renderPresetSelect);

  document.getElementById('providerValidateBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersValidate(providerPayload());
      ui.setFeedback('providerTestResult', JSON.stringify(payload, null, 2));
      ui.toast('Provider validation done', payload.valid ? 'success' : 'error');
      await refresh();
    } catch (error) {
      ui.setFeedback('providerTestResult', error.message, 'error');
      ui.toast(`Validation failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('providerTestBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersTest({
        ...providerPayload(),
        wav_path: document.getElementById('providerTestWav').value,
        language: 'en-US',
      });
      ui.setFeedback('providerTestResult', JSON.stringify(payload, null, 2));
      ui.toast('Provider test done', payload.success ? 'success' : 'error');
      await refresh();
    } catch (error) {
      ui.setFeedback('providerTestResult', error.message, 'error');
      ui.toast(`Test failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('hfImportBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersImportHuggingFaceModel({
        provider_profile: hfImportProviderProfile?.value || 'providers/huggingface_local',
        model_ref: hfImportModelRef?.value || '',
        preset_id: hfImportPresetId?.value || '',
        label: hfImportLabel?.value || '',
        description: hfImportDescription?.value || '',
        set_default: Boolean(hfImportSetDefault?.checked),
        update_base_settings: Boolean(hfImportUpdateBaseSettings?.checked),
        settings: parseObjectJson(hfImportSettings?.value || '', 'Additional settings'),
      });
      ui.setFeedback('hfImportFeedback', JSON.stringify(payload, null, 2));
      ui.toast(`Imported Hugging Face model ${payload.model_id}`, payload.valid ? 'success' : 'error');
      await refresh();
      const importedProfile =
        String(payload.provider_profile_id || payload.provider_profile || '').replace(/^providers\//, '');
      profileSelect.value = importedProfile;
      renderPresetSelect();
      const presetSelect = document.getElementById('providerTestPreset');
      if (presetSelect && payload.preset_id) {
        presetSelect.value = payload.preset_id;
        renderPresetSelect();
      }
      if (hfImportModelRef) {
        hfImportModelRef.value = '';
      }
      if (hfImportPresetId) {
        hfImportPresetId.value = '';
      }
      if (hfImportLabel) {
        hfImportLabel.value = '';
      }
      if (hfImportDescription) {
        hfImportDescription.value = '';
      }
      if (hfImportSettings) {
        hfImportSettings.value = '';
      }
    } catch (error) {
      ui.setFeedback('hfImportFeedback', error.message, 'error');
      ui.toast(`HF import failed: ${error.message}`, 'error');
    }
  });

  async function refresh() {
    const [catalog, profiles] = await Promise.all([api.providersCatalog(), api.providersProfiles()]);
    renderCatalog(catalog.providers || []);
    renderProfiles(profiles.profiles || []);
  }

  return {
    refresh,
    poll: null,
  };
}
