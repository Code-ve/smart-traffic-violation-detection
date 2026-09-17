/**
 * Analytics dashboard — loads real data and renders Chart.js charts.
 */

document.addEventListener('DOMContentLoaded', () => {
    let vehiclesChart, violationsChart, timelineChart, confidenceChart;

    // ── Load sessions into selector ─────────────────────────────────
    async function loadSessions() {
        try {
            const sessions = await API.get('/api/sessions');
            const select = document.getElementById('analytics-session');
            sessions.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = `${s.filename} (${s.id})`;
                select.appendChild(opt);
            });

            // Sessions table
            const tbody = document.getElementById('sessions-body');
            if (sessions.length) {
                tbody.innerHTML = sessions.map(s => `
                    <tr>
                        <td><code>${s.id}</code></td>
                        <td>${s.filename}</td>
                        <td><span class="badge ${s.status === 'completed' ? 'badge-resolved' : 'badge-detected'}">${s.status}</span></td>
                        <td>${s.unique_vehicles || 0}</td>
                        <td>${s.total_violations || 0}</td>
                        <td>${s.started_at ? new Date(s.started_at).toLocaleDateString() : '—'}</td>
                    </tr>
                `).join('');
            }
        } catch (err) {
            console.error('Failed to load sessions:', err);
        }
    }

    // ── Load analytics ──────────────────────────────────────────────
    async function loadAnalytics(sessionId = '') {
        try {
            const params = sessionId ? `?session_id=${sessionId}` : '';

            const [traffic, violations, confidence] = await Promise.all([
                API.get(`/api/analytics/traffic${params}`),
                API.get(`/api/analytics/violations${params}`),
                API.get(`/api/analytics/confidence${params}`),
            ]);

            // Summary cards
            document.getElementById('analytics-total-vehicles').textContent = traffic.total_vehicles || 0;
            document.getElementById('analytics-unique-vehicles').textContent = traffic.unique_vehicles || 0;
            document.getElementById('analytics-total-violations').textContent = violations.total_violations || 0;
            document.getElementById('analytics-violation-pct').textContent = (violations.violation_percentage || 0) + '%';

            // Vehicle chart
            renderDoughnut('chart-vehicles', vehiclesChart, traffic.by_type || {}, 'Vehicles by Type', c => vehiclesChart = c);

            // Violation chart
            const violationLabels = {};
            for (const [k, v] of Object.entries(violations.by_type || {})) {
                violationLabels[formatViolationType(k)] = v;
            }
            renderDoughnut('chart-violations', violationsChart, violationLabels, 'Violations by Type', c => violationsChart = c);

            // Confidence histogram
            renderBar('chart-confidence', confidenceChart, confidence || [], c => confidenceChart = c);

            // Timeline (needs session)
            if (sessionId) {
                const timeline = await API.get(`/api/analytics/timeline/${sessionId}`);
                renderTimeline(timeline);
            }

        } catch (err) {
            console.error('Analytics error:', err);
            showToast('Failed to load analytics: ' + err.message, 'error');
        }
    }

    // ── Chart renderers ─────────────────────────────────────────────
    function renderDoughnut(canvasId, existing, data, title, setter) {
        if (existing) existing.destroy();
        const labels = Object.keys(data);
        const values = Object.values(data);
        if (!labels.length) return;

        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: CHART_COLOURS.slice(0, labels.length),
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 }, padding: 15 },
                    },
                },
                cutout: '60%',
            },
        });
        setter(chart);
    }

    function renderBar(canvasId, existing, data, setter) {
        if (existing) existing.destroy();
        if (!data.length) return;
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.range),
                datasets: [{
                    label: 'Count',
                    data: data.map(d => d.count),
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    borderRadius: 4,
                }],
            },
            options: {
                ...CHART_DEFAULTS,
                plugins: {
                    ...CHART_DEFAULTS.plugins,
                    legend: { display: false },
                },
            },
        });
        setter(chart);
    }

    function renderTimeline(data) {
        if (timelineChart) timelineChart.destroy();
        const timeline = data.detection_timeline || [];
        if (!timeline.length) return;

        const ctx = document.getElementById('chart-timeline')?.getContext('2d');
        if (!ctx) return;
        timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeline.map(d => `Frame ${d.frame}`),
                datasets: [{
                    label: 'Detections',
                    data: timeline.map(d => d.count),
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                }],
            },
            options: CHART_DEFAULTS,
        });
    }

    // ── Event handlers ──────────────────────────────────────────────
    document.getElementById('btn-load-analytics')?.addEventListener('click', () => {
        const sessionId = document.getElementById('analytics-session').value;
        loadAnalytics(sessionId);
    });

    // ── Init ────────────────────────────────────────────────────────
    loadSessions();
    loadAnalytics();
});
