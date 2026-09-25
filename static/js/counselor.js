/* ===============================================================
   Serene Minds - Student Wellness System
   Counselor Module Interactive Scripts
   (Early Risk Detection, Chart.js Visualizations, Queue Management)
   =============================================================== */

let campusDistributionChart = null;
let campusMoodTrendChart = null;
let currentEditingAppointmentId = null;

document.addEventListener('DOMContentLoaded', () => {
  initCounselorDashboard();
  initAppointmentQueueFilters();
  initModalListeners();
});

async function initCounselorDashboard() {
  await loadOverviewData();
  await loadRiskAlerts();
  await loadCounselorAppointments();
}

// --- Overview Metrics & Charts ---
async function loadOverviewData() {
  try {
    const data = await API.get('/api/counselor/overview');
    if (!data) return;

    // Stat KPI numbers
    document.getElementById('counselor-stat-students').textContent = data.total_students || 0;
    document.getElementById('counselor-stat-flagged').textContent = data.flagged_students_count || 0;
    document.getElementById('counselor-stat-pending-apps').textContent = data.pending_appointments || 0;
    document.getElementById('counselor-stat-total-logs').textContent = data.total_mood_logs || 0;

    // Render Charts
    renderDistributionChart(data.distribution);
    renderTrendChart(data.daily_trends);
  } catch (err) {
    console.error('Failed to load counselor overview:', err);
    showToast('Failed to refresh counselor metrics.', 'error');
  }
}

function renderDistributionChart(distribution) {
  const canvas = document.getElementById('campusDistributionChart');
  if (!canvas || typeof Chart === 'undefined') return;

  const dataValues = [
    distribution.thriving || 0,
    distribution.stable || 0,
    distribution.vulnerable || 0,
    distribution.high_risk || 0
  ];

  if (campusDistributionChart) {
    campusDistributionChart.data.datasets[0].data = dataValues;
    campusDistributionChart.update();
    return;
  }

  const ctx = canvas.getContext('2d');
  campusDistributionChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Thriving (4.0+)', 'Stable (3.0 - 3.9)', 'Vulnerable (2.3 - 2.9)', 'High Risk / Flagged (<2.3)'],
      datasets: [{
        data: dataValues,
        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.label}: ${context.raw} students`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

function renderTrendChart(trends) {
  const canvas = document.getElementById('campusMoodTrendChart');
  if (!canvas || typeof Chart === 'undefined') return;

  const labels = (trends || []).map(t => t.date);
  const dataPoints = (trends || []).map(t => t.avg_mood);

  if (campusMoodTrendChart) {
    campusMoodTrendChart.data.labels = labels;
    campusMoodTrendChart.data.datasets[0].data = dataPoints;
    campusMoodTrendChart.update();
    return;
  }

  const ctx = canvas.getContext('2d');
  campusMoodTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Campus Avg Mood (1 to 5)',
        data: dataPoints,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.35,
        borderWidth: 3,
        pointBackgroundColor: '#3b82f6',
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          min: 1,
          max: 5,
          ticks: { stepSize: 1 },
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// --- Early Detection Risk Alerts ---
async function loadRiskAlerts() {
  const container = document.getElementById('risk-alerts-container');
  if (!container) return;

  try {
    const data = await API.get('/api/counselor/risk-alerts');
    if (!data.alerts || data.alerts.length === 0) {
      container.innerHTML = `
        <div style="text-align:center;padding:24px;color:var(--text-muted);background:var(--surface-alt);border-radius:var(--radius-sm);">
          ✓ No students currently flagged for high-risk criteria. Campus wellness equilibrium is stable.
        </div>
      `;
      return;
    }

    container.innerHTML = data.alerts.map(alert => `
      <div class="risk-card">
        <div style="flex:1;min-width:280px;">
          <div class="risk-student-name">
            <span>⚠️</span>
            <span>${escapeHtml(alert.full_name)}</span>
            <span class="badge ${alert.severity === 'Critical' ? 'badge-danger' : 'badge-warning'}">${alert.severity} Risk</span>
          </div>
          <div style="font-size:0.85rem;color:var(--text-muted);margin-top:2px;">
            ID: ${escapeHtml(alert.student_id)} • ${escapeHtml(alert.department)} (${escapeHtml(alert.academic_year)}) • Contact: ${escapeHtml(alert.email)}
          </div>
          <div class="risk-reasons">
            ${alert.reasons.map(r => `<span class="risk-reason-pill">${escapeHtml(r)}</span>`).join('')}
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <button class="btn btn-sm btn-outline-primary" onclick="openStudentTimeline(${alert.user_id})">
            View Wellness Timeline
          </button>
          <button class="btn btn-sm btn-danger" onclick="prefillUrgentAppointment(${alert.user_id}, '${escapeHtml(alert.full_name)}')">
            Initiate Outreach
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading risk alerts:', err);
  }
}

// --- Appointment Queue Management ---
function initAppointmentQueueFilters() {
  const statusFilter = document.getElementById('queue-filter-status');
  const urgencyFilter = document.getElementById('queue-filter-urgency');

  if (statusFilter) {
    statusFilter.addEventListener('change', () => loadCounselorAppointments());
  }
  if (urgencyFilter) {
    urgencyFilter.addEventListener('change', () => loadCounselorAppointments());
  }
}

async function loadCounselorAppointments() {
  const container = document.getElementById('counselor-appointments-tbody');
  if (!container) return;

  const status = document.getElementById('queue-filter-status')?.value || 'All';
  const urgency = document.getElementById('queue-filter-urgency')?.value || 'All';

  try {
    const data = await API.get(`/api/counselor/appointments?status=${status}&urgency=${urgency}`);
    if (!data.appointments || data.appointments.length === 0) {
      container.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted);">No appointments found matching current filters.</td></tr>`;
      return;
    }

    container.innerHTML = data.appointments.map(app => `
      <tr>
        <td>
          <strong>${escapeHtml(app.student_name)}</strong><br>
          <small style="color:var(--text-muted);">${escapeHtml(app.student_id)} • ${escapeHtml(app.student_department)}</small>
        </td>
        <td>
          <strong>${escapeHtml(app.preferred_date)}</strong><br>
          <small style="color:var(--text-muted);">${escapeHtml(app.preferred_time_slot)}</small>
        </td>
        <td>${escapeHtml(app.category)}</td>
        <td>
          <span class="badge ${app.urgency === 'Immediate Support' ? 'badge-danger' : app.urgency === 'Priority' ? 'badge-warning' : 'badge-neutral'}">
            ${escapeHtml(app.urgency)}
          </span>
        </td>
        <td>
          <span class="badge ${app.status === 'Confirmed' ? 'badge-success' : app.status === 'Pending' ? 'badge-warning' : app.status === 'Completed' ? 'badge-info' : 'badge-neutral'}">
            ${escapeHtml(app.status)}
          </span>
        </td>
        <td>
          ${app.meeting_details ? `<span style="font-weight:600;color:var(--primary);">${escapeHtml(app.meeting_details)}</span>` : '<span style="color:var(--text-muted);font-style:italic;">Not set</span>'}
          ${app.counselor_notes ? `<br><small style="color:var(--text-muted);">${escapeHtml(app.counselor_notes)}</small>` : ''}
        </td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="openEditAppointmentModal(${app.id}, '${escapeHtml(app.status)}', '${escapeHtml(app.meeting_details)}', '${escapeHtml(app.counselor_notes)}')">
            Manage
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading counselor appointments:', err);
  }
}

// --- Edit Appointment Modal ---
function openEditAppointmentModal(id, status, meeting, notes) {
  currentEditingAppointmentId = id;
  const modal = document.getElementById('appointment-modal');
  if (!modal) return;

  document.getElementById('modal-app-id').value = id;
  document.getElementById('modal-app-status').value = status || 'Pending';
  document.getElementById('modal-meeting-details').value = meeting || 'Room 304, Campus Wellness Pavilion';
  document.getElementById('modal-counselor-notes').value = notes || '';

  modal.classList.add('active');
}

function initModalListeners() {
  const closeBtn = document.getElementById('close-modal-btn');
  const cancelBtn = document.getElementById('cancel-modal-btn');
  const modal = document.getElementById('appointment-modal');
  const form = document.getElementById('edit-appointment-form');

  if (closeBtn && modal) closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  if (cancelBtn && modal) cancelBtn.addEventListener('click', () => modal.classList.remove('active'));

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!currentEditingAppointmentId) return;

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving Changes...';

      const payload = {
        status: document.getElementById('modal-app-status').value,
        meeting_details: document.getElementById('modal-meeting-details').value.trim(),
        counselor_notes: document.getElementById('modal-counselor-notes').value.trim()
      };

      try {
        await API.put(`/api/counselor/appointments/${currentEditingAppointmentId}`, payload);
        showToast('Appointment record and clinical notes updated in database.', 'success');
        modal.classList.remove('active');
        await loadCounselorAppointments();
        await loadOverviewData();
      } catch (err) {
        showToast(err.message || 'Error updating appointment.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Updates';
      }
    });
  }

  // Student Timeline Modal Close
  const closeTimelineBtn = document.getElementById('close-timeline-modal-btn');
  const timelineModal = document.getElementById('student-timeline-modal');
  if (closeTimelineBtn && timelineModal) {
    closeTimelineBtn.addEventListener('click', () => timelineModal.classList.remove('active'));
  }
}

// --- Student Deep-Dive Timeline Modal ---
async function openStudentTimeline(userId) {
  const modal = document.getElementById('student-timeline-modal');
  if (!modal) return;

  modal.classList.add('active');
  const content = document.getElementById('timeline-modal-content');
  content.innerHTML = `<div style="text-align:center;padding:32px;">Loading student wellness history...</div>`;

  try {
    const data = await API.get(`/api/counselor/student/${userId}/timeline`);
    const st = data.student;

    content.innerHTML = `
      <div style="border-bottom:1px solid var(--border-light);padding-bottom:14px;margin-bottom:18px;">
        <h3 style="font-size:1.25rem;color:var(--text-main);">${escapeHtml(st.full_name)}</h3>
        <p style="color:var(--text-muted);font-size:0.9rem;">
          ID: ${escapeHtml(st.student_id)} • ${escapeHtml(st.department)} • ${escapeHtml(st.email)}
        </p>
      </div>

      <div style="margin-bottom:20px;">
        <h4 style="font-size:1rem;margin-bottom:8px;">Recent Mood Entries (${data.mood_logs.length})</h4>
        <div style="display:flex;flex-direction:column;gap:8px;max-height:220px;overflow-y:auto;">
          ${data.mood_logs.length === 0 ? '<p style="color:var(--text-muted);font-size:0.85rem;">No mood logs submitted yet.</p>' : data.mood_logs.map(m => `
            <div style="background:var(--surface-alt);padding:10px 14px;border-radius:var(--radius-sm);font-size:0.85rem;">
              <strong>${m.date_formatted}</strong>: Mood Score <strong>${m.mood_score}/5</strong> • Stress: ${m.academic_stress}/10 • Sleep: ${m.sleep_hours}h
              ${m.notes ? `<br><em style="color:var(--text-muted);">"${escapeHtml(m.notes)}"</em>` : ''}
            </div>
          `).join('')}
        </div>
      </div>

      <div style="margin-bottom:20px;">
        <h4 style="font-size:1rem;margin-bottom:8px;">Clinical Assessments (${data.assessments.length})</h4>
        <div style="display:flex;flex-direction:column;gap:8px;max-height:200px;overflow-y:auto;">
          ${data.assessments.length === 0 ? '<p style="color:var(--text-muted);font-size:0.85rem;">No assessments completed yet.</p>' : data.assessments.map(a => `
            <div style="background:var(--surface-alt);padding:10px 14px;border-radius:var(--radius-sm);font-size:0.85rem;">
              <strong>${escapeHtml(a.assessment_type)}</strong> (${a.date_formatted}) — Score: <strong>${a.total_score}/${a.max_score}</strong> 
              <span class="badge ${a.risk_level.includes('Severe') ? 'badge-danger' : a.risk_level.includes('Moderate') ? 'badge-warning' : 'badge-success'}">${escapeHtml(a.risk_level)}</span>
              <p style="margin-top:4px;color:var(--text-muted);">${escapeHtml(a.recommendations)}</p>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    content.innerHTML = `<div style="color:var(--status-danger);">Failed to load student timeline.</div>`;
  }
}

function prefillUrgentAppointment(userId, studentName) {
  openStudentTimeline(userId);
  showToast(`Reviewing timeline for ${studentName}. You can schedule an intervention directly.`, 'info');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}
