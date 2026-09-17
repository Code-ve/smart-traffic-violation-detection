/**
 * Upload page — drag & drop, file upload, configuration, results display.
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const resultsPanel = document.getElementById('results-panel');
    const confSlider = document.getElementById('confidence-threshold');
    const confValue = document.getElementById('conf-value');

    // ── Confidence slider ───────────────────────────────────────────
    confSlider?.addEventListener('input', () => {
        confValue.textContent = parseFloat(confSlider.value).toFixed(2);
    });

    // ── Apply config ────────────────────────────────────────────────
    document.getElementById('btn-apply-config')?.addEventListener('click', async () => {
        try {
            const config = {
                signal_state: document.getElementById('signal-state').value,
                red_light_line_y: parseInt(document.getElementById('stop-line-y').value),
                confidence_threshold: parseFloat(confSlider.value),
            };
            await API.post('/api/config', config);
            showToast('Configuration applied', 'success');
        } catch (err) {
            showToast('Failed to apply config: ' + err.message, 'error');
        }
    });

    // ── Drag and drop ───────────────────────────────────────────────
    dropzone?.addEventListener('click', () => fileInput?.click());

    dropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    });

    fileInput?.addEventListener('change', () => {
        if (fileInput.files[0]) uploadFile(fileInput.files[0]);
    });

    // ── Upload handler ──────────────────────────────────────────────
    async function uploadFile(file) {
        uploadProgress.style.display = 'block';
        resultsPanel.style.display = 'none';
        progressFill.style.width = '10%';
        progressText.textContent = `Uploading ${file.name}...`;

        try {
            progressFill.style.width = '30%';
            progressText.textContent = 'Processing...';
            const data = await API.upload('/api/upload', file);

            progressFill.style.width = '100%';

            if (data.status === 'completed' && data.type === 'image') {
                progressText.textContent = 'Detection complete!';
                displayImageResults(data);
            } else if (data.status === 'processing' && data.type === 'video') {
                progressText.textContent = 'Video processing started in background...';
                showToast('Video is being processed. Check the Analytics page for results.', 'info');
                // Redirect to latest session after a moment
                setTimeout(async () => {
                    try {
                        const sessions = await API.get('/api/sessions');
                        if (sessions.length > 0) {
                            window.location.href = `/processing/${sessions[0].id}`;
                        }
                    } catch (e) { /* ignore */ }
                }, 2000);
            }
        } catch (err) {
            progressFill.style.width = '0%';
            progressText.textContent = `Error: ${err.message}`;
            showToast(err.message, 'error');
        }
    }

    // ── Display image results ───────────────────────────────────────
    function displayImageResults(data) {
        resultsPanel.style.display = 'block';
        const result = data.result;
        const detections = data.detections || [];

        // Stats
        const statsEl = document.getElementById('results-stats');
        statsEl.innerHTML = `
            <div class="stat-item"><span class="stat-value">${detections.length}</span><span class="stat-label">Detections</span></div>
            <div class="stat-item"><span class="stat-value">${result.avg_inference_ms}</span><span class="stat-label">Inference (ms)</span></div>
            <div class="stat-item"><span class="stat-value">${result.avg_fps}</span><span class="stat-label">FPS</span></div>
        `;

        // Annotated image
        const imgEl = document.getElementById('results-image');
        if (result.output_path) {
            const filename = result.output_path.split(/[/\\]/).pop();
            imgEl.src = `/output/${filename}`;
            imgEl.style.display = 'block';
        }

        // Detections table
        const tbody = document.getElementById('detections-body');
        tbody.innerHTML = detections.map(d => `
            <tr>
                <td><span class="badge ${getViolationBadgeClass('')}">${d.class_name}</span></td>
                <td>${(d.confidence * 100).toFixed(1)}%</td>
                <td>${d.track_id ?? '—'}</td>
                <td>${Math.round(d.x1)}, ${Math.round(d.y1)} → ${Math.round(d.x2)}, ${Math.round(d.y2)}</td>
            </tr>
        `).join('') || '<tr><td colspan="4" class="empty-state">No objects detected</td></tr>';
    }
});
