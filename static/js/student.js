/* ===============================================================
   Serene Minds - Student Wellness System
   Student Module Interactive Scripts
   (Mood Tracker, Assessments, Appointments, Wellness Hub, Web Audio)
   =============================================================== */

let studentMoodChart = null;
let breathingInterval = null;
let breathingPhase = 'idle'; // 'idle', 'inhale', 'hold', 'exhale'
let audioCtx = null;
let activeSoundNode = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initMoodTracker();
  initAssessmentModule();
  initAppointmentBooking();
  initWellnessHub();
  loadStudentDashboardData();
});

// --- Tab Switching ---
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      tabButtons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add('active');

      // Resize chart if tab was hidden
      if (targetId === 'overview-tab' && studentMoodChart) {
        studentMoodChart.resize();
      }
    });
  });
}

// --- Mood Tracker Initialization ---
function initMoodTracker() {
  const moodButtons = document.querySelectorAll('.mood-btn');
  let selectedMoodScore = 3;

  moodButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      moodButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedMoodScore = parseInt(btn.getAttribute('data-score'), 10);
    });
  });

  // Stress slider display update
  const stressSlider = document.getElementById('stress-slider');
  const stressValPill = document.getElementById('stress-val-display');
  if (stressSlider && stressValPill) {
    stressSlider.addEventListener('input', (e) => {
      stressValPill.textContent = e.target.value;
      if (e.target.value >= 8) {
        stressValPill.style.background = '#fef2f2';
        stressValPill.style.color = '#dc2626';
      } else if (e.target.value >= 5) {
        stressValPill.style.background = '#fffbeb';
        stressValPill.style.color = '#b45309';
      } else {
        stressValPill.style.background = '#ecfdf5';
        stressValPill.style.color = '#059669';
      }
    });
  }

  // Emotion Tags Pill Selection
  const tagPills = document.querySelectorAll('.tag-pill');
  tagPills.forEach(pill => {
    pill.addEventListener('click', () => {
      pill.classList.toggle('active');
    });
  });

  // Mood Form Submission
  const moodForm = document.getElementById('mood-log-form');
  if (moodForm) {
    moodForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = moodForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving Check-In...';

      const selectedTags = Array.from(document.querySelectorAll('.tag-pill.active')).map(p => p.getAttribute('data-tag'));
      const sleepHours = parseFloat(document.getElementById('sleep-input')?.value || 7.0);
      const stressScore = parseInt(document.getElementById('stress-slider')?.value || 5, 10);
      const energyScore = parseInt(document.getElementById('energy-select')?.value || 3, 10);
      const notes = document.getElementById('mood-notes')?.value.trim() || '';

      const payload = {
        mood_score: selectedMoodScore,
        sleep_hours: sleepHours,
        academic_stress: stressScore,
        energy_level: energyScore,
        emotion_tags: selectedTags,
        notes: notes
      };

      try {
        const res = await API.post('/api/mood/log', payload);
        showToast('Mood check-in saved to your wellness timeline!', 'success');

        // Append to mood logs list in DOM instantly
        prependMoodLogToDOM(res.log);

        // Reset notes and tag pills
        if (document.getElementById('mood-notes')) document.getElementById('mood-notes').value = '';
        tagPills.forEach(p => p.classList.remove('active'));

        // Refresh stats, chart, and recommendations
        await loadStudentDashboardData();
      } catch (err) {
        showToast(err.message || 'Could not save mood log. Please try again.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Daily Check-In';
      }
    });
  }
}

function getMoodEmoji(score) {
  switch (score) {
    case 1: return { emoji: '😫', label: 'Severe Distress', color: 'red' };
    case 2: return { emoji: '😔', label: 'Down / Anxious', color: 'amber' };
    case 3: return { emoji: '😐', label: 'Neutral / Okay', color: 'blue' };
    case 4: return { emoji: '😊', label: 'Good / Peaceful', color: 'green' };
    case 5: return { emoji: '✨', label: 'Thriving / Great', color: 'green' };
    default: return { emoji: '😐', label: 'Neutral', color: 'blue' };
  }
}

function prependMoodLogToDOM(log) {
  const container = document.getElementById('recent-mood-logs-list');
  if (!container) return;

  const emptyNotice = container.querySelector('.empty-state');
  if (emptyNotice) emptyNotice.remove();

  const meta = getMoodEmoji(log.mood_score);
  const item = document.createElement('div');
  item.className = 'log-item';
  item.innerHTML = `
    <div class="log-mood-display">
      <span class="log-emoji">${meta.emoji}</span>
      <div>
        <div class="log-score-tag">${meta.label} (${log.mood_score}/5)</div>
        <div class="log-meta">${log.date_formatted || 'Just now'} • Sleep: ${log.sleep_hours}h • Stress: ${log.academic_stress}/10</div>
        ${log.notes ? `<div style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;font-style:italic;">"${log.notes}"</div>` : ''}
      </div>
    </div>
    <div class="log-details">
      ${log.emotion_tags && log.emotion_tags.length ? log.emotion_tags.map(t => `<span class="badge badge-neutral">${t}</span>`).join('') : ''}
    </div>
  `;
  container.prepend(item);
}

// --- Load Student Dashboard Data & Chart ---
async function loadStudentDashboardData() {
  try {
    // 1. Fetch Mood History & Stats
    const moodData = await API.get('/api/mood/history');
    if (moodData) {
      if (document.getElementById('stat-total-logs')) {
        document.getElementById('stat-total-logs').textContent = moodData.stats.total_logs;
      }
      if (document.getElementById('stat-avg-mood')) {
        document.getElementById('stat-avg-mood').textContent = moodData.stats.avg_mood ? `${moodData.stats.avg_mood}/5` : 'N/A';
      }
      if (document.getElementById('stat-avg-sleep')) {
        document.getElementById('stat-avg-sleep').textContent = moodData.stats.avg_sleep ? `${moodData.stats.avg_sleep} hrs` : 'N/A';
      }
      if (document.getElementById('stat-avg-stress')) {
        document.getElementById('stat-avg-stress').textContent = moodData.stats.avg_stress ? `${moodData.stats.avg_stress}/10` : 'N/A';
      }

      // Render logs list
      const listContainer = document.getElementById('recent-mood-logs-list');
      if (listContainer && moodData.logs) {
        if (moodData.logs.length === 0) {
          listContainer.innerHTML = `<div class="empty-state" style="text-align:center;padding:24px;color:var(--text-muted);">No check-ins logged yet. Log your first check-in above!</div>`;
        } else {
          listContainer.innerHTML = '';
          moodData.logs.slice(0, 10).forEach(log => {
            const meta = getMoodEmoji(log.mood_score);
            const div = document.createElement('div');
            div.className = 'log-item';
            div.innerHTML = `
              <div class="log-mood-display">
                <span class="log-emoji">${meta.emoji}</span>
                <div>
                  <div class="log-score-tag">${meta.label} (${log.mood_score}/5)</div>
                  <div class="log-meta">${log.date_formatted} • Sleep: ${log.sleep_hours}h • Stress: ${log.academic_stress}/10</div>
                  ${log.notes ? `<div style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;font-style:italic;">"${escapeHtml(log.notes)}"</div>` : ''}
                </div>
              </div>
              <div class="log-details">
                ${log.emotion_tags && log.emotion_tags.length ? log.emotion_tags.map(t => `<span class="badge badge-neutral">${escapeHtml(t)}</span>`).join('') : ''}
              </div>
            `;
            listContainer.appendChild(div);
          });
        }
      }

      // Render or Update Student Mood Chart
      renderStudentMoodChart(moodData.logs);
    }

    // 2. Fetch Personalized Recommendations
    const recData = await API.get('/api/wellness/recommendations');
    const recContainer = document.getElementById('personalized-recommendations-list');
    if (recContainer && recData && recData.recommendations) {
      recContainer.innerHTML = '';
      recData.recommendations.forEach(rec => {
        const item = document.createElement('div');
        item.className = `rec-item ${rec.type || ''}`;
        item.innerHTML = `
          <div class="rec-item-title">
            <span>${rec.type === 'alert' || rec.type === 'urgent' ? '⚠️' : '🌿'}</span>
            <span>${rec.title}</span>
          </div>
          <div class="rec-item-desc">${rec.description}</div>
          <a href="${rec.action_target}" class="btn btn-sm ${rec.type === 'alert' || rec.type === 'urgent' ? 'btn-danger' : 'btn-outline-primary'} rec-item-btn">${rec.action_label}</a>
        `;
        recContainer.appendChild(item);
      });
    }

    // 3. Fetch Student Appointments
    loadStudentAppointments();
  } catch (err) {
    console.error('Error loading student dashboard data:', err);
  }
}

// Chart.js rendering for student
function renderStudentMoodChart(logs) {
  const chartCanvas = document.getElementById('studentMoodChart');
  if (!chartCanvas || typeof Chart === 'undefined') return;

  // Prepare chronological order for chart (last 7 logs)
  const chartLogs = [...(logs || [])].slice(0, 7).reverse();
  const labels = chartLogs.map(l => l.date_formatted || 'Day');
  const moodScores = chartLogs.map(l => l.mood_score);
  const stressScores = chartLogs.map(l => l.academic_stress);

  if (studentMoodChart) {
    studentMoodChart.data.labels = labels;
    studentMoodChart.data.datasets[0].data = moodScores;
    studentMoodChart.data.datasets[1].data = stressScores;
    studentMoodChart.update();
    return;
  }

  const ctx = chartCanvas.getContext('2d');
  studentMoodChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [
        {
          label: 'Mood Level (1 to 5)',
          data: moodScores.length ? moodScores : [3, 4, 3, 2, 4, 5, 4],
          borderColor: '#4a7c59',
          backgroundColor: 'rgba(74, 124, 89, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: '#4a7c59',
          yAxisID: 'y'
        },
        {
          label: 'Academic Stress (1 to 10)',
          data: stressScores.length ? stressScores : [6, 5, 7, 8, 5, 3, 4],
          borderColor: '#f59e0b',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#f59e0b',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { weight: '600' } } },
        tooltip: { padding: 10, cornerRadius: 8 }
      },
      scales: {
        y: {
          min: 1,
          max: 5,
          ticks: { stepSize: 1 },
          title: { display: true, text: 'Mood (1-5)' },
          grid: { color: 'rgba(0,0,0,0.04)' }
        },
        y1: {
          min: 1,
          max: 10,
          position: 'right',
          ticks: { stepSize: 2 },
          title: { display: true, text: 'Stress (1-10)' },
          grid: { drawOnChartArea: false }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// --- Assessment Questionnaire Logic ---
function initAssessmentModule() {
  const options = document.querySelectorAll('.option-choice');
  options.forEach(opt => {
    opt.addEventListener('click', () => {
      const parentRow = opt.closest('.options-row');
      parentRow.querySelectorAll('.option-choice').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
    });
  });

  const assessmentForm = document.getElementById('assessment-form');
  if (assessmentForm) {
    assessmentForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const type = document.getElementById('assessment-type-select')?.value || 'GAD-7';
      const questionBlocks = document.querySelectorAll('.question-block');
      const answers = {};
      let allAnswered = true;

      questionBlocks.forEach(block => {
        const qId = block.getAttribute('data-qid');
        const selected = block.querySelector('.option-choice.selected');
        if (!selected) {
          allAnswered = false;
        } else {
          answers[qId] = parseInt(selected.getAttribute('data-value'), 10);
        }
      });

      if (!allAnswered) {
        showToast('Please answer all questions before submitting the assessment.', 'warning');
        return;
      }

      const submitBtn = assessmentForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Analyzing Results...';

      try {
        const res = await API.post('/api/assessment/submit', {
          assessment_type: type,
          answers: answers,
          details_json: JSON.stringify(answers)
        });

        showToast('Assessment submitted and evaluated!', 'success');
        displayAssessmentResult(res.result);
      } catch (err) {
        showToast(err.message || 'Error submitting assessment.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit & View Clinical Analysis';
      }
    });
  }
}

function displayAssessmentResult(result) {
  const resultCard = document.getElementById('assessment-result-card');
  if (!resultCard) return;

  const scoreDisplay = document.getElementById('result-score-display');
  const riskBadge = document.getElementById('result-risk-badge');
  const recDisplay = document.getElementById('result-recommendations');

  if (scoreDisplay) scoreDisplay.textContent = `${result.total_score} / ${result.max_score}`;
  if (riskBadge) {
    riskBadge.textContent = result.risk_level;
    riskBadge.className = 'badge';
    if (result.risk_level.includes('Severe') || result.risk_level.includes('High')) {
      riskBadge.classList.add('badge-danger');
    } else if (result.risk_level.includes('Moderate')) {
      riskBadge.classList.add('badge-warning');
    } else {
      riskBadge.classList.add('badge-success');
    }
  }
  if (recDisplay) recDisplay.textContent = result.recommendations;

  resultCard.style.display = 'block';
  resultCard.scrollIntoView({ behavior: 'smooth' });
}

// --- Appointment Booking ---
function initAppointmentBooking() {
  const appForm = document.getElementById('appointment-request-form');
  if (appForm) {
    appForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = appForm.querySelector('button[type="submit"]');

      const preferred_date = document.getElementById('app-date').value;
      const preferred_time_slot = document.getElementById('app-time').value;
      const category = document.getElementById('app-category').value;
      const urgency = document.getElementById('app-urgency').value;
      const student_notes = document.getElementById('app-notes').value.trim();

      if (!preferred_date || !preferred_time_slot) {
        showToast('Please select a preferred date and time slot.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting Request...';

      try {
        await API.post('/api/appointment/create', {
          preferred_date,
          preferred_time_slot,
          category,
          urgency,
          student_notes
        });
        showToast('Your session request has been submitted to the counseling office.', 'success');
        appForm.reset();
        await loadStudentAppointments();
      } catch (err) {
        showToast(err.message || 'Failed to submit appointment request.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Request Confidential Session';
      }
    });
  }
}

async function loadStudentAppointments() {
  const container = document.getElementById('student-appointments-list');
  if (!container) return;

  try {
    const data = await API.get('/api/appointment/my');
    if (!data.appointments || data.appointments.length === 0) {
      container.innerHTML = `<div style="text-align:center;padding:24px;color:var(--text-muted);">You have no appointment requests logged. Need guidance? Book a session above.</div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Category</th>
              <th>Urgency</th>
              <th>Status</th>
              <th>Counselor Location / Link</th>
            </tr>
          </thead>
          <tbody>
            ${data.appointments.map(app => `
              <tr>
                <td><strong>${escapeHtml(app.preferred_date)}</strong><br><small style="color:var(--text-muted);">${escapeHtml(app.preferred_time_slot)}</small></td>
                <td>${escapeHtml(app.category)}</td>
                <td><span class="badge ${app.urgency === 'Immediate Support' ? 'badge-danger' : app.urgency === 'Priority' ? 'badge-warning' : 'badge-neutral'}">${escapeHtml(app.urgency)}</span></td>
                <td><span class="badge ${app.status === 'Confirmed' ? 'badge-success' : app.status === 'Pending' ? 'badge-warning' : 'badge-neutral'}">${escapeHtml(app.status)}</span></td>
                <td>
                  ${app.meeting_details ? `<span style="color:var(--primary);font-weight:600;">${escapeHtml(app.meeting_details)}</span>` : '<span style="color:var(--text-muted);font-style:italic;">Pending counselor review</span>'}
                  ${app.counselor_notes ? `<br><small style="color:var(--text-muted);">${escapeHtml(app.counselor_notes)}</small>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    console.error('Error loading appointments:', err);
  }
}

// --- Interactive Wellness Hub & 4-7-8 Breathing & Soundscapes ---
function initWellnessHub() {
  const startBreathBtn = document.getElementById('start-breathing-btn');
  const circle = document.getElementById('breathing-circle-elem');
  const phaseText = document.getElementById('breathing-phase-elem');
  const timerText = document.getElementById('breathing-timer-elem');
  const instruction = document.getElementById('breathing-instruction-elem');

  if (startBreathBtn && circle) {
    let isRunning = false;
    let currentStep = 0; // 0: Inhale (4s), 1: Hold (7s), 2: Exhale (8s)
    let secondsLeft = 4;

    startBreathBtn.addEventListener('click', () => {
      if (isRunning) {
        clearInterval(breathingInterval);
        isRunning = false;
        startBreathBtn.textContent = 'Begin 4-7-8 Breathing';
        startBreathBtn.className = 'btn btn-primary';
        phaseText.textContent = 'READY';
        timerText.textContent = '4';
        instruction.textContent = 'Click Begin to start the calming cycle.';
        circle.style.transform = 'scale(1)';
        return;
      }

      isRunning = true;
      startBreathBtn.textContent = 'Pause Exercise';
      startBreathBtn.className = 'btn btn-outline';
      currentStep = 0;
      secondsLeft = 4;
      runBreathingStep();

      breathingInterval = setInterval(() => {
        secondsLeft--;
        if (secondsLeft <= 0) {
          currentStep = (currentStep + 1) % 3;
          runBreathingStep();
        } else {
          timerText.textContent = secondsLeft;
        }
      }, 1000);
    });

    function runBreathingStep() {
      if (currentStep === 0) {
        secondsLeft = 4;
        phaseText.textContent = 'INHALE';
        instruction.textContent = 'Breathe in slowly through your nose...';
        circle.style.transition = 'transform 4s ease-out';
        circle.style.transform = 'scale(1.55)';
      } else if (currentStep === 1) {
        secondsLeft = 7;
        phaseText.textContent = 'HOLD';
        instruction.textContent = 'Gently hold your breath. Stay relaxed...';
        circle.style.transition = 'transform 0.5s ease';
        circle.style.transform = 'scale(1.55)';
      } else {
        secondsLeft = 8;
        phaseText.textContent = 'EXHALE';
        instruction.textContent = 'Slowly exhale all air through your mouth...';
        circle.style.transition = 'transform 8s ease-in-out';
        circle.style.transform = 'scale(1.0)';
      }
      timerText.textContent = secondsLeft;
    }
  }

  // Web Audio Ambient Synthesizer (Rain & Gentle Waves)
  initAmbientSoundscapes();
}

function initAmbientSoundscapes() {
  const rainBtn = document.getElementById('play-rain-btn');
  const wavesBtn = document.getElementById('play-waves-btn');

  if (rainBtn) {
    rainBtn.addEventListener('click', () => toggleAudio('rain', rainBtn));
  }
  if (wavesBtn) {
    wavesBtn.addEventListener('click', () => toggleAudio('waves', wavesBtn));
  }
}

function toggleAudio(type, btn) {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
  }

  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }

  if (activeSoundNode && activeSoundNode.type === type) {
    activeSoundNode.stop();
    activeSoundNode = null;
    btn.textContent = `Play ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    btn.classList.remove('btn-secondary');
    btn.classList.add('btn-outline-primary');
    return;
  }

  // Stop previous sound if any
  if (activeSoundNode) {
    activeSoundNode.stop();
    document.querySelectorAll('.soundscape-card button').forEach(b => {
      b.classList.remove('btn-secondary');
      b.classList.add('btn-outline-primary');
      if (b.id.includes('rain')) b.textContent = 'Play Gentle Rain';
      if (b.id.includes('waves')) b.textContent = 'Play Ocean Waves';
    });
  }

  // Synthesize ambient audio with Web Audio API
  const bufferSize = audioCtx.sampleRate * 3;
  const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const output = noiseBuffer.getChannelData(0);

  // Generate pink/brown noise
  let lastOut = 0.0;
  for (let i = 0; i < bufferSize; i++) {
    const white = Math.random() * 2 - 1;
    lastOut = (lastOut + 0.02 * white) / 1.02;
    output[i] = type === 'rain' ? (white * 0.05 + lastOut * 0.5) : (lastOut * 0.9);
  }

  const whiteNoise = audioCtx.createBufferSource();
  whiteNoise.buffer = noiseBuffer;
  whiteNoise.loop = true;

  const filter = audioCtx.createBiquadFilter();
  filter.type = type === 'rain' ? 'lowpass' : 'bandpass';
  filter.frequency.value = type === 'rain' ? 800 : 380;
  filter.Q.value = 1.0;

  const gainNode = audioCtx.createGain();
  gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);

  whiteNoise.connect(filter);
  filter.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  whiteNoise.start();

  activeSoundNode = {
    type: type,
    stop: () => {
      try {
        whiteNoise.stop();
        whiteNoise.disconnect();
      } catch (e) {}
    }
  };

  btn.textContent = `Pause ${type.charAt(0).toUpperCase() + type.slice(1)}`;
  btn.classList.remove('btn-outline-primary');
  btn.classList.add('btn-secondary');
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
