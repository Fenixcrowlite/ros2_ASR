// Datasets page controller for the browser UI.
export function initDatasetsPage(ctx) {
  const { api, ui } = ctx;

  const tableRoot = document.getElementById('datasetsRegistryTable');
  const detailsRoot = document.getElementById('datasetDetails');

  let cache = [];

  function renderTable(rows) {
    if (!rows.length) {
      tableRoot.innerHTML = ui.renderEmpty('Dataset registry is empty. Import or register a dataset to continue.');
      detailsRoot.innerHTML = ui.renderEmpty('Select a dataset to inspect metadata and sample preview.');
      return;
    }

    tableRoot.innerHTML = ui.table(
      [
        { key: 'dataset_id', label: 'Dataset ID', value: (row) => ui.toCode(row.dataset_id) },
        {
          key: 'valid',
          label: 'Status',
          value: (row) =>
            `<span class="${ui.statusBadgeClass(row.valid ? 'valid' : 'invalid')}">${row.valid ? 'valid' : 'invalid'}</span>`,
        },
        { key: 'sample_count', label: 'Samples', value: (row) => String(row.sample_count ?? 0) },
        { key: 'languages', label: 'Languages', value: (row) => ui.escapeHtml((row.languages || []).join(', ')) },
        { key: 'duration_sec', label: 'Duration(s)', value: (row) => String(Math.round(row.duration_sec || 0)) },
        { key: 'manifest_ref', label: 'Manifest', value: (row) => ui.escapeHtml(row.manifest_ref || '') },
      ],
      rows,
      [{ id: 'open', label: 'Open', rowKey: (row) => row.dataset_id }]
    );

    tableRoot.querySelectorAll('button[data-action="open"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const datasetId = event.currentTarget.getAttribute('data-row');
        if (!datasetId) {
          return;
        }
        await loadDatasetDetail(datasetId);
      });
    });
  }

  async function loadDatasetDetail(datasetId) {
    try {
      const detail = await api.datasetDetail(datasetId);
      detailsRoot.innerHTML = `
        <div class="stack-item">
          <strong>${ui.escapeHtml(detail.dataset_id)}</strong>
          <p>manifest: ${ui.escapeHtml(detail.manifest_ref)}</p>
          <p>samples: ${ui.escapeHtml(String(detail.sample_count))}</p>
          <p>languages: ${ui.escapeHtml((detail.languages || []).join(', ') || 'n/a')}</p>
          <p>splits: ${ui.escapeHtml(JSON.stringify(detail.splits || {}))}</p>
          <p>duration_sec: ${ui.escapeHtml(String(Math.round(detail.duration_sec || 0)))}</p>
        </div>
        ${(detail.preview || [])
          .slice(0, 12)
          .map(
            (sample) => `
              <div class="stack-item">
                <strong>${ui.escapeHtml(sample.sample_id)}</strong>
                <p>${ui.escapeHtml(sample.transcript)}</p>
                <p class="muted">${ui.escapeHtml(sample.audio_path)}</p>
              </div>
            `
          )
          .join('')}
      `;
    } catch (error) {
      detailsRoot.innerHTML = ui.renderEmpty(`Failed to load dataset detail: ${error.message}`);
    }
  }

  async function refresh() {
    const payload = await api.datasetsList();
    cache = payload.datasets || [];
    renderTable(cache);
    if (cache.length) {
      await loadDatasetDetail(cache[0].dataset_id);
    }
  }

  document.getElementById('datasetImportBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.datasetImport({
        source_path: document.getElementById('datasetImportSource').value,
        dataset_id: document.getElementById('datasetImportId').value,
        dataset_profile: document.getElementById('datasetImportProfile').value,
      });
      ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Dataset import finished', payload.success === false ? 'error' : 'success');
      await refresh();
    } catch (error) {
      ui.setFeedback('datasetsFeedback', error.message, 'error');
      ui.toast(`Dataset import failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('datasetUploadBtn')?.addEventListener('click', async () => {
    try {
      const files = Array.from(document.getElementById('datasetUploadFiles').files || []);
      if (!files.length) {
        throw new Error('Select files or a folder first');
      }
      const payload = await api.datasetImportUpload({
        dataset_id: document.getElementById('datasetUploadId').value,
        dataset_profile: document.getElementById('datasetUploadProfile').value,
        language: document.getElementById('datasetUploadLanguage').value,
        files,
      });
      ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Uploaded dataset imported', 'success');
      document.getElementById('datasetRegisterProfile').value = payload.dataset_profile || '';
      document.getElementById('datasetValidateManifest').value = payload.manifest_path || '';
      await refresh();
    } catch (error) {
      ui.setFeedback('datasetsFeedback', error.message, 'error');
      ui.toast(`Dataset upload failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('datasetRegisterBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.datasetRegister({
        manifest_path: document.getElementById('datasetRegisterManifest').value,
        dataset_id: document.getElementById('datasetRegisterId').value,
        dataset_profile: document.getElementById('datasetRegisterProfile').value,
      });
      ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Dataset registered', 'success');
      await refresh();
    } catch (error) {
      ui.setFeedback('datasetsFeedback', error.message, 'error');
      ui.toast(`Dataset register failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('datasetValidateBtn')?.addEventListener('click', async () => {
    try {
      const payload = await api.datasetValidateManifest({
        manifest_path: document.getElementById('datasetValidateManifest').value,
        check_audio_files: document.getElementById('datasetValidateAudio').checked,
      });
      ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
      ui.toast(`Manifest validation: ${payload.valid ? 'valid' : 'issues found'}`, payload.valid ? 'success' : 'error');
    } catch (error) {
      ui.setFeedback('datasetsFeedback', error.message, 'error');
      ui.toast(`Manifest validation failed: ${error.message}`, 'error');
    }
  });

  return {
    refresh,
    poll: null,
  };
}
