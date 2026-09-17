/**
 * Evaluation page — load model info and run inference benchmarks.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ── Load model info ─────────────────────────────────────────────
    async function loadModelInfo() {
        try {
            const info = await API.get('/api/evaluation/info');
            const el = document.getElementById('model-info');

            if (info.status === 'not_found') {
                el.innerHTML = `<p class="eval-note">⚠️ Model not found at: ${info.path}. Download a YOLO model first.</p>`;
                return;
            }

            el.innerHTML = `
                <p><strong>Model:</strong> ${info.filename}</p>
                <p><strong>Size:</strong> ${info.size_mb} MB</p>
                <p><strong>Classes:</strong> ${info.num_classes}</p>
                <p><strong>Class Names:</strong> ${(info.class_names || []).join(', ')}</p>
            `;
        } catch (err) {
            document.getElementById('model-info').innerHTML =
                `<p class="eval-note">⚠️ Could not load model info: ${err.message}</p>`;
        }
    }

    // ── Load evaluation metrics ─────────────────────────────────────
    async function loadMetrics() {
        try {
            const metrics = await API.get('/api/evaluation/evaluate');
            const noteEl = document.getElementById('eval-note');

            if (metrics.status === 'pending') {
                noteEl.textContent = metrics.message;
                noteEl.style.display = 'block';
            } else if (metrics.status === 'completed') {
                document.getElementById('metric-precision').textContent = metrics.precision?.toFixed(4) ?? '—';
                document.getElementById('metric-recall').textContent = metrics.recall?.toFixed(4) ?? '—';
                document.getElementById('metric-map50').textContent = metrics.mAP50?.toFixed(4) ?? '—';
                document.getElementById('metric-map50-95').textContent = metrics.mAP50_95?.toFixed(4) ?? '—';
                noteEl.style.display = 'none';
            } else {
                noteEl.textContent = metrics.message || 'Evaluation could not be completed.';
                noteEl.style.display = 'block';
            }
        } catch (err) {
            document.getElementById('eval-note').textContent = 'Evaluation pending dataset/model execution.';
            document.getElementById('eval-note').style.display = 'block';
        }
    }

    // ── Run benchmark ───────────────────────────────────────────────
    document.getElementById('btn-run-benchmark')?.addEventListener('click', async () => {
        const btn = document.getElementById('btn-run-benchmark');
        btn.textContent = 'Running...';
        btn.disabled = true;

        try {
            const result = await API.get('/api/evaluation/benchmark');
            const el = document.getElementById('benchmark-results');
            el.style.display = 'block';

            if (result.status === 'completed') {
                document.getElementById('bench-avg-ms').textContent = result.avg_inference_ms;
                document.getElementById('bench-fps').textContent = result.fps;
                document.getElementById('bench-resolution').textContent = result.resolution;
                document.getElementById('bench-num-images').textContent = result.num_images;
                showToast('Benchmark complete!', 'success');
            } else {
                showToast('Benchmark failed: ' + (result.message || 'Unknown error'), 'error');
            }
        } catch (err) {
            showToast('Benchmark failed: ' + err.message, 'error');
        } finally {
            btn.textContent = 'Run Benchmark';
            btn.disabled = false;
        }
    });

    // ── Init ────────────────────────────────────────────────────────
    loadModelInfo();
    loadMetrics();
});
