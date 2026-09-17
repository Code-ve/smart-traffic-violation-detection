/**
 * Shared utility functions for the TrafficVision frontend.
 */

const API = {
    /** Generic fetch wrapper with error handling */
    async request(url, options = {}) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) {
                const err = await res.json().catch(() => ({ error: res.statusText }));
                throw new Error(err.error || err.detail || `HTTP ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error(`API error: ${url}`, err);
            throw err;
        }
    },

    get(url) { return this.request(url); },

    post(url, body) {
        return this.request(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    },

    patch(url, body) {
        return this.request(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    },

    async upload(url, file) {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(url, { method: 'POST', body: form });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: res.statusText }));
            throw new Error(err.error || err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    },
};

/** Show a toast notification */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; z-index: 9999;
        padding: 12px 24px; border-radius: 8px; font-size: 0.9rem;
        font-family: var(--font-family); color: white; max-width: 400px;
        animation: fadeInUp 0.3s ease-out;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

/** Format a violation type for display */
function formatViolationType(type) {
    const map = {
        'RED_LIGHT_VIOLATION': 'Red Light',
        'SPEED_ZONE_VIOLATION': 'Speed / Zone',
        'HELMET_VIOLATION': 'Helmet',
    };
    return map[type] || type;
}

/** Get badge class for violation type */
function getViolationBadgeClass(type) {
    const map = {
        'RED_LIGHT_VIOLATION': 'badge-red-light',
        'SPEED_ZONE_VIOLATION': 'badge-speed-zone',
        'HELMET_VIOLATION': 'badge-helmet',
    };
    return map[type] || '';
}

/** Get badge class for status */
function getStatusBadgeClass(status) {
    const map = {
        'Detected': 'badge-detected',
        'Reviewed': 'badge-reviewed',
        'Resolved': 'badge-resolved',
    };
    return map[status] || '';
}

/** Chart.js default dark theme options */
const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } },
        },
    },
    scales: {
        x: {
            ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
            grid: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
            ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
            grid: { color: 'rgba(255,255,255,0.05)' },
        },
    },
};

const CHART_COLOURS = [
    '#6366f1', '#06b6d4', '#10b981', '#f59e0b',
    '#ef4444', '#a78bfa', '#f472b6', '#34d399',
];
