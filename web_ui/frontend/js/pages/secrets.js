function splitCsv(raw) {
  return String(raw || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export function initSecretsPage(ctx) {
  const { api, ui } = ctx;

  const tableRoot = document.getElementById('secretsRefsTable');
  const providerProfileSelect = document.getElementById('secretLinkProviderProfile');

  async function refreshProviderProfiles() {
    const profiles = await api.profilesByType('providers');
    ui.updateSelectOptions(providerProfileSelect, profiles.profiles || []);
  }

  function renderRefs(refs) {
    if (!refs.length) {
      tableRoot.innerHTML = ui.renderEmpty('No secret refs found in secrets/refs.');
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
          key: 'issues',
          label: 'Issues',
          value: (row) => ui.escapeHtml((row.validation?.issues || []).join('; ') || 'none'),
        },
        {
          key: 'linked',
          label: 'Linked Profiles',
          value: (row) => ui.escapeHtml((row.linked_provider_profiles || []).join(', ') || 'none'),
        },
      ],
      refs
    );
  }

  async function refreshRefs() {
    const payload = await api.secretsRefs();
    renderRefs(payload.refs || []);
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

  return {
    refresh: async () => {
      await Promise.all([refreshProviderProfiles(), refreshRefs()]);
    },
    poll: null,
  };
}
