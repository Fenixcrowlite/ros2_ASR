export function initProvidersPage(ctx) {
  const { api, ui } = ctx;

  const catalogRoot = document.getElementById('providersCatalogTable');
  const profilesRoot = document.getElementById('providerProfilesTable');
  const profileSelect = document.getElementById('providerTestProfile');

  let profileRows = [];

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
        try {
          if (action === 'validate') {
            const payload = await api.providersValidate({ provider_profile: profile });
            ui.setFeedback('providerTestResult', JSON.stringify(payload, null, 2));
            ui.toast(`Validation completed for ${profile}`, payload.valid ? 'success' : 'error');
          }
          if (action === 'test') {
            const payload = await api.providersTest({
              provider_profile: profile,
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

  document.getElementById('providerValidateBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.providersValidate({ provider_profile: profileSelect.value });
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
        provider_profile: profileSelect.value,
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
