/**
 * Violations page — load, filter, and manage violation records.
 */

document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('violations-body');
    const modal = document.getElementById('evidence-modal');

    // ── Load violations ─────────────────────────────────────────────
    async function loadViolations() {
        const type = document.getElementById('filter-type').value;
        const vehicle = document.getElementById('filter-vehicle').value;
        const status = document.getElementById('filter-status').value;

        const params = new URLSearchParams();
        if (type) params.set('violation_type', type);
        if (vehicle) params.set('vehicle_type', vehicle);
        if (status) params.set('status', status);

        try {
            const violations = await API.get(`/api/violations?${params}`);
            renderViolations(violations);
        } catch (err) {
            showToast('Failed to load violations: ' + err.message, 'error');
        }
    }

    function renderViolations(violations) {
        if (!violations.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="empty-state">No violations found.</td></tr>';
            return;
        }

        tbody.innerHTML = violations.map(v => `
            <tr>
                <td>${v.id}</td>
                <td>${v.timestamp ? new Date(v.timestamp).toLocaleString() : '—'}</td>
                <td><span class="badge ${getViolationBadgeClass(v.violation_type)}">${formatViolationType(v.violation_type)}</span></td>
                <td>${v.vehicle_type || '—'}</td>
                <td>${v.track_id ?? '—'}</td>
                <td>${v.confidence ? (v.confidence * 100).toFixed(1) + '%' : '—'}</td>
                <td>${v.frame_number ?? '—'}</td>
                <td><span class="badge ${getStatusBadgeClass(v.status)}">${v.status}</span></td>
                <td>
                    ${v.evidence_path ? `<button class="btn btn-sm btn-secondary" onclick="showEvidence('${v.evidence_path.split(/[/\\\\]/).pop()}', ${v.id})">View</button>` : '—'}
                </td>
                <td>
                    <select class="status-select" data-id="${v.id}" onchange="updateStatus(${v.id}, this.value)">
                        <option value="Detected" ${v.status === 'Detected' ? 'selected' : ''}>Detected</option>
                        <option value="Reviewed" ${v.status === 'Reviewed' ? 'selected' : ''}>Reviewed</option>
                        <option value="Resolved" ${v.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                    </select>
                </td>
            </tr>
        `).join('');
    }

    // ── Evidence modal ──────────────────────────────────────────────
    window.showEvidence = function(filename, violationId) {
        document.getElementById('modal-image').src = `/evidence/${filename}`;
        document.getElementById('modal-title').textContent = `Evidence — Violation #${violationId}`;
        modal.style.display = 'flex';
    };

    document.getElementById('btn-close-modal')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // ── Update status ───────────────────────────────────────────────
    window.updateStatus = async function(id, newStatus) {
        try {
            await API.patch(`/api/violations/${id}/status`, { status: newStatus });
            showToast(`Violation #${id} → ${newStatus}`, 'success');
        } catch (err) {
            showToast('Failed to update: ' + err.message, 'error');
        }
    };

    // ── Filters ─────────────────────────────────────────────────────
    document.getElementById('btn-apply-filters')?.addEventListener('click', loadViolations);

    // Initial load
    loadViolations();
});
