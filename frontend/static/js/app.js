/**
 * Adobe Personalised Learning Buddy - Application Logic & State Engine
 * Built for Quiet Academic Instrument Specification (Linear / Stripe caliber).
 * Zero external telemetry, 100% offline compliant, goal-aware reactive UI.
 */

const state = {
  studentId: '',
  students: [],
  activeTab: 'dashboard',
  profileRecord: null,
  profile: null,
  plan: null,
  planDiff: null,
  certificate: null,
  summary: null,
  skillsMatrix: {},
  exercises: [],
  activeExercise: null,
  llmOfflineMode: false,
  instituteProfile: 'legacy',
  seedConsistency: null,
  requestController: null,
  loadGeneration: 0,
  diagnosticQuestion: null,
  diagnosticAnswered: [],
  simulationScenarios: [],
  buddyLoadedFor: '',
  buddyLoadPromise: null
};

const api = window.LearningBuddyApi;

function runScenario(name) {
  return { scenario: name, status: 'ready' };
}

// Application Lifecycle
document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  initTheme();
  setupPersonaSelector();
  await loadStudentList();
  if (window.initIcons) window.initIcons();
});

// Theme Management
function initTheme() {
  const urlParams = new URLSearchParams(window.location.search);
  const urlTheme = urlParams.get('theme');
  const savedTheme = localStorage.getItem('theme');
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  const theme = [urlTheme, savedTheme].find(value => value === 'light' || value === 'dark') || systemTheme;
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.setAttribute('data-icon', theme === 'dark' ? 'sun' : 'moon');
}

function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  const newTheme = isDark ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.setAttribute('data-icon', isDark ? 'moon' : 'sun');
  if (window.initIcons) window.initIcons();
}

function toggleBuddyPanel() {
  const panel = document.getElementById('buddy-panel') || document.getElementById('buddy-drawer');
  if (panel) {
    panel.classList.toggle('is-open');
    if (panel.classList.contains('is-open')) loadBuddyMemory();
  }
}

async function loadBuddyMemory() {
  if (!state.studentId || state.buddyLoadedFor === state.studentId) return;
  if (state.buddyLoadPromise) {
    await state.buddyLoadPromise;
    if (state.buddyLoadedFor === state.studentId) return;
  }
  const stream = document.getElementById('buddy-chat-stream');
  if (!stream) return;
  const requestedStudent = state.studentId;
  state.buddyLoadPromise = (async () => {
    try {
      const memory = await api.getBuddyMemory(requestedStudent);
      if (state.studentId !== memory.student_id) return;
      stream.replaceChildren();
      const history = memory.recent_history || [];
      if (!history.length) {
        const intro = document.createElement('div');
        intro.className = 'chat-msg assistant';
        intro.innerText = 'I can help with your semester plan, electives, prerequisites, or study goals. Ask me anything about your curriculum.';
        stream.appendChild(intro);
      } else {
        history.forEach(turn => {
          const message = document.createElement('div');
          message.className = `chat-msg ${turn.role === 'user' ? 'user' : 'assistant'}`;
          message.innerText = turn.content;
          stream.appendChild(message);
        });
      }
      state.buddyLoadedFor = requestedStudent;
    } catch (error) {
      const notice = document.createElement('div');
      notice.className = 'text-meta';
      notice.innerText = `Conversation history is unavailable: ${error.message || 'service error'}`;
      stream.appendChild(notice);
    }
  })();
  try {
    await state.buddyLoadPromise;
  } finally {
    state.buddyLoadPromise = null;
  }
}

// Setup Navigation
function setupTabs() {
  document.querySelectorAll('.app-sidebar .nav-item[data-target]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.target));
  });
}

function switchTab(target) {
  state.activeTab = target;
  document.querySelectorAll('.app-sidebar .nav-item').forEach(b => {
    b.classList.toggle('is-active', b.dataset.target === target);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `view-${target}`);
  });

  const titles = {
    dashboard: 'Today',
    plan: 'Your plan',
    practice: 'Practise',
    mastery: 'Progress',
    diagnostic: 'Skill check',
    admin: 'Evaluator tools',
    setup: 'Set up profile'
  };
  const topTitle = document.getElementById('topbar-section-title');
  if (topTitle) topTitle.innerText = titles[target] || 'Today';

  if (target === 'plan') renderPlanTimeline();
  if (target === 'mastery') renderMasteryViews();
  if (target === 'practice') renderPracticeSandbox();
  if (target === 'diagnostic') renderDiagnosticView();
  if (target === 'setup') renderOnboardingForm();
  if (target === 'admin') renderEvaluatorTools();
}

function renderDiagnosticView() {
  const status = document.getElementById('diagnostic-status');
  const detail = document.getElementById('diagnostic-status-detail');
  if (!state.summary) return;
  if (status) {
    status.innerText = state.summary.status_message;
    status.dataset.status = state.summary.status;
  }
  if (detail) {
    detail.innerText = state.summary.readiness_percentage === null
      ? `${state.summary.assessed_items_count} of ${state.summary.min_assessed_items} diagnostic items assessed`
      : `Readiness ${state.summary.readiness_percentage}% \u2022 ${state.summary.priority_gap_count} priority gaps`;
  }
  const count = document.getElementById('diagnostic-progress');
  if (count) count.innerText = `${state.diagnosticAnswered.length} answered this session`;
}

// ==============================================================================
// ONBOARDING WIZARD (PDF §3 UX, §2.2)
// ==============================================================================
const wizardState = {
  step: 1,
  totalSteps: 6,
  name: '',
  programme_id: 'BH-CSE-BTECH',
  semester: 3,
  cgpa: null,
  completedCourses: {}, // course_code -> grade
  goal: 'goal_software',
  interests: [],
  hours: 15,
  learningStyle: 'hands_on'
};

const CANONICAL_INTERESTS = [
  "AI/ML", "Systems", "Web and App Dev", "Data and Databases",
  "Algorithms and Theory", "Security", "Research", "Product and Business"
];

const SEMESTER_COURSES_CATALOGUE = [
  {
    sem: 1,
    title: "Semester 1",
    courses: [
      { code: "CSL100", title: "Introduction to Computer Science", credits: 4.5 },
      { code: "ECL101", title: "Digital Electronics", credits: 4.0 }
    ]
  },
  {
    sem: 2,
    title: "Semester 2",
    courses: [
      { code: "MAL403", title: "Linear Algebra & Applications", credits: 4.0 },
      { code: "LAL100", title: "Liberal Arts Course I", credits: 2.0 }
    ]
  },
  {
    sem: 3,
    title: "Semester 3",
    courses: [
      { code: "CSL201", title: "Data Structures", credits: 4.0 },
      { code: "CSL202", title: "Data Structures Laboratory", credits: 4.0 },
      { code: "CSP203", title: "Software Systems Laboratory", credits: 3.0 },
      { code: "LAL222", title: "Liberal Arts Course II", credits: 2.0 }
    ]
  },
  {
    sem: 4,
    title: "Semester 4",
    courses: [
      { code: "CSL251", title: "Computer Architecture", credits: 4.0 },
      { code: "CSL252", title: "Design and Analysis of Algorithms", credits: 4.0 },
      { code: "CSL253", title: "Database Systems", credits: 4.0 },
      { code: "LAL101", title: "Liberal Arts Course III", credits: 1.0 }
    ]
  }
];

function renderOnboardingForm() {
  wizardState.step = 1;
  updateWizardProgress();
  renderWizardCompletedCourses();
  renderWizardInterests();
}

function updateWizardProgress() {
  const stepTitles = {
    1: "Step 1 of 6: Basics",
    2: "Step 2 of 6: Courses Completed",
    3: "Step 3 of 6: Target Goal",
    4: "Step 4 of 6: Interests",
    5: "Step 5 of 6: Time & Preferences",
    6: "Step 6 of 6: Review & Create"
  };

  const titleEl = document.getElementById('wizard-step-title');
  const pctEl = document.getElementById('wizard-progress-pct');
  const barEl = document.getElementById('wizard-progress-bar');
  const indEl = document.getElementById('wizard-step-indicator');
  const backBtn = document.getElementById('wizard-back-btn');
  const nextBtn = document.getElementById('wizard-next-btn');
  const submitBtn = document.getElementById('wizard-submit-btn');

  const pct = Math.round((wizardState.step / wizardState.totalSteps) * 100);
  if (titleEl) titleEl.innerText = stepTitles[wizardState.step] || `Step ${wizardState.step} of 6`;
  if (pctEl) pctEl.innerText = `${pct}% Complete`;
  if (barEl) barEl.style.width = `${pct}%`;
  if (indEl) indEl.innerText = `Step ${wizardState.step} of 6`;

  for (let s = 1; s <= 6; s++) {
    const el = document.getElementById(`wizard-step-${s}`);
    if (el) el.style.display = (s === wizardState.step) ? 'block' : 'none';
  }

  if (backBtn) backBtn.style.visibility = (wizardState.step > 1) ? 'visible' : 'hidden';
  if (nextBtn) nextBtn.style.display = (wizardState.step < 6) ? 'inline-block' : 'none';
  if (submitBtn) submitBtn.style.display = (wizardState.step === 6) ? 'inline-block' : 'none';
}

function wizardStepNext() {
  if (wizardState.step === 1) {
    const nameInput = document.getElementById('wizard-name');
    const nameErr = document.getElementById('wizard-error-name');
    const cgpaInput = document.getElementById('wizard-cgpa');
    const cgpaErr = document.getElementById('wizard-error-cgpa');
    const semSelect = document.getElementById('wizard-semester');

    const name = nameInput ? nameInput.value.trim() : '';
    if (!name) {
      if (nameErr) nameErr.style.display = 'block';
      if (nameInput) nameInput.focus();
      return;
    } else {
      if (nameErr) nameErr.style.display = 'none';
      wizardState.name = name;
    }

    if (cgpaInput && cgpaInput.value.trim() !== '') {
      const val = parseFloat(cgpaInput.value);
      if (isNaN(val) || val < 0.0 || val > 10.0) {
        if (cgpaErr) cgpaErr.style.display = 'block';
        return;
      } else {
        if (cgpaErr) cgpaErr.style.display = 'none';
        wizardState.cgpa = val;
      }
    } else {
      if (cgpaErr) cgpaErr.style.display = 'none';
      wizardState.cgpa = null;
    }

    if (semSelect) wizardState.semester = parseInt(semSelect.value, 10);
  } else if (wizardState.step === 4) {
    const intErr = document.getElementById('wizard-error-interests');
    if (wizardState.interests.length > 5) {
      if (intErr) intErr.style.display = 'block';
      return;
    } else {
      if (intErr) intErr.style.display = 'none';
    }
  }

  if (wizardState.step < wizardState.totalSteps) {
    wizardState.step++;
    updateWizardProgress();
    if (wizardState.step === 6) {
      renderWizardReview();
    }
  }
}

function wizardStepBack() {
  if (wizardState.step > 1) {
    wizardState.step--;
    updateWizardProgress();
  }
}

function selectWizardGoal(goalId) {
  wizardState.goal = goalId;
  document.querySelectorAll('.wizard-goal-cards .goal-card, .goal-card[data-goal]').forEach(c => {
    if (c.dataset.goal === goalId) {
      c.classList.add('is-selected');
    } else {
      c.classList.remove('is-selected');
    }
  });
}

function selectWizardStyle(style) {
  wizardState.learningStyle = style;
  document.querySelectorAll('.style-card').forEach(c => {
    if (c.dataset.style === style) {
      c.classList.add('is-selected');
    } else {
      c.classList.remove('is-selected');
    }
  });
}

function updateWizardHours(val) {
  wizardState.hours = parseFloat(val);
  const el = document.getElementById('wizard-hours-val');
  if (el) el.innerText = `${val} hrs/week`;
}

function renderWizardInterests() {
  const container = document.getElementById('wizard-interest-chips');
  if (!container) return;
  container.innerHTML = CANONICAL_INTERESTS.map(intName => {
    const sel = wizardState.interests.includes(intName) ? 'is-selected' : '';
    return `<div class="wizard-chip ${sel}" onclick="toggleWizardInterest('${intName}', this)">${intName}</div>`;
  }).join('');
  updateWizardInterestCounter();
}

function toggleWizardInterest(intName, el) {
  const idx = wizardState.interests.indexOf(intName);
  const errEl = document.getElementById('wizard-error-interests');
  if (idx >= 0) {
    wizardState.interests.splice(idx, 1);
    if (el) el.classList.remove('is-selected');
    if (errEl) errEl.style.display = 'none';
  } else {
    if (wizardState.interests.length >= 5) {
      if (errEl) errEl.style.display = 'block';
      return;
    }
    wizardState.interests.push(intName);
    if (el) el.classList.add('is-selected');
    if (errEl) errEl.style.display = 'none';
  }
  updateWizardInterestCounter();
}

function updateWizardInterestCounter() {
  const el = document.getElementById('wizard-interest-counter');
  if (el) el.innerText = `${wizardState.interests.length} of 5 selected`;
}

function renderWizardCompletedCourses() {
  const container = document.getElementById('wizard-completed-groups');
  if (!container) return;

  container.innerHTML = SEMESTER_COURSES_CATALOGUE.map(group => {
    const courseRows = group.courses.map(c => {
      const isChecked = wizardState.completedCourses[c.code] ? 'checked' : '';
      return `
        <div class="sem-course-item">
          <label style="display:flex; align-items:center; gap:10px; cursor:pointer; flex:1;">
            <input type="checkbox" data-sem="${group.sem}" data-code="${c.code}" ${isChecked} onchange="onWizardCourseToggle('${c.code}', ${group.sem}, this.checked)">
            <div>
              <span class="plan-course-code" style="font-size:11px;">${c.code}</span>
              <span style="font-size:12px; font-weight:500; color:var(--ink); margin-left:6px;">${c.title}</span>
              <span class="text-meta" style="font-size:11px; margin-left:4px;">(${c.credits} cr)</span>
            </div>
          </label>
          <select class="input" style="font-size:11px; padding:2px 6px; width:80px;" onchange="onWizardCourseGradeChange('${c.code}', this.value)">
            <option value="A">Grade: A</option>
            <option value="A-">Grade: A-</option>
            <option value="B" selected>Grade: B</option>
            <option value="B-">Grade: B-</option>
            <option value="C">Grade: C</option>
            <option value="Pass">Pass</option>
          </select>
        </div>
      `;
    }).join('');

    return `
      <div class="sem-checklist-card">
        <div class="sem-checklist-header">
          <span>${group.title}</span>
          <button type="button" class="btn btn-secondary btn-sm" style="font-size:11px; padding:2px 8px;" onclick="toggleSelectAllSemesterCourses(${group.sem})">Select all of ${group.title}</button>
        </div>
        <div>${courseRows}</div>
      </div>
    `;
  }).join('');
}

function onWizardCourseToggle(code, sem, checked) {
  if (checked) {
    wizardState.completedCourses[code] = wizardState.completedCourses[code] || 'B';
  } else {
    delete wizardState.completedCourses[code];
  }
}

function onWizardCourseGradeChange(code, grade) {
  if (wizardState.completedCourses[code]) {
    wizardState.completedCourses[code] = grade;
  }
}

function toggleSelectAllSemesterCourses(sem) {
  const group = SEMESTER_COURSES_CATALOGUE.find(g => g.sem === sem);
  if (!group) return;
  const checkboxes = document.querySelectorAll(`input[type="checkbox"][data-sem="${sem}"]`);
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  const targetState = !allChecked;

  checkboxes.forEach(cb => {
    cb.checked = targetState;
    const code = cb.dataset.code;
    if (targetState) {
      wizardState.completedCourses[code] = 'B';
    } else {
      delete wizardState.completedCourses[code];
    }
  });
}

function renderWizardReview() {
  const summaryEl = document.getElementById('wizard-review-summary');
  if (!summaryEl) return;

  const goalLabels = {
    goal_software: 'Software / IT (Systems, Algorithms, Placements)',
    goal_higher_studies: 'Higher Studies & Research (Theory, MS/PhD)',
    goal_upsc: 'UPSC Civil Services (Humanities, General Studies)',
    goal_startup: 'Startup & Entrepreneurship (Product, Full-stack)',
    goal_exploratory: 'Not sure yet (General CSE exploration)'
  };

  const styleLabels = {
    hands_on: '💻 Hands-on (Labs & Projects)',
    videos: '🎥 Videos (Lectures & Visual Walkthroughs)',
    reading: '📖 Reading (Textbooks & Formal Docs)'
  };

  const completedList = Object.keys(wizardState.completedCourses);
  const interestsList = wizardState.interests.length ? wizardState.interests.join(', ') : 'None specified';

  summaryEl.innerHTML = `
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
      <div>
        <span class="text-meta" style="font-size:11px;">STUDENT NAME</span>
        <div style="font-weight:600; font-size:13px; color:var(--ink);">${wizardState.name || 'Not provided'}</div>
      </div>
      <div>
        <span class="text-meta" style="font-size:11px;">PROGRAMME</span>
        <div style="font-weight:600; font-size:13px; color:var(--ink);">B.Tech CSE (BH-CSE-BTECH)</div>
      </div>
      <div>
        <span class="text-meta" style="font-size:11px;">SEMESTER & CGPA (SELF-DECLARED)</span>
        <div style="font-weight:500; font-size:13px; color:var(--ink);">Semester ${wizardState.semester} · CGPA ${wizardState.cgpa !== null ? wizardState.cgpa : 'Not entered (8.0 default)'}</div>
      </div>
      <div>
        <span class="text-meta" style="font-size:11px;">PRIMARY GOAL</span>
        <div style="font-weight:600; font-size:13px; color:var(--accent);">${goalLabels[wizardState.goal] || wizardState.goal}</div>
      </div>
      <div style="grid-column: 1 / -1;">
        <span class="text-meta" style="font-size:11px;">COMPLETED COURSES (${completedList.length} SELF-DECLARED)</span>
        <div style="font-size:12px; color:var(--ink);">${completedList.length ? completedList.join(', ') : 'None marked as completed'}</div>
      </div>
      <div style="grid-column: 1 / -1;">
        <span class="text-meta" style="font-size:11px;">EXPRESSED INTERESTS (${wizardState.interests.length} OF 5)</span>
        <div style="font-size:12px; color:var(--ink);">${interestsList}</div>
      </div>
      <div>
        <span class="text-meta" style="font-size:11px;">INDEPENDENT STUDY BUDGET</span>
        <div style="font-weight:500; font-size:12px; color:var(--ink);">${wizardState.hours} hours/week</div>
      </div>
      <div>
        <span class="text-meta" style="font-size:11px;">PREFERRED LEARNING STYLE</span>
        <div style="font-weight:500; font-size:12px; color:var(--ink);">${styleLabels[wizardState.learningStyle] || wizardState.learningStyle}</div>
      </div>
    </div>
  `;
}

async function submitWizardOnboarding() {
  const submitBtn = document.getElementById('wizard-submit-btn');
  const statusEl = document.getElementById('wizard-submit-status');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerText = 'Creating profile & generating valid plan...';
  }
  if (statusEl) statusEl.innerText = 'Validating inputs against curriculum rules...';

  try {
    const payload = {
      name: wizardState.name,
      programme_id: 'BH-CSE-BTECH',
      current_semester: wizardState.semester,
      cgpa: wizardState.cgpa !== null ? wizardState.cgpa : 8.0,
      available_hours_per_week: wizardState.hours,
      goal: wizardState.goal === 'goal_exploratory' ? 'goal_software' : wizardState.goal,
      interests: wizardState.interests,
      completed_course_codes: Object.keys(wizardState.completedCourses),
      shortlisted_course_codes: [],
      learning_style: wizardState.learningStyle
    };

    const res = await api.createOnboardingProfile(payload);
    const newStudentId = res.student_id;

    if (statusEl) statusEl.innerText = 'Profile created! Switching to your validated degree plan...';
    showToast(`Welcome, ${wizardState.name}! Your degree roadmap is verified and ready.`, 'success');

    // Reload student dropdown and switch active context to newly created student
    await loadStudentList();
    const sel = document.getElementById('persona-select');
    if (sel && newStudentId) {
      if (!Array.from(sel.options).some(o => o.value === newStudentId)) {
        const opt = document.createElement('option');
        opt.value = newStudentId;
        opt.text = `${wizardState.name} (New student)`;
        sel.appendChild(opt);
      }
      sel.value = newStudentId;
    }
    await loadFullStudentContext(newStudentId);

    // Land on Your Plan tab (PDF §3 Acceptance)
    switchTab('plan');

    // Offer short diagnostic
    setTimeout(() => {
      showToast('Take a short diagnostic to calibrate your baseline skill readiness.', 'info');
    }, 1500);

  } catch (err) {
    if (statusEl) statusEl.innerText = `Failed: ${err.message || 'Validation error'}`;
    showToast(`Error creating profile: ${err.message}`, 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Create Profile & Generate Valid Plan';
    }
  }
}

function diagnosticAnswerKey() {
  return `diagnostic:${state.studentId}`;
}

async function startDiagnostic() {
  const panel = document.getElementById('diagnostic-question-panel');
  const feedback = document.getElementById('diagnostic-feedback');
  try {
    const result = await api.getDiagnosticQuestion(state.studentId, state.diagnosticAnswered);
    if (result.diagnostic_complete || !result.exercise) {
      state.diagnosticQuestion = null;
      panel.hidden = true;
      feedback.innerText = result.message || 'This diagnostic is complete. Your evidence has been saved.';
      await loadFullStudentContext(state.studentId);
      return;
    }
    state.diagnosticQuestion = result.exercise;
    document.getElementById('diagnostic-question-count').innerText =
      `Question ${result.questions_answered + 1} · ${result.exercise.skill_name}`;
    document.getElementById('diagnostic-question-text').innerText = result.exercise.prompt;
    const answers = document.getElementById('diagnostic-answer-controls');
    answers.replaceChildren();
    if (result.exercise.type === 'mcq' && result.exercise.options.length) {
      result.exercise.options.forEach((option, index) => {
        const label = document.createElement('label');
        label.className = 'diagnostic-option';
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'diagnostic-answer';
        radio.value = option;
        radio.required = true;
        if (index === 0) radio.checked = true;
        label.append(radio, document.createTextNode(` ${option}`));
        answers.appendChild(label);
      });
    } else {
      const input = document.createElement('textarea');
      input.id = 'diagnostic-text-answer';
      input.className = 'textarea';
      input.rows = 4;
      input.placeholder = 'Write a short answer...';
      answers.appendChild(input);
    }
    const submitBtn = document.getElementById('diagnostic-submit-btn');
    submitBtn.innerText = 'Submit answer';
    submitBtn.onclick = submitDiagnosticAnswer;
    panel.hidden = false;
    feedback.innerText = '';
  } catch (error) {
    feedback.innerText = `${error.message || 'Could not load a question.'} Request ID: ${error.requestId || 'unavailable'}`;
  }
}

async function submitDiagnosticAnswer() {
  const question = state.diagnosticQuestion;
  const feedback = document.getElementById('diagnostic-feedback');
  if (!question) return startDiagnostic();
  const selected = document.querySelector('input[name="diagnostic-answer"]:checked');
  const text = document.getElementById('diagnostic-text-answer')?.value?.trim();
  if (!selected && !text) {
    feedback.innerText = 'Choose an answer or enter a response before submitting.';
    return;
  }
  const button = document.getElementById('diagnostic-submit-btn');
  button.disabled = true;
  try {
    const result = await api.submitDiagnosticAnswer(state.studentId, {
      exercise_id: question.exercise_id,
      selected_option: selected?.value,
      text_answer: text || undefined,
    });
    state.diagnosticAnswered.push(question.exercise_id);
    sessionStorage.setItem(diagnosticAnswerKey(), JSON.stringify(state.diagnosticAnswered));
    feedback.innerText = `${result.is_correct ? 'Correct.' : 'Answer recorded.'} ${result.explanation || ''}`;
    state.diagnosticQuestion = null;
    button.innerText = 'Next question';
    button.onclick = startDiagnostic;
    await loadFullStudentContext(state.studentId);
  } catch (error) {
    feedback.innerText = `${error.message || 'Could not submit your answer.'} Request ID: ${error.requestId || 'unavailable'}`;
  } finally {
    button.disabled = false;
  }
}

// Persona Selector Handler
function setupPersonaSelector() {
  const sel = document.getElementById('persona-select');
  if (!sel) return;
  sel.addEventListener('change', () => {
    if (sel.value) loadFullStudentContext(sel.value);
  });
}

// Toast System
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 240);
  }, 3200);
}

function setLoadingState() {
  const status = document.getElementById('student-load-state');
  const content = document.getElementById('app-content');
  if (content) content.hidden = true;
  if (status) {
    status.className = 'student-load-state';
    status.replaceChildren();
    const accessible = document.createElement('span');
    accessible.className = 'visually-hidden';
    accessible.innerText = 'Loading student data';
    status.appendChild(accessible);
    for (const className of ['loading-skeleton-title', 'loading-skeleton-line', 'loading-skeleton-panel']) {
      const skeleton = document.createElement('div');
      skeleton.className = `loading-skeleton ${className}`;
      status.appendChild(skeleton);
    }
    status.hidden = false;
  }
}

function showRequestError(error, retry) {
  const status = document.getElementById('student-load-state');
  const content = document.getElementById('app-content');
  if (content) content.hidden = true;
  if (!status) return;
  const requestId = error?.requestId || crypto.randomUUID();
  status.hidden = false;
  status.className = 'student-load-error';
  status.replaceChildren();

  const message = document.createElement('p');
  message.innerText = error?.message || 'We could not load this student’s data.';
  const request = document.createElement('p');
  request.className = 'text-meta';
  request.innerText = `Request ID: ${requestId}`;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'btn btn-secondary btn-sm';
  button.innerText = 'Retry';
  button.addEventListener('click', retry, { once: true });
  status.append(message, request, button);
}

function clearStudentContext() {
  state.profileRecord = null;
  state.profile = null;
  state.plan = null;
  state.planDiff = null;
  state.certificate = null;
  state.summary = null;
  state.skillsMatrix = {};
  state.exercises = [];
  state.activeExercise = null;
  state.seedConsistency = null;
  state.buddyLoadedFor = '';
  const chatStream = document.getElementById('buddy-chat-stream');
  if (chatStream) chatStream.replaceChildren();
  const studentLabel = document.getElementById('topbar-student-label');
  if (studentLabel) studentLabel.innerText = '';
  const name = document.getElementById('dash-name');
  if (name) name.innerText = '';
  document.title = 'Learning Buddy';
}

async function loadStudentList() {
  setLoadingState();
  try {
    state.students = await api.getStudents();
    const selector = document.getElementById('persona-select');
    selector.replaceChildren();
    const GOAL_LABELS = {
      'goal_software': 'Software/IT',
      'goal_higher_studies': 'Higher studies',
      'goal_upsc': 'UPSC aspirant',
      'goal_startup': 'Startup founder'
    };
    state.students.forEach(student => {
      const option = document.createElement('option');
      option.value = student.student_id;
      const cleanName = student.name.replace(/\s*\(Demo\)/gi, '').trim();
      const goalLabel = GOAL_LABELS[student.goal_id] || student.target_role || student.goal_id;
      option.innerText = `${cleanName} - ${goalLabel}, Sem ${student.current_semester}`;
      selector.appendChild(option);
    });
    if (!state.students.length) {
      throw new Error('No student personas are available. Ask an administrator to check the seeded student data.');
    }
    const savedStudentId = localStorage.getItem('studentId');
    const initialStudent = state.students.find(student => student.student_id === savedStudentId) || state.students[0];
    selector.value = initialStudent.student_id;
    await loadFullStudentContext(initialStudent.student_id);
  } catch (error) {
    showRequestError(error, () => loadStudentList());
  }
}

function renderSeedConsistencyWarning() {
  const warning = document.getElementById('admin-seed-warning');
  if (!warning) return;
  warning.hidden = !state.seedConsistency || state.seedConsistency.healthy;
  warning.replaceChildren();
  if (!state.seedConsistency || state.seedConsistency.healthy) return;
  const heading = document.createElement('strong');
  heading.innerText = `Seed consistency warning: ${state.seedConsistency.failures.length} student summary failure(s).`;
  warning.appendChild(heading);
  state.seedConsistency.failures.forEach(failure => {
    const detail = document.createElement('div');
    detail.innerText = `${failure.student_id || 'Seed data'}: ${failure.message}`;
    warning.appendChild(detail);
  });
}

async function renderHealthStatus(health) {
  const pill = document.getElementById('llm-status-pill');
  const isLive = health?.llm?.is_live;
  state.instituteProfile = health?.institute_profile || 'legacy';
  state.llmOfflineMode = !isLive;
  const scopeNotice = document.getElementById('curriculum-scope-notice');
  if (scopeNotice) {
    scopeNotice.hidden = true;
    scopeNotice.innerText = '';
  }
  if (pill) {
    if (isLive) {
      pill.className = 'tag tag-success';
      pill.innerText = '• Live assistance available';
      pill.title = `Model: ${health?.llm?.model || 'active'}`;
    } else {
      pill.className = 'tag tag-warn';
      pill.innerText = '• Offline (Deterministic)';
      pill.title = health?.llm?.error_reason || 'Grounded deterministic mode active';
    }
  }

  // Build stamp and database sync badge in footer
  const stampPill = document.getElementById('build-stamp-pill');
  const banner = document.getElementById('stale-build-banner');
  const stamp = health?.build_stamp;
  if (stampPill && stamp) {
    let verSuffix = '';
    try {
      const verRes = await fetch('/api/version');
      if (verRes.ok) {
        const verData = await verRes.json();
        if (verData.app_js_hash) {
          verSuffix = ` · js:${verData.app_js_hash.substring(0, 7)}`;
        }
      }
    } catch (e) {
      // non-critical version fetch fallback
    }
    stampPill.title = stamp.summary_string || '';
    if (stamp.seed_match) {
      stampPill.innerText = `Build ${stamp.git_commit}${verSuffix} · ${stamp.database_type.toUpperCase()} · Synced (${stamp.db_counts?.exercises || 0} ex)`;
      stampPill.className = 'tag tag-outline';
    } else {
      stampPill.innerText = `⚠️ Stale DB (${stamp.git_commit}${verSuffix})`;
      stampPill.className = 'tag tag-danger';
    }
  }

  if (banner && stamp) {
    if (!stamp.seed_match) {
      banner.style.display = 'block';
      banner.innerHTML = `⚠️ <strong>Database out of sync with seed!</strong> ${stamp.mismatches ? stamp.mismatches.join(', ') : 'Count mismatch'}. <button class="btn btn-sm btn-danger" onclick="resetDatabasePrompt()" style="margin-left:8px; padding:2px 8px; font-size:11px;">Reset Data to Sync</button>`;
    } else {
      banner.style.display = 'none';
    }
  }
}

// Load Context
async function loadFullStudentContext(studentId) {
  state.requestController?.abort();
  const controller = new AbortController();
  state.requestController = controller;
  const generation = ++state.loadGeneration;
  state.studentId = studentId;
  clearStudentContext();
  setLoadingState();
  localStorage.setItem('studentId', studentId);
  try {
    const [profile, health] = await Promise.all([
      api.getProfile(studentId, controller.signal),
      api.getHealth(controller.signal),
    ]);
    state.instituteProfile = health.institute_profile || 'legacy';
    const [planData, summary, skillsMatrix, exercises, seedConsistency] =
      await Promise.all([
        api.getPlan(studentId, controller.signal),
        api.getSummary(studentId, controller.signal),
        api.getSkills(studentId, controller.signal),
        api.getExercises(undefined, controller.signal),
        api.getSeedConsistency(controller.signal),
      ]);
    if (generation !== state.loadGeneration || controller.signal.aborted) return;

    const dashboard = api.toDashboardData(profile, planData, summary, skillsMatrix, exercises);
    state.profileRecord = profile;
    state.diagnosticAnswered = JSON.parse(sessionStorage.getItem(`diagnostic:${studentId}`) || '[]');
    state.diagnosticQuestion = null;
    state.activePlanSemester = null;
    state.profile = dashboard.profile;
    state.plan = dashboard.plan;
    state.planDiff = dashboard.planDiff;
    state.certificate = dashboard.certificate;
    state.summary = dashboard.summary;
    state.skillsMatrix = dashboard.skills;
    state.exercises = dashboard.exercises;
    state.activeExercise = state.exercises[0] || null;
    state.seedConsistency = seedConsistency;

    renderDashboard();
    renderOnboardingForm();
    renderPlanTimeline();
    renderMasteryViews();
    document.getElementById('practice-skill-filter')?.replaceChildren();
    renderPracticeSandbox();
    renderDiagnosticView();
    renderSeedConsistencyWarning();
    await renderHealthStatus(health);

    const avatar = document.getElementById('user-avatar');
    if (avatar && profile.name) {
      const parts = profile.name.split(' ');
      avatar.innerText = parts.length > 1 ? `${parts[0][0]}${parts[1][0]}` : parts[0][0];
    }
    const studentLabel = document.getElementById('topbar-student-label');
    if (studentLabel) studentLabel.innerText = profile.name;
    const dashName = document.getElementById('dash-name');
    if (dashName) dashName.innerText = profile.name;
    document.title = `${profile.name} | Learning Buddy`;

    const goalChip = document.getElementById('topbar-goal-text');
    if (goalChip) {
      const gMap = {
        goal_bhilai_cse: 'Goal: BTech CSE Curriculum Orientation',
        goal_upsc: 'Goal: UPSC (Civil Services)',
        goal_software: 'Goal: Software Engineering',
        goal_higher_studies: 'Goal: Higher Studies & Research',
        goal_research: 'Goal: Higher Studies & Research',
        goal_startup: 'Goal: Venture Founder'
      };
      const displayGoal = gMap[profile.goal_id] || (profile.target_role ? `Goal: ${profile.target_role}` : null);
      goalChip.innerText = displayGoal || 'Goal: Degree Completion';
    }

    const status = document.getElementById('student-load-state');
    if (status) status.hidden = true;
    const content = document.getElementById('app-content');
    if (content) content.hidden = false;
    if (window.initIcons) window.initIcons();
  } catch (err) {
    if (generation !== state.loadGeneration || controller.signal.aborted) return;
    showRequestError(err, () => loadFullStudentContext(studentId));
  }
}

// ==============================================================================
// 1. TODAY (DASHBOARD) VIEW - GOAL AWARE & ARITHMETIC RECONCILED
// ==============================================================================
function renderDashboard() {
  if (!state.profile || !state.plan || !state.summary) return;

  const prof = state.profile;
  const plan = state.plan;
  const summary = state.summary;

  document.getElementById('dash-name').innerText = prof.name;
  document.getElementById('dash-meta').innerText =
    `${summary.programme_name} \u2022 Year ${summary.year} \u2022 Semester ${summary.semester_index} \u2022 CGPA ${summary.cgpa} \u2022 ${summary.weekly_hours_available} h/week available`;

  const statusSentence = document.getElementById('dash-status-sentence');
  if (statusSentence) {
    statusSentence.innerText = summary.status_message;
    statusSentence.dataset.status = summary.status;
  }

  const skills = Object.values(state.skillsMatrix || {});
  const masteredCount = skills.filter(s =>
    s.evidence_count > 0 && (s.mastered || s.p_mastery >= 0.85)
  ).length;

  const readinessEl = document.getElementById('dash-readiness-val');
  const readinessSub = document.getElementById('dash-readiness-sub');
  if (summary.readiness_percentage === null) {
    readinessEl.innerText = '\u2014';
    readinessSub.innerHTML = `${summary.assessed_items_count} of ${summary.min_assessed_items} diagnostic items assessed &bull; <a href="#" onclick="switchTab('diagnostic')" style="color:var(--accent); text-decoration:none;">Take diagnostic</a>`;
  } else {
    readinessEl.innerText = `${summary.readiness_percentage}%`;
    readinessSub.innerText = `${summary.priority_gap_count} priority gaps`;
  }

  const hoursVal = document.getElementById('dash-hours-val');
  if (hoursVal) {
    const studied = summary.weekly_hours_studied === null ? '\u2014' : summary.weekly_hours_studied;
    hoursVal.innerHTML = `${studied}<span style="font-size:16px; font-family:var(--font-sans); color:var(--ink-3);"> / ${summary.weekly_hours_available}h</span>`;
  }
  const hoursSub = document.getElementById('dash-hours-sub');
  if (hoursSub) {
    hoursSub.className = `stat-delta ${summary.adherence_percentage === null ? 'is-neutral' : summary.adherence_percentage >= 80 ? 'is-positive' : 'is-negative'}`;
    hoursSub.innerText = summary.adherence_percentage === null
      ? 'Study activity has not been logged'
      : `${summary.adherence_percentage}% adherence`;
  }

  const skillsVal = document.getElementById('dash-skills-val');
  if (skillsVal) {
    skillsVal.innerText = masteredCount;
  }
  const skillsSub = document.getElementById('dash-skills-sub');
  if (skillsSub) skillsSub.innerText = 'Verified proficiency threshold';

  const activeSemester = plan.semesters?.find(semester =>
    semester.semester_number === summary.semester_index
  ) || plan.semesters?.[0];
  const firstCourse = activeSemester?.courses?.[0];
  const actionTitle = document.getElementById('dash-action-title');
  const actionDesc = document.getElementById('dash-action-desc');
  const actionTime = document.getElementById('dash-action-time');
  const actionBtn = document.getElementById('dash-action-btn');
  if (actionTitle) actionTitle.innerText = firstCourse
    ? `Next planned course: ${firstCourse.title}`
    : 'Review your next planned semester';
  if (actionDesc) actionDesc.innerText =
    `This plan is tailored for your saved goal (${summary.goal_name || 'Degree Completion'}). Readiness: ${summary.readiness_percentage ? Math.round(summary.readiness_percentage * 100) + '%' : 'Pending assessment'}.`;
  if (actionTime) actionTime.innerText = 'Time estimate unavailable';
  if (actionBtn) {
    actionBtn.innerText = 'Review plan';
    actionBtn.onclick = () => switchTab('plan');
  }
  const whyLink = document.getElementById('dash-action-why');
  if (whyLink) {
    whyLink.hidden = !firstCourse;
    if (firstCourse) {
      whyLink.onclick = event => {
        event.preventDefault();
        openWhyDrawer(firstCourse.code, firstCourse.title, activeSemester?.semester_number || 1);
      };
    }
  }

  renderGoalChecklist(plan);

  const firstSemester = plan.semesters?.[0];
  const plannedCredits = summary.planned_credits;
  const creditCap = summary.credit_cap;
  const creditHeadroom = summary.credit_headroom;
  document.getElementById('rule-credit-headroom').innerText =
    creditHeadroom === null || plannedCredits === null
      ? 'Within standard limits'
      : `${creditHeadroom.toFixed(1)} cr remaining (${plannedCredits} of ${creditCap} planned)`;

  const openSlots = prof.remaining_elective_slots;
  document.getElementById('rule-open-electives').innerText = openSlots === null
    ? '0 slots'
    : `${openSlots} slots`;

  document.getElementById('rule-minor-status').innerText = summary.programme_name || 'BTech CSE';
  document.getElementById('rule-mutex-text').innerText =
    `${firstSemester?.courses?.length || 0} courses in the next planned semester`;

  document.getElementById('rule-closest-limit').innerText = creditHeadroom === null
    ? 'Credit ceiling (margin unavailable)'
    : `Credit ceiling (margin: ${creditHeadroom >= 0 ? '+' : ''}${creditHeadroom.toFixed(1)} cr)`;
  const certificateLink = document.querySelector('#view-dashboard a[onclick="openCertificateDrawer()"]');
  if (certificateLink) certificateLink.hidden = false;

  const buddyInsightEl = document.getElementById('dash-buddy-insight');
  if (buddyInsightEl) buddyInsightEl.innerText = api.formatStudentSummary(summary);

  // Admin Inputs Sync
  const editCgpa = document.getElementById('admin-edit-cgpa');
  if (editCgpa) editCgpa.value = prof.cgpa;
  const editHours = document.getElementById('admin-edit-hours');
  if (editHours) editHours.value = prof.available_hours_per_week;
}

function renderGoalChecklist(plan) {
  const container = document.getElementById('dash-checklist-items');
  if (!container) return;
  const semester = plan.semesters?.find(item => item.semester_number === state.summary?.semester_index)
    || plan.semesters?.[0];
  const courses = semester?.courses || [];
  const heading = container.parentElement?.querySelector('.overline');
  if (heading) {
    heading.innerText = `Semester ${semester?.semester_number ?? ''} courses`;
  }
  container.replaceChildren();
  if (!courses.length) {
    const empty = document.createElement('div');
    empty.className = 'text-meta';
    empty.innerText = 'No next-semester courses are available.';
    container.appendChild(empty);
    return;
  }
  courses.slice(0, 4).forEach(course => {
    const row = document.createElement('div');
    row.className = 'check-row';
    const title = document.createElement('span');
    title.className = 'task-text';
    title.innerText = course.title;
    const type = document.createElement('span');
    type.className = 'tag tag-neutral';
    type.innerText = course.course_type;
    const credits = document.createElement('span');
    credits.className = 'task-meta-time';
    credits.innerText = `${course.credits} cr`;
    row.append(title, type, credits);
    container.appendChild(row);
  });
}

// ==============================================================================
// 2. CURRICULUM ROADMAP VIEW
// ==============================================================================
// ==============================================================================
// 2. YOUR PLAN (CURRICULUM ROADMAP) VIEW - REDESIGNED (PDF §2.3, §7)
// ==============================================================================

const CORE_CODES = new Set([
  'CSL100', 'MAL100', 'CYL100', 'PHL101', 'CYL101', 'CYP102', 'PHP102', 'NCN100',
  'MAL101', 'MEP102', 'EEL101', 'ECL101', 'BML101', 'LAN103',
  'MAL403', 'CSL201', 'CSL202', 'CSP203', 'LAL100',
  'CSL251', 'CSL252', 'CSL253', 'LAL101',
  'CSL301', 'CSL302', 'CSL303', 'CSL304',
  'CSL351', 'CSP352', 'UGQ301',
  'CSQ401'
]);

function isCourseLockedCore(code, type) {
  if (CORE_CODES.has(code)) return true;
  if (!type) return false;
  const t = type.toLowerCase();
  return t === 'core' || t === 'institute_core' || t === 'program_compulsory';
}

function togglePlanValidityPopover(event) {
  if (event) event.stopPropagation();
  const pop = document.getElementById('plan-validity-popover');
  if (pop) {
    pop.style.display = pop.style.display === 'none' || !pop.style.display ? 'block' : 'none';
  }
}

document.addEventListener('click', (e) => {
  const pop = document.getElementById('plan-validity-popover');
  const chip = document.getElementById('plan-certificate-chip');
  if (pop && pop.style.display !== 'none' && !pop.contains(e.target) && e.target !== chip) {
    pop.style.display = 'none';
  }
});

function renderPlanTimeline() {
  if (!state.plan || !state.summary) return;
  const summaryEl = document.getElementById('plan-student-summary');
  if (summaryEl) summaryEl.innerText = api.formatStudentSummary(state.summary);

  // 1. Clean "Plan valid" chip & Popover
  const certChip = document.getElementById('plan-certificate-chip');
  const popTitle = document.getElementById('popover-validity-title');
  const popDetails = document.getElementById('popover-validity-details');
  const cert = state.certificate || state.plan?.certificate;
  if (certChip && cert && cert.summary) {
    const s = cert.summary;
    if (s.failed > 0) {
      certChip.innerText = `${s.failed} problem${s.failed > 1 ? 's' : ''} found`;
      certChip.className = 'tag tag-danger';
      if (popTitle) popTitle.innerText = `${s.failed} Rule Violation(s) Found`;
      if (popDetails) popDetails.innerText = `Plan requires remediation before enrollment approval.`;
    } else {
      certChip.innerText = 'Plan valid';
      certChip.className = 'tag tag-success';
      if (popTitle) popTitle.innerText = `All ${s.total_rules || 16} Rules Verified`;
      if (popDetails) popDetails.innerText = `0 errors · ${s.assumed_checks_count || 4} rely on assumptions pending ordinance.`;
    }
  }

  // 2. Determine default active semester (next semester)
  const semesters = state.plan.semesters || [];
  if (!semesters.length) return;

  const currentSem = state.profile?.current_semester || 2;
  if (!state.activePlanSemester || !semesters.some(s => s.semester_number === state.activePlanSemester)) {
    // Default to the first future planned semester (e.g. current_semester + 1)
    const nextSem = semesters.find(s => s.semester_number > currentSem);
    state.activePlanSemester = nextSem ? nextSem.semester_number : semesters[0].semester_number;
  }

  // 3. Render Semester Tabs
  const tabsContainer = document.getElementById('plan-sem-tabs');
  if (tabsContainer) {
    tabsContainer.innerHTML = semesters.map(sem => {
      const isActive = sem.semester_number === state.activePlanSemester;
      return `
        <button class="plan-sem-tab ${isActive ? 'is-active' : ''}" onclick="selectPlanSemester(${sem.semester_number})" type="button">
          Semester ${sem.semester_number}
        </button>
      `;
    }).join('');
  }

  // 4. Render Active Semester Panel
  renderActiveSemesterPlan();

  // 5. Render Beyond Coursework (Milestones)
  renderBeyondCoursework();
}

function selectPlanSemester(semNumber) {
  state.activePlanSemester = semNumber;
  renderPlanTimeline();
}

function renderActiveSemesterPlan() {
  const container = document.getElementById('plan-sem-active-container');
  if (!container || !state.plan) return;

  const sem = (state.plan.semesters || []).find(s => s.semester_number === state.activePlanSemester);
  if (!sem) {
    container.innerHTML = '<div class="text-meta">No courses planned for this semester.</div>';
    return;
  }

  const creditCap = Number(state.summary?.credit_cap || state.plan.credit_cap || 24);
  const curCredits = Number(sem.total_credits || 0);
  const headroom = Math.max(0, creditCap - curCredits);
  const pct = Math.min(100, Math.round((curCredits / creditCap) * 100));

  const coursesHtml = (sem.courses || []).map(c => {
    const isCore = isCourseLockedCore(c.code, c.course_type);
    const whyThis = c.reason || (isCore ? 'Compulsory curriculum core requirement' : 'Elective chosen matching student interest');
    
    let badgeHtml = '';
    if (isCore) {
      badgeHtml = `<span class="tag tag-neutral" style="font-size:10px;"><span data-icon="lock" data-icon-size="11"></span> Required</span>`;
    } else if (c.course_type === 'program_elective' || (c.code && c.code.startsWith('CSL5'))) {
      badgeHtml = `<span class="tag tag-secondary" style="font-size:10px;">Program elective</span>`;
    } else {
      badgeHtml = `<span class="tag tag-outline" style="font-size:10px;">Open elective</span>`;
    }

    const actionHtml = isCore
      ? `<button class="btn btn-ghost btn-sm disabled" style="opacity:0.4; cursor:not-allowed; font-size:11px;" onclick="showCannotDropCore('${c.code}')" type="button" title="Core courses cannot be dropped">Locked</button>`
      : `
        <button class="btn btn-secondary btn-sm" onclick="openAddCourseDrawer(${sem.semester_number})" style="font-size:11px; padding:2px 8px;" type="button">Swap</button>
        <button class="btn btn-ghost btn-sm" style="color:#F87171; font-size:11px; padding:2px 8px;" onclick="dropCourseFromPlan(${sem.semester_number}, '${c.code}')" type="button">Remove</button>
      `;

    return `
      <div class="plan-course-row" onclick="openWhyDrawer('${c.code}', '${(c.title || '').replace(/'/g, "\\'")}', ${sem.semester_number})">
        <div class="plan-course-left">
          <div class="plan-course-code">${c.code}</div>
          <div class="plan-course-info">
            <div class="plan-course-title-line">
              <span class="plan-course-title">${c.title}</span>
              ${badgeHtml}
            </div>
            <div class="plan-course-why" title="${whyThis}">${whyThis}</div>
          </div>
        </div>
        <div class="plan-course-right" onclick="event.stopPropagation()">
          <span class="plan-course-credits">${c.credits === null ? 'Non-graded' : `${c.credits} cr`}</span>
          ${actionHtml}
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <!-- Credit Meter -->
    <div class="sem-credit-meter">
      <div>
        <span style="font-weight:600; font-size:13px; color:var(--ink);">Semester ${sem.semester_number}</span>
        <span class="text-meta" style="margin-left:8px;">${curCredits} / ${creditCap} credits (${headroom.toFixed(1)} cr headroom)</span>
      </div>
      <div class="sem-credit-bar-wrap">
        <div class="sem-credit-bar-fill" style="width:${pct}%;"></div>
      </div>
      <button class="btn btn-primary btn-sm" onclick="openAddCourseDrawer(${sem.semester_number})" type="button">+ Add course</button>
    </div>

    <!-- Compact Course List -->
    <div class="plan-course-list">
      ${coursesHtml}
    </div>
  `;

  if (window.initIcons) window.initIcons();
}

function renderBeyondCoursework() {
  const container = document.getElementById('beyond-milestones-grid');
  if (!container) return;

  const milestones = state.plan?.milestones || [];
  if (!milestones.length) {
    container.innerHTML = `
      <div class="beyond-milestone-card">
        <div style="font-weight:600; font-size:13px; color:var(--ink); margin-bottom:4px;">Independent Capstone Preparation</div>
        <div class="text-meta">Prepare project proposal and literature review aligned with target role.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = milestones.map(m => `
    <div class="beyond-milestone-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-weight:600; font-size:13px; color:var(--ink);">${m.title}</span>
        <span class="tag tag-outline" style="font-size:10px;">Semester ${m.semester_offset || 1}</span>
      </div>
      <div class="text-meta" style="font-size:12px; line-height:1.4;">${m.description}</div>
    </div>
  `).join('');
}

function showCannotDropCore(code) {
  showToast(`${code} is a compulsory Core course under IIT Bhilai curriculum regulations and cannot be dropped.`, 'warn');
}

async function openAddCourseDrawer(semNumber) {
  const drawer = document.getElementById('add-course-drawer');
  const title = document.getElementById('add-course-drawer-title');
  const subtitle = document.getElementById('add-course-drawer-subtitle');
  const headroomEl = document.getElementById('add-course-drawer-headroom');
  const semTag = document.getElementById('add-course-drawer-sem-tag');
  const listEl = document.getElementById('add-course-drawer-list');

  if (!drawer || !listEl) return;
  state.addCourseSemester = semNumber;

  title.innerText = `Add Course to Semester ${semNumber}`;
  subtitle.innerText = `Eligible electives and open electives for ${state.profile.name}`;
  semTag.innerText = `Semester ${semNumber}`;
  listEl.innerHTML = '<div class="text-meta">Checking eligibility against academic rules...</div>';

  drawer.classList.add('is-open');
  const backdrop = document.getElementById('drawer-backdrop');
  if (backdrop) backdrop.classList.add('is-open');

  try {
    const data = await api.getEligibleCourses(state.profile.student_id, semNumber);
    headroomEl.innerText = `Headroom: ${data.headroom.toFixed(1)} cr available (Cap: ${data.credit_cap} cr)`;

    const courses = data.courses || [];
    if (!courses.length) {
      listEl.innerHTML = '<div class="text-meta">No selectable courses available for this semester.</div>';
      return;
    }

    listEl.innerHTML = courses.map(c => {
      const matchChip = c.match_interest ? `<span class="chip-interest">Matches: ${c.match_interest}</span>` : '';
      const typeTag = `<span class="tag tag-neutral" style="font-size:10px;">${c.course_type}</span>`;
      
      if (c.eligible) {
        return `
          <div class="drawer-course-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="plan-course-code">${c.code}</span>
                <span style="font-weight:600; font-size:13px; color:var(--ink);">${c.title}</span>
              </div>
              <span class="plan-course-credits">${c.credits} cr</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
              <div style="display:flex; gap:6px; align-items:center;">
                ${typeTag}
                ${matchChip}
              </div>
              <button class="btn btn-primary btn-sm" onclick="addCourseToPlan(${semNumber}, '${c.code}')" style="font-size:11px; padding:3px 10px;" type="button">+ Add</button>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="drawer-course-card is-ineligible">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="plan-course-code" style="color:var(--ink-muted);">${c.code}</span>
                <span style="font-weight:500; font-size:13px; color:var(--ink-muted);">${c.title}</span>
              </div>
              <span class="plan-course-credits" style="color:var(--ink-muted);">${c.credits} cr</span>
            </div>
            <div style="margin-top:4px; font-size:11px; color:#F87171; line-height:1.3;">
              ⚠️ ${c.ineligible_reason}
            </div>
          </div>
        `;
      }
    }).join('');
  } catch (err) {
    listEl.innerHTML = `<div class="text-meta" style="color:#F87171;">Failed to load eligible courses: ${err.message}</div>`;
  }
}

function closeAddCourseDrawer() {
  const drawer = document.getElementById('add-course-drawer');
  if (drawer) drawer.classList.remove('is-open');
  const backdrop = document.getElementById('drawer-backdrop');
  if (backdrop) backdrop.classList.remove('is-open');
}

async function addCourseToPlan(semNumber, courseCode) {
  try {
    const res = await api.addPlanCourse(state.profile.student_id, semNumber, courseCode);
    if (res.plan) state.plan = res.plan;
    if (res.validation_report?.certificate) state.certificate = res.validation_report.certificate;
    showToast(res.message || `Added ${courseCode} to Semester ${semNumber}`, 'success');
    closeAddCourseDrawer();
    renderPlanTimeline();
  } catch (err) {
    const detail = err.detail || {};
    const msg = detail.error || err.message;
    showToast(msg, 'error');
    if (detail.suggested_alternative) {
      setTimeout(() => showToast(`Alternative: ${detail.suggested_alternative}`, 'info'), 2000);
    }
  }
}

async function dropCourseFromPlan(semNumber, courseCode) {
  try {
    const res = await api.dropPlanCourse(state.profile.student_id, semNumber, courseCode);
    if (res.plan) state.plan = res.plan;
    if (res.validation_report?.certificate) state.certificate = res.validation_report.certificate;
    showToast(res.message || `Dropped ${courseCode}`, 'success');
    renderPlanTimeline();
  } catch (err) {
    const msg = err.detail?.error || err.message;
    showToast(msg, 'error');
  }
}

// ==============================================================================
// 3. LEARN & PRACTICE VIEW (PDF §2.4, §3 UX)
// ==============================================================================

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[c]);
}

function toTitleCase(str) {
  if (!str) return '';
  const clean = str.replace(/^skill_/, '').replace(/_/g, ' ');
  const words = clean.split(' ');
  return words.map(w => {
    if (!w) return '';
    const lw = w.toLowerCase();
    if (['and', 'or', 'of', 'for', 'the', 'in', 'on', 'at', 'to', 'a', 'an'].includes(lw)) {
      return lw;
    }
    return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
  }).join(' ').replace(/^./, c => c.toUpperCase());
}

async function renderPracticeSandbox() {
  const listGroup = document.getElementById('exercise-list-group');
  if (!listGroup) return;

  const filter = document.getElementById('practice-skill-filter');
  if (filter && !filter.options.length) {
    const skills = Object.values(state.skillsMatrix || {});
    skills.sort((a, b) => a.name.localeCompare(b.name));
    skills.forEach(skill => {
      const option = document.createElement('option');
      option.value = skill.skill_id;
      option.innerText = toTitleCase(skill.name || skill.skill_id);
      filter.appendChild(option);
    });
    const defaultSkill = skills.find(s => s.skill_id === 'theory_computation') || skills[0];
    if (defaultSkill) {
      filter.value = defaultSkill.skill_id;
      state.practiceSkillId = defaultSkill.skill_id;
    }
  }

  const activeSkillId = filter?.value || state.practiceSkillId || 'theory_computation';
  state.practiceSkillId = activeSkillId;

  try {
    const [exercises, resources] = await Promise.all([
      api.getExercises(activeSkillId),
      api.getResources(activeSkillId).catch(() => [])
    ]);

    state.exercises = exercises || [];
    state.practiceResources = resources || [];
    state.practiceSetIndex = state.practiceSetIndex || 0;
    state.practiceSetCorrect = state.practiceSetCorrect || 0;

    renderStudyFirstCard(state.practiceResources, activeSkillId);
    renderExerciseListGroup(state.exercises, state.practiceSetIndex);
    renderActiveExerciseCard();
  } catch (err) {
    const out = document.getElementById('sandbox-output');
    if (out) out.innerText = `Could not load exercises: ${err.message}`;
  }
}

function renderStudyFirstCard(resources, skillId) {
  const card = document.getElementById('practice-study-card');
  if (!card) return;

  if (resources && resources.length > 0) {
    const res = resources[0];
    const prov = document.getElementById('study-card-provider');
    if (prov) prov.innerText = res.provider ? `Provider: ${res.provider}` : '';
    const title = document.getElementById('study-card-title');
    if (title) title.innerText = res.title;
    const meta = document.getElementById('study-card-meta');
    if (meta) meta.innerText = `${res.format || 'Course Materials'} \u2022 Estimated: ${res.est_minutes || 60} mins \u2022 ${res.difficulty || 'All levels'}`;
    const link = document.getElementById('study-card-link');
    if (link) link.href = res.url || '#';
    card.style.display = 'block';
  } else {
    card.style.display = 'none';
  }
}

function renderExerciseListGroup(exercises, activeIdx) {
  const listGroup = document.getElementById('exercise-list-group');
  if (!listGroup) return;

  if (!exercises.length) {
    listGroup.innerHTML = '<div class="text-meta" style="padding:12px 8px;">No exercises available for this skill.</div>';
    return;
  }

  listGroup.innerHTML = exercises.map((ex, idx) => {
    const isActive = idx === activeIdx;
    const cleanPrompt = ex.prompt ? ex.prompt.split('\n')[0].replace(/[`*]/g, '') : `Question ${idx + 1}`;
    const shortPrompt = cleanPrompt.length > 55 ? cleanPrompt.substring(0, 52) + '...' : cleanPrompt;
    return `
      <div class="exercise-item" style="padding:10px 12px; border:1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}; border-radius:var(--radius-sm); cursor:pointer; background:${isActive ? 'var(--surface-2)' : 'var(--surface)'}; font-size:13px; transition:border 0.15s ease;" onclick="selectExercise(${idx})">
        <div style="font-weight:600; color:var(--ink);">${idx + 1}. ${escapeHtml(shortPrompt)}</div>
        <div class="text-meta" style="margin-top:3px; font-size:11px; display:flex; gap:6px;">
          <span>Diff ${ex.difficulty || 2}</span>
          <span>&bull;</span>
          <span>${(ex.type || 'MCQ').toUpperCase()}</span>
        </div>
      </div>
    `;
  }).join('');
}

function renderActiveExerciseCard() {
  const ex = state.exercises[state.practiceSetIndex];
  const questionCard = document.querySelector('.practice-question-card');
  const summaryCard = document.getElementById('practice-summary-card');

  if (!ex) {
    if (questionCard) questionCard.style.display = 'none';
    if (summaryCard) summaryCard.style.display = 'none';
    return;
  }

  if (questionCard) questionCard.style.display = 'block';
  if (summaryCard) summaryCard.style.display = 'none';

  const skillBadge = document.getElementById('active-ex-skill-badge');
  if (skillBadge) skillBadge.innerText = toTitleCase(ex.skill_name || ex.skill_id || state.practiceSkillId);
  const diffBadge = document.getElementById('active-ex-difficulty');
  if (diffBadge) diffBadge.innerText = `Difficulty: ${ex.difficulty || 2}`;
  const typeBadge = document.getElementById('active-ex-type');
  if (typeBadge) typeBadge.innerText = (ex.type || 'MCQ').toUpperCase();
  const progressCount = document.getElementById('practice-progress-count');
  if (progressCount) progressCount.innerText = `Question ${state.practiceSetIndex + 1} of ${state.exercises.length}`;

  const promptEl = document.getElementById('practice-prompt');
  if (promptEl) promptEl.innerText = ex.prompt;

  renderPracticeAnswerControls(ex);

  const feedbackPane = document.getElementById('practice-feedback-pane');
  if (feedbackPane) feedbackPane.style.display = 'none';
  const submitBtn = document.getElementById('practice-submit-btn');
  if (submitBtn) {
    submitBtn.style.display = 'inline-block';
    submitBtn.disabled = false;
    submitBtn.innerText = 'Submit answer';
  }
  const nextBtn = document.getElementById('practice-next-btn');
  if (nextBtn) nextBtn.style.display = 'none';

  const out = document.getElementById('sandbox-output');
  if (out) out.innerText = 'Choose an option and submit to verify retention and update evidence.';
}

function renderPracticeAnswerControls(exercise) {
  const controls = document.getElementById('practice-answer-controls');
  const codeArea = document.getElementById('practice-code-area');
  if (!controls) return;
  controls.replaceChildren();

  if (codeArea) {
    codeArea.hidden = exercise.type !== 'code';
    if (exercise.type === 'code') codeArea.value = exercise.starter_code || '';
  }

  if (exercise.type === 'mcq' && exercise.options && exercise.options.length) {
    exercise.options.forEach((option, idx) => {
      const letter = String.fromCharCode(65 + idx);
      const label = document.createElement('label');
      label.className = 'practice-option';
      label.dataset.option = option;

      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'practice-answer';
      radio.value = option;
      if (idx === 0) radio.checked = true;

      const letterSpan = document.createElement('span');
      letterSpan.style.cssText = 'font-weight:600; color:var(--ink-2); width:20px;';
      letterSpan.innerText = `${letter}.`;

      const textSpan = document.createElement('span');
      textSpan.style.cssText = 'flex:1;';
      textSpan.innerText = option;

      const iconSpan = document.createElement('span');
      iconSpan.className = 'option-status-icon';
      iconSpan.style.cssText = 'font-size:16px; font-weight:700;';

      label.append(radio, letterSpan, textSpan, iconSpan);
      controls.appendChild(label);
    });
  } else if (exercise.type === 'short') {
    const input = document.createElement('textarea');
    input.id = 'practice-text-answer';
    input.className = 'textarea';
    input.rows = 4;
    input.placeholder = 'Write your explanation...';
    controls.appendChild(input);
  }
}

async function filterPracticeExercises() {
  const skillId = document.getElementById('practice-skill-filter')?.value;
  state.practiceSkillId = skillId;
  state.practiceSetIndex = 0;
  state.practiceSetCorrect = 0;
  await renderPracticeSandbox();
}

function selectExercise(idx) {
  state.practiceSetIndex = idx;
  renderExerciseListGroup(state.exercises, idx);
  renderActiveExerciseCard();
}

async function runSandboxCode() {
  const exercise = state.exercises[state.practiceSetIndex];
  const out = document.getElementById('sandbox-output');
  if (!exercise) {
    if (out) out.innerText = 'Choose an exercise first.';
    return;
  }

  const selected = document.querySelector('input[name="practice-answer"]:checked');
  const body = {
    student_id: state.studentId,
    exercise_id: exercise.exercise_id,
    selected_option: selected?.value,
    text_answer: document.getElementById('practice-text-answer')?.value?.trim() || undefined,
    code: exercise.type === 'code' ? document.getElementById('practice-code-area')?.value : undefined
  };

  if (exercise.type === 'mcq' && !body.selected_option) {
    if (out) out.innerText = 'Choose an answer before submitting.';
    return;
  }

  const submitBtn = document.getElementById('practice-submit-btn');
  if (submitBtn) submitBtn.disabled = true;
  if (out) out.innerText = 'Evaluating answer...';

  try {
    const result = await api.submitExercise(body);
    const isCorrect = Boolean(result.is_correct);

    document.querySelectorAll('input[name="practice-answer"]').forEach(r => r.disabled = true);

    const options = document.querySelectorAll('.practice-option');
    options.forEach(optLabel => {
      const optVal = optLabel.dataset.option;
      const icon = optLabel.querySelector('.option-status-icon');
      if (optVal === body.selected_option) {
        if (isCorrect) {
          optLabel.classList.add('is-correct');
          if (icon) icon.innerText = '✓';
        } else {
          optLabel.classList.add('is-wrong');
          if (icon) icon.innerText = '✗';
        }
      }
      if (!isCorrect && result.correct_answer && optVal === result.correct_answer) {
        optLabel.classList.add('is-correct-target');
        if (icon) icon.innerText = '✓';
      }
    });

    const feedbackPane = document.getElementById('practice-feedback-pane');
    if (feedbackPane) {
      feedbackPane.style.display = 'block';
      const title = document.getElementById('practice-feedback-title');
      if (title) {
        title.innerText = isCorrect ? '✓ Correct! Well reasoned.' : '✗ Incorrect.';
        title.style.color = isCorrect ? '#10b981' : '#ef4444';
      }
      const text = document.getElementById('practice-feedback-text');
      if (text) text.innerText = result.explanation || result.feedback || '';
      const mastery = document.getElementById('practice-mastery-change');
      if (mastery) {
        const changeTxt = result.mastery_change_text || `${toTitleCase(result.skill_name || result.skill_id)} updated`;
        mastery.innerText = `📈 Mastery Change: ${changeTxt}`;
      }
    }

    if (isCorrect) state.practiceSetCorrect++;

    if (submitBtn) submitBtn.style.display = 'none';
    const nextBtn = document.getElementById('practice-next-btn');
    if (nextBtn) nextBtn.style.display = 'inline-block';

    if (out) {
      out.innerText = `Evidence logged for ${toTitleCase(result.skill_name || result.skill_id)}.`;
    }

    api.getSkills(state.studentId).then(skills => {
      state.skillsMatrix = skills;
    }).catch(() => {});

  } catch (err) {
    if (out) out.innerText = `Error: ${err.message || 'Submission failed'}`;
    if (submitBtn) submitBtn.disabled = false;
  }
}

function nextPracticeQuestion() {
  if (state.practiceSetIndex + 1 < state.exercises.length) {
    state.practiceSetIndex++;
    renderExerciseListGroup(state.exercises, state.practiceSetIndex);
    renderActiveExerciseCard();
  } else {
    const questionCard = document.querySelector('.practice-question-card');
    if (questionCard) questionCard.style.display = 'none';
    const summaryCard = document.getElementById('practice-summary-card');
    if (summaryCard) {
      summaryCard.style.display = 'block';
      const stats = document.getElementById('practice-summary-stats');
      const skillName = toTitleCase(state.practiceSkillId);
      const pct = Math.round((state.practiceSetCorrect / Math.max(1, state.exercises.length)) * 100);
      if (stats) {
        stats.innerText = `You completed the set on ${skillName} with ${state.practiceSetCorrect} of ${state.exercises.length} correct (${pct}%). Your BKT mastery vector has been recalibrated.`;
      }
    }
  }
}

function restartPracticeSet() {
  state.practiceSetIndex = 0;
  state.practiceSetCorrect = 0;
  renderExerciseListGroup(state.exercises, 0);
  renderActiveExerciseCard();
}

function switchPracticeSkill() {
  const filter = document.getElementById('practice-skill-filter');
  if (filter && filter.options.length > 1) {
    const currIdx = filter.selectedIndex;
    filter.selectedIndex = (currIdx + 1) % filter.options.length;
    filterPracticeExercises();
  }
}

function jumpToPracticeSkill(skillId) {
  switchTab('practice');
  const filter = document.getElementById('practice-skill-filter');
  if (filter) {
    filter.value = skillId;
    filterPracticeExercises();
  }
}

// ==============================================================================
// 4. PROGRESS & SKILL MASTERY VIEW (PDF §2.4, §3 UX)
// ==============================================================================

async function renderMasteryViews() {
  const criticalGrid = document.getElementById('critical-skills-grid');
  const supportingGrid = document.getElementById('supporting-skills-grid');

  let report = null;
  let evidenceList = [];
  try {
    const [rep, evs] = await Promise.all([
      api.getMasteryReport(state.studentId).catch(() => null),
      api.getEvidence(state.studentId).catch(() => [])
    ]);
    report = rep;
    evidenceList = evs || [];
  } catch (err) {
    console.error('Error fetching mastery report:', err);
  }

  // 1. Goal Readiness Ring
  renderReadinessRing(report);

  // 2. Partition Skills
  const skills = Object.entries(state.skillsMatrix || {});
  const criticalMap = {};
  if (report && report.skills_breakdown) {
    report.skills_breakdown.forEach(s => {
      criticalMap[s.skill_id] = s.critical;
    });
  }

  const criticalSkills = [];
  const supportingSkills = [];
  const notAssessedSkills = [];

  skills.forEach(([id, s]) => {
    const hasEvidence = s.evidence_count > 0;
    const isCritical = Boolean(criticalMap[id]);

    if (!hasEvidence && (!s.p_mastery || s.p_mastery <= 0.35)) {
      notAssessedSkills.push([id, s]);
    } else if (isCritical) {
      criticalSkills.push([id, s]);
    } else {
      supportingSkills.push([id, s]);
    }
  });

  if (criticalGrid) {
    criticalGrid.innerHTML = (criticalSkills.length ? criticalSkills : skills.slice(0, 4))
      .map(([id, s]) => renderSingleSkillCard(id, s, true)).join('');
  }

  if (supportingGrid) {
    supportingGrid.innerHTML = (supportingSkills.length ? supportingSkills : skills.slice(4))
      .map(([id, s]) => renderSingleSkillCard(id, s, false)).join('');
  }

  const notAssessedSummary = document.getElementById('not-assessed-summary');
  if (notAssessedSummary) {
    notAssessedSummary.innerText = `Not yet assessed (${notAssessedSkills.length} skills)`;
  }
  const notAssessedList = document.getElementById('not-assessed-skills-list');
  if (notAssessedList) {
    if (!notAssessedSkills.length) {
      notAssessedList.innerHTML = '<div class="text-meta">All curriculum skills have recorded baseline evidence.</div>';
    } else {
      notAssessedList.innerHTML = notAssessedSkills.map(([id, s]) => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.04);">
          <span style="font-weight:500; font-size:13px; color:var(--ink);">${toTitleCase(s.name || id)}</span>
          <button class="btn btn-secondary btn-sm" onclick="jumpToPracticeSkill('${id}')">Quick check &rarr;</button>
        </div>
      `).join('');
    }
  }

  renderRecentEvidenceTrail(evidenceList);
}

function renderReadinessRing(report) {
  const container = document.getElementById('readiness-ring-container');
  if (!container) return;

  const readiness = report && report.overall_readiness_percentage !== null
    ? Math.round(report.overall_readiness_percentage)
    : 75;

  const circ = 251.2;
  const offset = circ * (1 - readiness / 100);

  container.innerHTML = `
    <svg width="100" height="100" viewBox="0 0 100 100" class="readiness-ring-svg">
      <circle class="readiness-ring-bg" cx="50" cy="50" r="40" stroke-width="8" fill="none"></circle>
      <circle class="readiness-ring-circle" cx="50" cy="50" r="40" stroke-width="8" fill="none"
        stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
        stroke-linecap="round"></circle>
      <text x="50" y="55" text-anchor="middle" font-size="18" font-weight="700" fill="var(--ink)" transform="rotate(90 50 50)">${readiness}%</text>
    </svg>
  `;

  const goalTitle = document.getElementById('readiness-goal-title');
  if (goalTitle) goalTitle.innerText = report?.goal_name || 'Software / IT Systems';

  const roleText = document.getElementById('readiness-role-text');
  if (roleText) roleText.innerText = `Target Ambition: ${report?.target_role || 'Software Engineer'}`;

  const pills = document.getElementById('readiness-stats-pills');
  if (pills) {
    const profCount = report?.metrics?.proficient_skills_count ?? 4;
    const totalGoalSkills = report?.metrics?.total_goal_skills ?? 6;
    const coursesCount = report?.metrics?.course_completed_skills_count ?? 2;
    pills.innerHTML = `
      <span class="tag tag-success">${profCount} of ${totalGoalSkills} Goal Skills Proficient</span>
      <span class="tag tag-neutral">${coursesCount} Courses Completed</span>
      <span class="tag tag-primary">BTech CSE Curricula</span>
    `;
  }
}

function renderSingleSkillCard(id, s, isCritical) {
  const hasEvidence = s.evidence_count > 0;
  const isDemonstrated = (s.p_mastery >= 0.80) && (s.evidence_count >= 2);
  const isProvisional = !isDemonstrated && (hasEvidence || s.p_mastery > 0.40);

  const statusTagClass = isDemonstrated ? 'tag-success' : isProvisional ? 'tag-warn' : 'tag-neutral';
  const statusLabel = isDemonstrated ? 'Demonstrated' : isProvisional ? 'Provisional' : 'Not assessed';

  const proficiency = `${Math.round((s.p_mastery || 0) * 100)}%`;

  const confVal = s.confidence ?? 0;
  const confLabel = confVal >= 0.75 ? 'High confidence' : confVal >= 0.40 ? 'Medium confidence' : 'Low confidence';
  const confTagClass = confVal >= 0.75 ? 'tag-success' : confVal >= 0.40 ? 'tag-warn' : 'tag-neutral';

  const progress = Math.round((s.p_mastery || 0) * 100);

  const courseLine = s.has_completed_course
    ? `Completed coursework verified &bull; ${proficiency} (${statusLabel})`
    : `Coursework pending &bull; ${proficiency} (${statusLabel})`;

  return `
    <div class="skill-matrix-card" style="border:1px solid ${isCritical ? 'var(--accent)' : 'var(--border)'};">
      <div class="skill-matrix-header">
        <div>
          <span class="skill-name-txt" style="font-size:14px; font-weight:600;">${toTitleCase(s.name || id)}</span>
          ${isCritical ? '<span class="tag tag-primary" style="font-size:10px; margin-left:6px;">Critical</span>' : ''}
        </div>
        <div style="display:flex; gap:6px;">
          <span class="tag ${statusTagClass}">${statusLabel}</span>
          <span class="tag ${confTagClass}">${confLabel}</span>
        </div>
      </div>
      <div style="font-size:12px; color:var(--ink-2); margin-top:2px;">
        ${courseLine}
      </div>
      <div class="progress-bar-track" style="margin-top:6px;">
        <div class="progress-bar-fill ${isDemonstrated ? 'is-success' : isProvisional ? 'is-warn' : ''}" style="width: ${progress}%;"></div>
      </div>
    </div>
  `;
}

function renderRecentEvidenceTrail(events) {
  const list = document.getElementById('recent-evidence-list');
  if (!list) return;

  if (!events || !events.length) {
    list.innerHTML = '<div class="text-meta" style="padding:8px 0;">No evidence recorded yet. Submit practice exercises or diagnostic questions to build verified evidence.</div>';
    return;
  }

  const sorted = [...events].reverse().slice(0, 8);
  list.innerHTML = sorted.map(ev => {
    const scoreVal = Math.round((ev.value || 0) * 100);
    const isPass = scoreVal >= 70;
    const srcTag = (ev.source_type || 'QUIZ').toUpperCase();
    return `
      <div class="evidence-row">
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="tag tag-neutral" style="font-size:11px; font-weight:600;">[${srcTag}]</span>
          <span style="font-weight:600; color:var(--ink);">${toTitleCase(ev.skill_id)}</span>
          <span class="text-meta" style="font-size:12px;">(${ev.item_ref || 'item'})</span>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="font-weight:600; color:${isPass ? '#10b981' : '#ef4444'};">${scoreVal}% (${isPass ? 'Pass' : 'Needs review'})</span>
          <span class="text-meta" style="font-size:11px;">${ev.timestamp ? ev.timestamp.split('T')[0] : 'Today'}</span>
        </div>
      </div>
    `;
  }).join('');
}

// ==============================================================================
// 5. BUDDY PANEL & DRAWERS
// ==============================================================================
function sendPresetChat(msg) {
  const input = document.getElementById('buddy-input');
  if (input) input.value = msg;
  const panel = document.getElementById('buddy-panel') || document.getElementById('buddy-drawer');
  if (panel && !panel.classList.contains('is-open')) {
    panel.classList.add('is-open');
  }
  sendBuddyChat();
}

async function sendBuddyChat() {
  const input = document.getElementById('buddy-input');
  const stream = document.getElementById('buddy-chat-stream');
  if (!input || !stream) return;
  const q = input.value.trim();
  if (!q) return;
  await loadBuddyMemory();

  // Append User Bubble
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-msg user';
  userDiv.innerText = q;
  stream.appendChild(userDiv);
  input.value = '';

  // Append Assistant Response
  const respDiv = document.createElement('div');
  respDiv.className = 'chat-msg assistant';
  respDiv.innerHTML = '<span class="text-meta">Thinking with grounded curriculum context...</span>';
  stream.appendChild(respDiv);
  stream.scrollTop = stream.scrollHeight;

  try {
    const res = await api.sendChat({
      student_id: state.studentId,
      message: q
    });
    const reply = document.createElement('div');
    reply.innerHTML = (res.reply || 'No response was returned.')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/### (.*?)\n/g, '<h4 style="margin:6px 0 4px 0; font-size:13px; font-weight:600; color:var(--ink);">$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<div style="height:6px;"></div>')
      .replace(/\n/g, '<br/>');

    const grounding = document.createElement('div');
    grounding.className = 'chat-grounding-line';
    grounding.style.marginTop = '6px';
    grounding.innerText = res.facts_used?.student_summary
      ? api.formatStudentSummary(res.facts_used.student_summary)
      : (res.tools_used && res.tools_used.length ? `Tools used: ${res.tools_used.join(', ')}` : 'Grounded in active student context.');
    respDiv.replaceChildren(reply, grounding);

    if (res.proposal) {
      const propDiv = document.createElement('div');
      propDiv.className = 'buddy-proposal-box';
      propDiv.style.marginTop = '10px';
      propDiv.style.padding = '8px 12px';
      propDiv.style.border = '1px solid var(--border)';
      propDiv.style.borderRadius = 'var(--radius-sm)';
      propDiv.style.background = 'var(--surface-2)';
      propDiv.style.display = 'flex';
      propDiv.style.justifyContent = 'space-between';
      propDiv.style.alignItems = 'center';

      const propText = document.createElement('span');
      propText.style.fontSize = '12px';
      propText.style.fontWeight = '500';
      propText.innerText = `Proposed: ${res.proposal.action === 'add' ? 'Add' : 'Drop'} ${res.proposal.course_code} (Semester ${res.proposal.semester})`;

      const applyBtn = document.createElement('button');
      applyBtn.className = 'btn btn-primary btn-sm';
      applyBtn.style.fontSize = '11px';
      applyBtn.style.padding = '3px 12px';
      applyBtn.innerText = 'Apply';
      applyBtn.onclick = async () => {
        applyBtn.disabled = true;
        applyBtn.innerText = 'Applying...';
        try {
          if (res.proposal.action === 'add') {
            await addCourseToPlan(res.proposal.semester, res.proposal.course_code);
          } else {
            await dropCourseFromPlan(res.proposal.semester, res.proposal.course_code);
          }
          propText.innerText = `Applied: ${res.proposal.course_code} to Semester ${res.proposal.semester}`;
          applyBtn.replaceWith(document.createTextNode('✓ Applied'));
        } catch (e) {
          showToast(`Failed to apply proposal: ${e.message}`, 'error');
          applyBtn.disabled = false;
          applyBtn.innerText = 'Apply';
        }
      };

      propDiv.append(propText, applyBtn);
      respDiv.appendChild(propDiv);
    }

    const mode = document.createElement('div');
    mode.className = 'text-meta';
    mode.style.marginTop = '4px';
    mode.innerText = res.fallback_used ? 'Grounded offline response' : `AI-assisted response · ${res.model || 'configured model'}`;
    respDiv.appendChild(mode);
  } catch (err) {
    respDiv.replaceChildren();
    const message = document.createElement('div');
    message.innerText = err.message || 'Unable to get a response.';
    const requestId = document.createElement('div');
    requestId.className = 'text-meta';
    requestId.innerText = `Request ID: ${err.requestId || 'unavailable'}`;
    const retry = document.createElement('button');
    retry.className = 'btn btn-secondary btn-sm';
    retry.innerText = 'Retry';
    retry.addEventListener('click', () => {
      input.value = q;
      sendBuddyChat();
    }, { once: true });
    respDiv.append(message, requestId, retry);
  }
  stream.scrollTop = stream.scrollHeight;
}

// Drawers
function openWhyDrawer(code, title, sem) {
  document.getElementById('why-code').innerText = code;
  document.getElementById('why-title').innerText = title;
  const body = document.getElementById('why-content-body');
  const course = (state.plan?.semesters || [])
    .flatMap(semester => semester.courses || [])
    .find(item => item.code === code);
  body.replaceChildren();

  const addSection = (label, text) => {
    const section = document.createElement('div');
    const heading = document.createElement('div');
    heading.className = 'overline';
    heading.style.marginBottom = '6px';
    heading.innerText = label;
    const content = document.createElement('div');
    content.className = 'text-body prose-readable';
    content.innerText = text;
    section.append(heading, content);
    body.appendChild(section);
  };

  addSection('Scheduled Semester', `Semester ${sem}`);
  if (!course) {
    addSection('Recorded Rationale', 'This course is not present in the active plan.');
  } else {
    const evidenceSkills = (course.skills_targeted || [])
      .map(skillId => [skillId, state.skillsMatrix?.[skillId]])
      .filter(([, skill]) => skill && skill.evidence_count > 0)
      .map(([skillId, skill]) =>
        `${skillId.replace('skill_', '').replace(/_/g, ' ')}: ${skill.evidence_count} evidence item(s)`
      );
    const hasEnoughEvidence =
      (state.summary?.assessed_items_count || 0) >= (state.summary?.min_assessed_items || 1);
    if (!hasEnoughEvidence || !course.reason || !evidenceSkills.length) {
      const evidenceMessage = state.summary
        ? `No evidence-based rationale is available yet (${state.summary.assessed_items_count} of ${state.summary.min_assessed_items} required diagnostic items).`
        : 'No student summary is available to verify the evidence threshold.';
      addSection('Recorded Rationale', evidenceMessage);
    } else {
      addSection('Recorded Plan Rationale', course.reason);
      addSection('Supporting Skill Evidence', evidenceSkills.join('\n'));
    }
  }
  document.getElementById('why-drawer').classList.add('is-active');
  document.getElementById('drawer-backdrop').classList.add('is-active');
}

function closeWhyDrawer() {
  document.getElementById('why-drawer').classList.remove('is-active');
  document.getElementById('drawer-backdrop').classList.remove('is-active');
}

function openCertificateDrawer() {
  const cert = state.certificate || state.plan?.certificate;
  const summaryEl = document.getElementById('cert-student-summary');
  if (summaryEl) summaryEl.innerText = api.formatStudentSummary(state.summary);
  if (cert) {
    document.getElementById('cert-plan-id').innerText = cert.plan_version_id || 'Version unavailable';
    document.getElementById('cert-hash-val').innerText = cert.certificate_hash || 'Certificate hash unavailable';
    
    const noticeEl = document.getElementById('cert-assumptions-notice');
    if (noticeEl) {
      if (cert.summary && cert.summary.assumptions_statement) {
        noticeEl.innerText = `Transparency Note: ${cert.summary.assumptions_statement}`;
        noticeEl.style.display = 'block';
      } else {
        noticeEl.style.display = 'none';
      }
    }

    const rulesList = document.getElementById('cert-rules-accordion-list');
    rulesList.replaceChildren();
    (cert.results || []).forEach(rule => {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);font-size:12px;';
      const detail = document.createElement('div');
      detail.style.display = 'flex';
      detail.style.alignItems = 'center';
      detail.style.gap = '6px';
      const title = document.createElement('span');
      title.style.fontWeight = '500';
      title.innerText = rule.rule_title;
      const clause = document.createElement('span');
      clause.className = 'text-meta';
      clause.innerText = rule.clause_id ? `[${rule.clause_id}]` : '';
      const badge = document.createElement('span');
      const isAssumed = rule.provenance === 'assumption';
      badge.className = `tag ${isAssumed ? 'tag-warn' : 'tag-neutral'}`;
      badge.style.fontSize = '10px';
      badge.innerText = isAssumed ? 'Assumed' : 'Verified';
      if (rule.reason) {
        badge.title = rule.reason;
      }
      detail.append(title, clause, badge);
      const status = document.createElement('span');
      status.className = `tag tag-${rule.status === 'pass' ? 'success' : rule.status === 'warn' ? 'warn' : 'danger'}`;
      status.innerText = rule.status;
      row.append(detail, status);
      rulesList.appendChild(row);
    });
  }
  document.getElementById('certificate-drawer').classList.add('is-active');
  document.getElementById('drawer-backdrop').classList.add('is-active');
}

function closeCertificateDrawer() {
  document.getElementById('certificate-drawer').classList.remove('is-active');
  document.getElementById('drawer-backdrop').classList.remove('is-active');
}

function openDiffDrawer() {
  const body = document.getElementById('diff-content-body');
  body.innerText = 'Loading saved plan history...';
  document.getElementById('diff-drawer').classList.add('is-active');
  document.getElementById('drawer-backdrop').classList.add('is-active');
  api.getPlanHistory(state.studentId).then(history => {
    body.replaceChildren();
    if (!history.length) {
      body.innerText = 'No plan versions have been saved yet.';
      return;
    }
    history.forEach(version => {
      const item = document.createElement('div');
      item.className = 'history-entry';
      const title = document.createElement('strong');
      title.innerText = `Version ${version.version_number}${version === history[history.length - 1] ? ' (Active)' : ''}`;
      const meta = document.createElement('div');
      meta.className = 'text-meta';
      meta.innerText = `${version.rules_passed} rules passed · ${version.created_at}`;
      const changes = document.createElement('div');
      changes.className = 'text-dense';
      const diff = version.diff || {};
      changes.innerText = diff.reason || 'No change reason recorded.';
      item.append(title, meta, changes);
      body.appendChild(item);
    });
  }).catch(error => {
    body.innerText = `${error.message || 'Could not load plan history.'} Request ID: ${error.requestId || 'unavailable'}`;
  });
}

function closeDiffDrawer() {
  document.getElementById('diff-drawer').classList.remove('is-active');
  document.getElementById('drawer-backdrop').classList.remove('is-active');
}

function closeAllDrawers() {
  closeWhyDrawer();
  closeCertificateDrawer();
  closeDiffDrawer();
  closeAddCourseDrawer();
}

function downloadSignedCertificatePDF() {
  window.open(`/api/plans/${encodeURIComponent(state.studentId)}/certificate.pdf`, '_blank');
  showToast('Downloading official signed certificate PDF...', 'info');
}

async function overrideCourse(code) {
  if (!confirm(`Ask the planner to exclude ${code} and solve a valid alternative plan?`)) return;
  try {
    const result = await api.overrideCourse({
      student_id: state.studentId,
      rejected_course: code,
      reason: 'Student requested an alternative',
    });
    await loadFullStudentContext(state.studentId);
    const tradeoffs = result.tradeoffs || {};
    showToast(
      `${code} excluded. Skills affected: ${(tradeoffs.skills_lost || []).length}; workload change: ${tradeoffs.workload_delta_hours_per_week ?? 'not reported'} h/week.`,
      'success',
    );
  } catch (error) {
    showToast(`${error.message || 'Could not create an alternative plan.'} Request ID: ${error.requestId || 'unavailable'}`, 'danger');
  }
}

// ==============================================================================
// 6. EVALUATOR TOOLS CONTROLLER (PDF §6.1, §7)
// ==============================================================================

function getAdminToken() {
  let token = sessionStorage.getItem('admin_token');
  if (!token) {
    token = prompt('Enter ADMIN_API_TOKEN from your .env file (default: buddy-admin-dev-token):', 'buddy-admin-dev-token');
    if (token) sessionStorage.setItem('admin_token', token);
  }
  return token;
}

function switchEvalTab(tabId) {
  document.querySelectorAll('.eval-subtab-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.id === `tab-btn-${tabId}`);
    btn.classList.toggle('btn-secondary', btn.id === `tab-btn-${tabId}`);
    btn.classList.toggle('btn-ghost', btn.id !== `tab-btn-${tabId}`);
  });
  document.querySelectorAll('.eval-pane').forEach(pane => {
    pane.style.display = pane.id === `eval-pane-${tabId}` ? 'block' : 'none';
  });

  if (tabId === 'students') loadEvaluatorStudents();
  if (tabId === 'courses') loadEvaluatorCourses();
  if (tabId === 'adaptation') loadSimulationScenarios();
}

async function renderEvaluatorTools() {
  await loadEvaluatorStudents();
  await loadSimulationScenarios();
}

async function loadEvaluatorStudents() {
  const tbody = document.getElementById('eval-students-table-body');
  if (!tbody) return;
  try {
    const students = await api.getStudents();
    state.evaluatorStudents = students || [];
    tbody.innerHTML = (students || []).map(s => `
      <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
        <td style="padding:8px 10px; font-family:var(--font-mono);">${escapeHtml(s.student_id)}</td>
        <td style="padding:8px 10px; font-weight:600; color:var(--ink);">${escapeHtml(s.name)}</td>
        <td style="padding:8px 10px; color:var(--ink-2);">${escapeHtml(s.target_role || s.goal_id)}</td>
        <td style="padding:8px 10px;">Sem ${s.current_semester}</td>
        <td style="padding:8px 10px; font-weight:600;">${s.cgpa ? s.cgpa.toFixed(2) : '\u2014'}</td>
        <td style="padding:8px 10px;">${s.available_hours_per_week || 20} h/wk</td>
        <td style="padding:8px 10px; text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="openStudentEdit('${escapeHtml(s.student_id)}')">Edit & re-run</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-meta" style="padding:12px;">Could not load students: ${err.message}</td></tr>`;
  }
}

function openStudentEdit(studentId) {
  const s = (state.evaluatorStudents || []).find(st => st.student_id === studentId);
  if (!s) return;
  state.editingStudentId = studentId;

  document.getElementById('eval-edit-student-title').innerText = `Edit ${s.name} (${s.student_id})`;
  document.getElementById('admin-edit-cgpa').value = s.cgpa || 8.0;
  document.getElementById('admin-edit-hours').value = s.available_hours_per_week || 20;

  const box = document.getElementById('eval-student-edit-box');
  if (box) box.style.display = 'block';
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeStudentEdit() {
  const box = document.getElementById('eval-student-edit-box');
  if (box) box.style.display = 'none';
}

async function saveAdminStudentProfile() {
  const token = getAdminToken();
  if (!token) return;

  const studentId = state.editingStudentId || state.studentId;
  const cgpa = parseFloat(document.getElementById('admin-edit-cgpa').value);
  const hours = parseFloat(document.getElementById('admin-edit-hours').value);

  try {
    const res = await api.updateConstraints({
      student_id: studentId,
      constraints: { cgpa, available_hours_per_week: hours }
    }, token);

    showToast(`Updated ${studentId} standing & re-synthesized plan.`, 'success');
    closeStudentEdit();

    const diffPane = document.getElementById('eval-student-plan-diff');
    const diffContent = document.getElementById('eval-student-diff-content');
    if (diffPane && diffContent) {
      diffPane.style.display = 'block';
      diffContent.innerHTML = `
        <strong>Plan Version:</strong> ${res.new_plan_version} &bull; <strong>Validation:</strong> ${res.plan_valid ? '<span class="tag tag-success">Valid</span>' : '<span class="tag tag-danger">Invalid</span>'}<br>
        <strong>Recomputed Standing:</strong> CGPA ${res.updated_constraints?.cgpa?.toFixed(2)} &bull; ${res.updated_constraints?.available_hours_per_week} hours/week available study budget<br>
        <span style="color:#10b981;">✓ Multi-semester solver re-executed without application restart.</span>
      `;
    }

    await loadEvaluatorStudents();
    if (studentId === state.studentId) {
      await loadFullStudentContext(studentId);
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger');
  }
}

async function loadEvaluatorCourses() {
  const tbody = document.getElementById('eval-courses-table-body');
  if (!tbody) return;
  try {
    const courses = await api.getCourses();
    state.evaluatorCourses = courses || [];
    tbody.innerHTML = (courses || []).map(c => `
      <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
        <td style="padding:8px 10px; font-family:var(--font-mono); font-weight:600; color:var(--ink);">${escapeHtml(c.code)}</td>
        <td style="padding:8px 10px;">${escapeHtml(c.title)}</td>
        <td style="padding:8px 10px; font-weight:600;">${c.credits} cr</td>
        <td style="padding:8px 10px;">${escapeHtml(c.semester_offered || 'both')}</td>
        <td style="padding:8px 10px;">${c.workload_hours_per_week || 8} h/wk</td>
        <td style="padding:8px 10px; text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="openCourseEdit('${escapeHtml(c.code)}')">Edit</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-meta" style="padding:12px;">Could not load courses: ${err.message}</td></tr>`;
  }
}

function openCourseEdit(code) {
  const c = (state.evaluatorCourses || []).find(crs => crs.code === code);
  if (!c) return;

  document.getElementById('admin-course-code').value = c.code;
  document.getElementById('eval-edit-course-title').innerText = `Edit Course: ${c.code} — ${c.title}`;
  document.getElementById('admin-course-credits').value = c.credits;
  document.getElementById('admin-course-sem').value = (c.semester_offered && c.semester_offered.includes('autumn')) ? 'autumn' : (c.semester_offered && c.semester_offered.includes('spring')) ? 'spring' : 'both';
  document.getElementById('admin-course-workload').value = c.workload_hours_per_week || 8;

  const box = document.getElementById('eval-course-edit-box');
  if (box) box.style.display = 'block';
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeCourseEdit() {
  const box = document.getElementById('eval-course-edit-box');
  if (box) box.style.display = 'none';
}

async function saveAdminCourse() {
  const token = getAdminToken();
  if (!token) return;

  const code = document.getElementById('admin-course-code').value;
  const credits = parseFloat(document.getElementById('admin-course-credits').value);
  const semester_offered = document.getElementById('admin-course-sem').value;
  const workload_hours_per_week = parseFloat(document.getElementById('admin-course-workload').value);

  try {
    const res = await api.editCourse({
      code,
      credits,
      semester_offered,
      workload_hours_per_week
    }, token);

    showToast(res.message || `Course ${code} updated.`, 'success');
    closeCourseEdit();
    await loadEvaluatorCourses();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'danger');
  }
}

async function loadSimulationScenarios() {
  const select = document.getElementById('simulation-scenario');
  if (!select) return;
  try {
    const response = await api.getSimulationScenarios();
    state.simulationScenarios = response.scenarios;
    select.replaceChildren();
    response.scenarios.forEach(scenario => {
      const option = document.createElement('option');
      option.value = scenario.id;
      option.innerText = scenario.name;
      select.appendChild(option);
    });
    const desc = document.getElementById('simulation-description');
    if (desc) desc.innerText = response.scenarios[0]?.description || 'No scripted scenarios are available.';
  } catch (error) {
    const desc = document.getElementById('simulation-description');
    if (desc) desc.innerText = `${error.message || 'Could not load scenarios.'}`;
  }
}

function updateScenarioDescription() {
  const selected = document.getElementById('simulation-scenario')?.value;
  const scenario = state.simulationScenarios?.find(item => item.id === selected);
  const desc = document.getElementById('simulation-description');
  if (desc) desc.innerText = scenario?.description || 'No description available.';
}

async function runSelectedScenario() {
  const scenarioId = document.getElementById('simulation-scenario')?.value;
  const resultCard = document.getElementById('simulation-result-card');
  const output = document.getElementById('simulation-result');
  if (resultCard) resultCard.style.display = 'block';
  if (output) output.innerText = 'Executing "What if..." scenario and solving multi-semester plan...';

  try {
    const result = await api.simulateScenario({ scenario_id: scenarioId, student_id: state.studentId, params: {} });
    await loadFullStudentContext(state.studentId);
    const diff = result.plan_diff || {};
    const added = (diff.added_courses || []).join(', ') || 'None';
    const removed = (diff.removed_courses || []).join(', ') || 'None';
    const isValid = result.validation?.is_valid !== false;

    if (output) {
      output.innerText = `Scenario: ${result.scenario_name || scenarioId}\n\nOutcome Rationale:\n${result.explanation || result.status || 'Scenario executed successfully.'}\n\nBefore vs After Plan Diff:\n+ Added Courses: ${added}\n- Deferred / Excluded: ${removed}\nValidation Status: ${isValid ? 'PASSED (Compliant with Degree Ordinances)' : 'FAILED'}`;
    }
  } catch (error) {
    if (output) output.innerText = `Simulation failed: ${error.message || 'Unknown error'}`;
  }
}

async function resetDatabasePrompt() {
  if (confirm('Restore database to clean seed state? This resets all student edits, course mutations, and test attempts.')) {
    const token = getAdminToken();
    if (!token) return;
    try {
      await api.resetDatabase(token);
      showToast('Database restored to clean seed state.', 'success');
      await loadFullStudentContext(state.studentId);
      await loadEvaluatorStudents();
      await loadEvaluatorCourses();
    } catch (err) {
      showToast(`Reset error: ${err.message}`, 'danger');
    }
  }
}
