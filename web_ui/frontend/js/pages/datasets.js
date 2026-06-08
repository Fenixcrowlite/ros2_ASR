// Datasets page controller for the browser UI.
export function initDatasetsPage(ctx) {
  const { api, ui } = ctx;

  const tableRoot = document.getElementById('datasetsRegistryTable');
  const detailsRoot = document.getElementById('datasetDetails');

  let cache = [];
  let manualRecorder = null;
  let manualAudioBlob = null;
  let manualAudioUrl = '';
  let manualProfileTouched = false;
  let selectedDatasetId = '';
  let editingSampleId = '';

  function setManualStatus(message) {
    const status = document.getElementById('datasetManualStatus');
    if (status) {
      status.textContent = message;
    }
  }

  function setManualButtons({ recording = false, hasAudio = Boolean(manualAudioBlob) } = {}) {
    const recordBtn = document.getElementById('datasetManualRecordBtn');
    const stopBtn = document.getElementById('datasetManualStopBtn');
    const saveBtn = document.getElementById('datasetManualSaveBtn');
    if (recordBtn) {
      recordBtn.disabled = recording;
    }
    if (stopBtn) {
      stopBtn.disabled = !recording;
    }
    if (saveBtn) {
      saveBtn.disabled = recording || !hasAudio;
    }
  }

  function defaultSampleId() {
    const stamp = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
    return `sample_${stamp}`;
  }

  function encodeWav(samples, sampleRate) {
    const bytesPerSample = 2;
    const blockAlign = bytesPerSample;
    const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
    const view = new DataView(buffer);

    function writeString(offset, value) {
      for (let index = 0; index < value.length; index += 1) {
        view.setUint8(offset + index, value.charCodeAt(index));
      }
    }

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * bytesPerSample, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, samples.length * bytesPerSample, true);

    let offset = 44;
    for (let index = 0; index < samples.length; index += 1, offset += 2) {
      const sample = Math.max(-1, Math.min(1, samples[index]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    }
    return new Blob([view], { type: 'audio/wav' });
  }

  function mergeAudioChunks(chunks) {
    const totalLength = chunks.reduce((total, chunk) => total + chunk.length, 0);
    const samples = new Float32Array(totalLength);
    let offset = 0;
    chunks.forEach((chunk) => {
      samples.set(chunk, offset);
      offset += chunk.length;
    });
    return samples;
  }

  function setManualPreview(blob) {
    const player = document.getElementById('datasetManualPreview');
    if (manualAudioUrl) {
      URL.revokeObjectURL(manualAudioUrl);
      manualAudioUrl = '';
    }
    manualAudioBlob = blob;
    if (player) {
      if (blob) {
        manualAudioUrl = URL.createObjectURL(blob);
        player.src = manualAudioUrl;
      } else {
        player.removeAttribute('src');
        player.load();
      }
    }
    setManualButtons({ hasAudio: Boolean(blob) });
  }

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
        { key: 'source', label: 'Source', value: (row) => ui.escapeHtml(row.metadata?.source || 'bundled') },
        { key: 'duration_sec', label: 'Duration(s)', value: (row) => String(Math.round(row.duration_sec || 0)) },
        { key: 'manifest_ref', label: 'Manifest', value: (row) => ui.escapeHtml(row.manifest_ref || '') },
      ],
      rows,
      [
        { id: 'open', label: 'Open', rowKey: (row) => row.dataset_id },
        { id: 'delete', label: 'Delete', rowKey: (row) => row.dataset_id },
      ]
    );

    tableRoot.querySelectorAll('button[data-action="open"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const datasetId = event.currentTarget.getAttribute('data-row');
        if (!datasetId) {
          return;
        }
        editingSampleId = '';
        await loadDatasetDetail(datasetId);
      });
    });
    tableRoot.querySelectorAll('button[data-action="delete"]').forEach((button) => {
      const datasetId = button.getAttribute('data-row') || '';
      const row = rows.find((item) => item.dataset_id === datasetId);
      const source = String(row?.metadata?.source || '').toLowerCase();
      if (!['manual', 'upload'].includes(source)) {
        button.disabled = true;
        button.title = 'Only manually created or uploaded datasets can be deleted from the GUI.';
      } else {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
      }
      button.addEventListener('click', async (event) => {
        const targetDatasetId = event.currentTarget.getAttribute('data-row');
        if (!targetDatasetId) {
          return;
        }
        const confirmed = window.confirm(
          `Delete dataset "${targetDatasetId}" and its local manifest/profile/audio files?`
        );
        if (!confirmed) {
          return;
        }
        try {
          const payload = await api.datasetDelete(targetDatasetId, { delete_artifacts: true });
          ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
          ui.toast(`Dataset deleted: ${targetDatasetId}`, 'success');
          await refresh();
        } catch (error) {
          ui.setFeedback('datasetsFeedback', error.message, 'error');
          ui.toast(`Dataset delete failed: ${error.message}`, 'error');
        }
      });
    });
  }

  function renderSampleCard(detail, sample) {
    const sampleId = String(sample.sample_id || '');
    const isEditing = detail.editable && editingSampleId === sampleId;
    if (isEditing) {
      return `
        <div class="stack-item dataset-sample-editor" data-sample-id="${ui.escapeHtml(sampleId)}">
          <label>
            Sample ID
            <input data-sample-edit-field="sample_id" value="${ui.escapeHtml(sampleId)}" />
          </label>
          <label>
            Reference text
            <textarea data-sample-edit-field="transcript" rows="4">${ui.escapeHtml(sample.transcript)}</textarea>
          </label>
          <p class="muted">${ui.escapeHtml(sample.audio_path)}</p>
          <div class="actions-row">
            <button class="btn-primary" data-action="save_sample" data-sample-id="${ui.escapeHtml(sampleId)}">Save</button>
            <button class="btn-secondary" data-action="cancel_sample_edit" data-sample-id="${ui.escapeHtml(sampleId)}">Cancel</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="stack-item dataset-sample-card" data-sample-id="${ui.escapeHtml(sampleId)}">
        <div class="dataset-sample-card__head">
          <strong>${ui.escapeHtml(sampleId)}</strong>
          ${
            detail.editable
              ? `<button class="btn-secondary" data-action="edit_sample" data-sample-id="${ui.escapeHtml(sampleId)}">Edit</button>`
              : ''
          }
        </div>
        <p class="dataset-sample-card__text">${ui.escapeHtml(sample.transcript)}</p>
        <p class="muted">${ui.escapeHtml(sample.audio_path)}</p>
      </div>
    `;
  }

  function renderDatasetDetail(detail) {
    const editableBadge = detail.editable
      ? '<span class="badge badge-ok">editable</span>'
      : `<span class="badge badge-muted" title="${ui.escapeHtml(detail.read_only_reason || '')}">read-only</span>`;
    detailsRoot.innerHTML = `
      <div class="stack-item">
        <div class="dataset-sample-card__head">
          <strong>${ui.escapeHtml(detail.dataset_id)}</strong>
          ${editableBadge}
        </div>
        <p>manifest: ${ui.escapeHtml(detail.manifest_ref)}</p>
        <p>source: ${ui.escapeHtml(detail.metadata?.source || 'bundled')}</p>
        <p>samples: ${ui.escapeHtml(String(detail.sample_count))}</p>
        <p>languages: ${ui.escapeHtml((detail.languages || []).join(', ') || 'n/a')}</p>
        <p>splits: ${ui.escapeHtml(JSON.stringify(detail.splits || {}))}</p>
        <p>duration_sec: ${ui.escapeHtml(String(Math.round(detail.duration_sec || 0)))}</p>
      </div>
      ${(detail.preview || []).slice(0, 25).map((sample) => renderSampleCard(detail, sample)).join('')}
    `;

    detailsRoot.querySelectorAll('button[data-action="edit_sample"]').forEach((button) => {
      button.addEventListener('click', (event) => {
        editingSampleId = event.currentTarget.getAttribute('data-sample-id') || '';
        renderDatasetDetail(detail);
      });
    });
    detailsRoot.querySelectorAll('button[data-action="cancel_sample_edit"]').forEach((button) => {
      button.addEventListener('click', () => {
        editingSampleId = '';
        renderDatasetDetail(detail);
      });
    });
    detailsRoot.querySelectorAll('button[data-action="save_sample"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const oldSampleId = event.currentTarget.getAttribute('data-sample-id') || '';
        const editor = event.currentTarget.closest('[data-sample-id]');
        const sampleIdInput = editor?.querySelector('[data-sample-edit-field="sample_id"]');
        const transcriptInput = editor?.querySelector('[data-sample-edit-field="transcript"]');
        const newSampleId = sampleIdInput?.value.trim() || '';
        const transcript = transcriptInput?.value.trim() || '';
        try {
          if (!newSampleId || !transcript) {
            throw new Error('Sample ID and reference text are required');
          }
          const payload = await api.datasetSampleUpdate(detail.dataset_id, oldSampleId, {
            sample_id: newSampleId,
            transcript,
          });
          ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
          ui.toast('Dataset sample updated', 'success');
          editingSampleId = '';
          await refresh(detail.dataset_id);
        } catch (error) {
          ui.setFeedback('datasetsFeedback', error.message, 'error');
          ui.toast(`Sample update failed: ${error.message}`, 'error');
        }
      });
    });
  }

  async function loadDatasetDetail(datasetId) {
    try {
      selectedDatasetId = datasetId;
      const detail = await api.datasetDetail(datasetId);
      renderDatasetDetail(detail);
    } catch (error) {
      detailsRoot.innerHTML = ui.renderEmpty(`Failed to load dataset detail: ${error.message}`);
    }
  }

  async function refresh(preferredDatasetId = selectedDatasetId) {
    const payload = await api.datasetsList();
    cache = payload.datasets || [];
    renderTable(cache);
    if (cache.length) {
      const selected =
        cache.find((row) => row.dataset_id === preferredDatasetId) ||
        cache.find((row) => row.dataset_id === selectedDatasetId) ||
        cache[0];
      await loadDatasetDetail(selected.dataset_id);
    }
  }

  document.getElementById('datasetManualProfile')?.addEventListener('input', () => {
    manualProfileTouched = true;
  });

  document.getElementById('datasetManualId')?.addEventListener('input', (event) => {
    const profileInput = document.getElementById('datasetManualProfile');
    if (profileInput && !manualProfileTouched) {
      profileInput.value = event.currentTarget.value.trim();
    }
  });

  document.getElementById('datasetManualRecordBtn')?.addEventListener('click', async () => {
    try {
      if (!document.getElementById('datasetManualSampleId').value.trim()) {
        document.getElementById('datasetManualSampleId').value = defaultSampleId();
      }
      setManualPreview(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      const chunks = [];

      processor.onaudioprocess = (event) => {
        chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      };
      source.connect(processor);
      processor.connect(audioContext.destination);
      manualRecorder = { stream, audioContext, source, processor, chunks, startedAt: performance.now() };
      setManualStatus('recording');
      setManualButtons({ recording: true, hasAudio: false });
    } catch (error) {
      setManualStatus('microphone unavailable');
      ui.toast(`Recording failed: ${error.message}`, 'error');
    }
  });

  document.getElementById('datasetManualStopBtn')?.addEventListener('click', async () => {
    if (!manualRecorder) {
      return;
    }
    const recorder = manualRecorder;
    manualRecorder = null;
    recorder.processor.disconnect();
    recorder.source.disconnect();
    recorder.stream.getTracks().forEach((track) => track.stop());
    await recorder.audioContext.close();

    const samples = mergeAudioChunks(recorder.chunks);
    if (!samples.length) {
      setManualStatus('empty recording');
      setManualButtons({ recording: false, hasAudio: false });
      return;
    }
    const blob = encodeWav(samples, Math.round(recorder.audioContext.sampleRate));
    setManualPreview(blob);
    const durationSec = (performance.now() - recorder.startedAt) / 1000;
    setManualStatus(`ready ${durationSec.toFixed(1)}s`);
  });

  document.getElementById('datasetManualSaveBtn')?.addEventListener('click', async () => {
    try {
      if (!manualAudioBlob) {
        throw new Error('Record a sample first');
      }
      const datasetId = document.getElementById('datasetManualId').value.trim();
      const sampleId = document.getElementById('datasetManualSampleId').value.trim();
      const transcript = document.getElementById('datasetManualTranscript').value.trim();
      if (!datasetId || !sampleId || !transcript) {
        throw new Error('Dataset ID, sample ID, and reference text are required');
      }
      const payload = await api.datasetManualSample({
        dataset_id: datasetId,
        dataset_profile: document.getElementById('datasetManualProfile').value.trim() || datasetId,
        sample_id: sampleId,
        transcript,
        language: document.getElementById('datasetManualLanguage').value.trim() || 'en-US',
        split: 'test',
        replace_existing: document.getElementById('datasetManualReplace').checked,
        audio_file: new File([manualAudioBlob], `${sampleId}.wav`, { type: 'audio/wav' }),
      });
      ui.setFeedback('datasetsFeedback', JSON.stringify(payload, null, 2));
      ui.toast('Manual sample saved', 'success');
      document.getElementById('datasetRegisterProfile').value = payload.dataset_profile || '';
      document.getElementById('datasetValidateManifest').value = payload.manifest_path || '';
      setManualStatus(`saved ${payload.sample_count} sample(s)`);
      await refresh();
      await loadDatasetDetail(payload.dataset_id);
    } catch (error) {
      ui.setFeedback('datasetsFeedback', error.message, 'error');
      ui.toast(`Manual sample save failed: ${error.message}`, 'error');
    }
  });

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
