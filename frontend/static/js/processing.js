/**
 * Processing page — polls for video processing progress and shows completion.
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof SESSION_ID === 'undefined' || !SESSION_ID) return;

    const progressFill = document.getElementById('video-progress-fill');
    const progressText = document.getElementById('video-progress-text');
    const statusCard = document.getElementById('processing-status-card');
    const summaryCard = document.getElementById('session-summary-card');

    let pollInterval = null;

    async function pollProgress() {
        try {
            const data = await API.get(`/api/sessions/${SESSION_ID}/progress`);

            if (data.status === 'completed') {
                // Show completion
                progressFill.style.width = '100%';
                progressText.textContent = 'Processing complete!';
                clearInterval(pollInterval);
                showCompletion();
                return;
            }

            // Update progress
            const pct = data.percent || 0;
            progressFill.style.width = `${pct}%`;
            progressText.textContent = `${pct}% — Frame ${data.frame || 0}/${data.total_frames || '?'}`;

            document.getElementById('stat-frame').textContent = data.frame || 0;
            document.getElementById('stat-fps').textContent = data.fps || 0;
            document.getElementById('stat-detections').textContent = data.detections || 0;
            document.getElementById('stat-vehicles').textContent = data.unique_vehicles || 0;
            document.getElementById('stat-violations').textContent = data.violations || 0;

        } catch (err) {
            console.error('Poll error:', err);
        }
    }

    async function showCompletion() {
        try {
            const session = await API.get(`/api/sessions/${SESSION_ID}`);
            summaryCard.style.display = 'block';

            document.getElementById('session-summary').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value">${session.total_frames || 0}</span>
                        <span class="stat-label">Total Frames</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${session.processed_frames || 0}</span>
                        <span class="stat-label">Processed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${session.unique_vehicles || 0}</span>
                        <span class="stat-label">Vehicles</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${session.total_violations || 0}</span>
                        <span class="stat-label">Violations</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${session.avg_fps || 0}</span>
                        <span class="stat-label">Avg FPS</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${session.avg_inference_ms || 0}</span>
                        <span class="stat-label">Inference (ms)</span>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error('Failed to load session summary:', err);
        }
    }

    // Start polling
    pollProgress();
    pollInterval = setInterval(pollProgress, 1500);
});
