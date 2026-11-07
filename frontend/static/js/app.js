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
      const intro = document.createElement('div');
      intro.className = 'chat-msg assistant';
      intro.innerText = memory.memory_summary?.summary
        ? `I remember your learning context: ${memory.memory_summary.summary}`
        : 'Hello! I can help review your plan, recorded skills, and current status.';
      stream.appendChild(intro);
      (memory.recent_history || []).forEach(turn => {
        const message = document.createElement('div');
        message.className = `chat-msg ${turn.role === 'user' ? 'user' : 'assistant'}`;
        message.innerText = turn.content;
        stream.appendChild(message);
      });
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
    admin: 'Administrative Console',
    setup: 'Set up profile'
  };
  const topTitle = document.getElementById('topbar-section-title');
  if (topTitle) topTitle.innerText = titles[target] || 'Today';

  if (target === 'plan') renderPlanTimeline();
  if (target === 'mastery') renderMasteryViews();
  if (target === 'practice') renderPracticeSandbox();
  if (target === 'diagnostic') renderDiagnosticView();
  if (target === 'setup') renderOnboardingForm();
  if (target === 'admin') loadSimulationScenarios();
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

function renderOnboardingForm() {
  const profile = state.profileRecord;
  if (!profile) return;
  const goalSelect = document.getElementById('setup-goal');
  goalSelect.replaceChildren(
    new Option('Software Engineering & Systems', 'goal_software'),
    new Option('Higher Studies & Research', 'goal_higher_studies'),
    new Option('UPSC Civil Services', 'goal_upsc'),
    new Option('Startup & Entrepreneurship', 'goal_startup')
  );
  document.getElementById('setup-scope-description').innerText =
    'Update your learning profile and target goal. Your degree plan will be generated and verified against academic rules.';
  document.getElementById('setup-save-btn').innerText = 'Save & regenerate plan';
  document.getElementById('setup-name').value = profile.name || '';
  goalSelect.value = profile.goal_id || 'goal_software';
  document.getElementById('setup-hours').value = profile.available_hours_per_week ?? 8;
  document.getElementById('setup-cgpa').value = profile.cgpa ?? 8;
  document.getElementById('setup-interests').value = (profile.interests || []).join(', ');
  document.getElementById('admin-edit-cgpa').value = profile.cgpa ?? '';
  document.getElementById('admin-edit-hours').value = profile.available_hours_per_week ?? '';
}

async function saveOnboarding() {
  if (!state.profileRecord) return;
  const goalTargets = {
    goal_software: 'Software engineer',
    goal_higher_studies: 'Computing researcher',
    goal_research: 'Computing researcher',
    goal_upsc: 'Civil servant',
    goal_startup: 'Technical founder',
  };
  const name = document.getElementById('setup-name').value.trim();
  const cgpa = Number(document.getElementById('setup-cgpa').value);
  const hours = Number(document.getElementById('setup-hours').value);
  const status = document.getElementById('setup-status');
  if (!name || !Number.isFinite(cgpa) || cgpa < 0 || cgpa > 10
      || !Number.isFinite(hours) || hours < 0 || hours > 80) {
    status.innerText = 'Enter a name, CGPA from 0 to 10, and weekly study hours from 0 to 80.';
    return;
  }
  const goalId = document.getElementById('setup-goal').value;
  const profile = {
    ...state.profileRecord,
    name,
    goal_id: goalId,
    target_role: goalTargets[goalId] || state.profileRecord.target_role,
    available_hours_per_week: hours,
    cgpa,
    interests: document.getElementById('setup-interests').value.split(',').map(value => value.trim()).filter(Boolean),
  };
  const button = document.getElementById('setup-save-btn');
  button.disabled = true;
  status.innerText = 'Saving your profile and generating a validated plan...';
  try {
    await api.saveProfile(profile);
    await api.generatePlan(profile.student_id);
    status.innerText = 'Your preferences are saved and the plan has been revalidated.';
    await loadFullStudentContext(profile.student_id);
  } catch (error) {
    status.innerText = `${error.message || 'Could not save your profile.'} Request ID: ${error.requestId || 'unavailable'}`;
  } finally {
    button.disabled = false;
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
    document.getElementById('diagnostic-submit-btn').innerText = 'Submit answer';
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
    state.students.forEach(student => {
      const option = document.createElement('option');
      option.value = student.student_id;
      option.innerText = `${student.name} (${student.programme} · ${student.target_role || student.goal_id})`;
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

function renderHealthStatus(health) {
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
    pill.className = isLive ? 'tag tag-success' : 'tag tag-neutral';
    pill.innerText = isLive ? '• Live assistance available' : '• Offline (Deterministic)';
  }

  // Build stamp and database sync badge
  const stampPill = document.getElementById('build-stamp-pill');
  const banner = document.getElementById('stale-build-banner');
  const stamp = health?.build_stamp;
  if (stampPill && stamp) {
    stampPill.title = stamp.summary_string || '';
    if (stamp.seed_match) {
      stampPill.innerText = `Build ${stamp.git_commit} · ${stamp.database_type.toUpperCase()} · Synced (${stamp.db_counts?.exercises || 0} ex)`;
      stampPill.className = 'tag tag-outline';
    } else {
      stampPill.innerText = `⚠️ Stale DB (${stamp.git_commit})`;
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
    renderHealthStatus(health);

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
function renderPlanTimeline() {
  if (!state.plan || !state.summary) return;
  const summaryEl = document.getElementById('plan-student-summary');
  if (summaryEl) summaryEl.innerText = api.formatStudentSummary(state.summary);
  const container = document.getElementById('plan-timeline-grid');
  if (!container) return;

  const certChip = document.getElementById('plan-certificate-chip');
  if (certChip) {
    const cert = state.certificate || state.plan?.certificate;
    if (cert && cert.summary) {
      const s = cert.summary;
      if (s.failed > 0) {
        certChip.innerText = `${s.failed} problem${s.failed > 1 ? 's' : ''} found`;
        certChip.className = 'tag tag-danger';
      } else if (s.assumed_checks_count > 0) {
        certChip.innerText = `All ${s.total_rules} checks passed (${s.assumed_checks_count} rely on assumptions pending ordinance)`;
        certChip.className = 'tag tag-secondary';
      } else {
        certChip.innerText = `All ${s.total_rules} checks passed · verified`;
        certChip.className = 'tag tag-success';
      }
      certChip.onclick = () => openCertificateDrawer();
    }
  }

  const historyButton = document.querySelector('#view-plan button[onclick="openDiffDrawer()"]');
  if (historyButton) historyButton.hidden = false;

  container.innerHTML = '';
  state.plan.semesters.forEach(sem => {
    const col = document.createElement('div');
    col.className = 'sem-column';

    const coursesHtml = sem.courses.map(c => `
      <div class="course-tile" onclick="openWhyDrawer('${c.code}', '${c.title.replace(/'/g, "\\'")}', ${sem.semester_number})">
        <div class="course-tile-top">
          <span class="course-code-txt">${c.code}</span>
          <span class="course-credits-txt">${c.credits === null ? 'Non-graded' : `${c.credits} cr`}</span>
        </div>
        <div class="course-title-txt">${c.title}</div>
        <div class="skill-chips-row">
          <span class="tag tag-neutral" style="font-size:10px; padding:1px 5px;">${c.course_type}</span>
          ${(c.skills_targeted || []).map(sk => `<span class="skill-chip">${sk.replace('skill_', '')}</span>`).join('')}
        </div>
        <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); overrideCourse('${c.code}')" type="button">Suggest alternative</button>
      </div>
    `).join('');

    col.innerHTML = `
      <div class="sem-head">
        <div class="sem-name">Semester ${sem.semester_number}</div>
        <div class="sem-stats">${sem.total_credits} / ${state.summary?.credit_cap || 24} cr</div>
      </div>
      <div style="display:flex; flex-direction:column; gap:8px;">
        ${coursesHtml}
      </div>
    `;
    container.appendChild(col);
  });
}

// ==============================================================================
// 3. LEARN & PRACTICE VIEW
// ==============================================================================
function renderPracticeSandbox() {
  const listGroup = document.getElementById('exercise-list-group');
  if (!listGroup) return;
  const filter = document.getElementById('practice-skill-filter');
  if (filter && !filter.options.length) {
    const all = document.createElement('option');
    all.value = '';
    all.innerText = 'All skills';
    filter.appendChild(all);
    Object.values(state.skillsMatrix || {}).forEach(skill => {
      const option = document.createElement('option');
      option.value = skill.skill_id;
      option.innerText = skill.name;
      filter.appendChild(option);
    });
  }

  listGroup.innerHTML = (state.exercises || []).map((ex, idx) => {
    const itemTitle = ex.title || ex.prompt?.split('\n')[0] || `Exercise ${idx + 1}`;
    const isActive = state.activeExercise && state.activeExercise.exercise_id === ex.exercise_id;
    return `
    <div class="exercise-item" style="padding:8px 12px; border:1px solid var(--border); border-radius:var(--radius-sm); cursor:pointer; background:${isActive ? 'var(--surface-2)' : 'var(--surface)'}; font-size:13px;" onclick="selectExercise(${idx})">
      <div style="font-weight:500; color:var(--ink);">${itemTitle}</div>
      <div class="text-meta" style="margin-top:2px;">Difficulty: ${ex.difficulty} &bull; ${ex.type.toUpperCase()}</div>
    </div>
  `;
  }).join('');

  if (!state.exercises || !state.exercises.length) {
    listGroup.innerHTML = '<div class="text-meta">No exercises available for this filter.</div>';
    document.getElementById('active-ex-title').innerText = 'No exercises available';
    document.getElementById('practice-prompt').innerText =
      'Select a different skill filter to view practice exercises.';
    document.getElementById('practice-answer-controls').replaceChildren();
    const codeArea = document.getElementById('practice-code-area');
    codeArea.value = '';
    codeArea.hidden = true;
    document.getElementById('practice-submit-btn').disabled = true;
    document.getElementById('sandbox-output').innerText = 'No exercise is available to submit.';
    return;
  }

  if (!state.activeExercise && state.exercises.length > 0) {
    state.activeExercise = state.exercises[0];
  }

  if (state.activeExercise) {
    document.getElementById('practice-submit-btn').disabled = false;
    document.getElementById('active-ex-title').innerText = state.activeExercise.title;
    document.getElementById('practice-prompt').innerText = state.activeExercise.prompt;
    document.getElementById('practice-code-area').value = state.activeExercise.starter_code || '';
    renderPracticeAnswerControls(state.activeExercise);
  }
}

async function filterPracticeExercises() {
  const skillId = document.getElementById('practice-skill-filter').value;
  try {
    state.exercises = await api.getExercises(skillId || undefined);
    state.activeExercise = state.exercises[0] || null;
    renderPracticeSandbox();
  } catch (error) {
    document.getElementById('sandbox-output').innerText =
      `${error.message || 'Could not load exercises.'} Request ID: ${error.requestId || 'unavailable'}`;
  }
}

function selectExercise(idx) {
  state.activeExercise = state.exercises[idx];
  if (state.activeExercise) {
    document.getElementById('active-ex-title').innerText = state.activeExercise.title;
    document.getElementById('practice-prompt').innerText = state.activeExercise.prompt;
    document.getElementById('practice-code-area').value = state.activeExercise.starter_code || '';
    document.getElementById('sandbox-output').innerText = 'Submit your answer to receive feedback and update your evidence.';
    renderPracticeAnswerControls(state.activeExercise);
  }
}

function renderPracticeAnswerControls(exercise) {
  const controls = document.getElementById('practice-answer-controls');
  const codeArea = document.getElementById('practice-code-area');
  controls.replaceChildren();
  codeArea.hidden = exercise.type !== 'code';
  document.getElementById('practice-submit-btn').innerText =
    exercise.type === 'code' ? 'Run & test' : 'Submit answer';
  if (exercise.type === 'mcq') {
    exercise.options.forEach((option, index) => {
      const label = document.createElement('label');
      label.className = 'diagnostic-option';
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'practice-answer';
      radio.value = option;
      if (index === 0) radio.checked = true;
      label.append(radio, document.createTextNode(` ${option}`));
      controls.appendChild(label);
    });
  } else if (exercise.type === 'short') {
    const input = document.createElement('textarea');
    input.id = 'practice-text-answer';
    input.className = 'textarea';
    input.rows = 4;
    input.placeholder = 'Write your explanation...';
    controls.appendChild(input);
  } else if (exercise.type === 'project' || exercise.type === 'case') {
    const url = document.createElement('input');
    url.id = 'practice-repo-url';
    url.className = 'input';
    url.placeholder = 'Repository URL (optional)';
    const summary = document.createElement('textarea');
    summary.id = 'practice-project-summary';
    summary.className = 'textarea';
    summary.rows = 4;
    summary.placeholder = 'Describe what you built and how it works...';
    controls.append(url, summary);
  }
}

async function runSandboxCode() {
  const exercise = state.activeExercise;
  const out = document.getElementById('sandbox-output');
  if (!exercise) {
    out.innerText = 'Choose an exercise first.';
    return;
  }
  const selected = document.querySelector('input[name="practice-answer"]:checked');
  const body = {
    student_id: state.studentId,
    exercise_id: exercise.exercise_id,
    selected_option: selected?.value,
    text_answer: document.getElementById('practice-text-answer')?.value?.trim() || undefined,
    code: exercise.type === 'code' ? document.getElementById('practice-code-area').value : undefined,
    repo_url: document.getElementById('practice-repo-url')?.value?.trim() || undefined,
    summary: document.getElementById('practice-project-summary')?.value?.trim() || undefined,
  };
  if (exercise.type === 'mcq' && !body.selected_option) {
    out.innerText = 'Choose an answer before submitting.';
    return;
  }
  if (exercise.type === 'short' && !body.text_answer) {
    out.innerText = 'Write an answer before submitting.';
    return;
  }
  out.innerText = 'Evaluating your submission...';
  const button = document.getElementById('practice-submit-btn');
  button.disabled = true;
  try {
    const result = await api.submitExercise(body);
    await loadFullStudentContext(state.studentId);
    const score = Math.round(Number(result.score || 0) * 100);
    out.innerText = `${result.feedback || 'Submission recorded.'} Score: ${score}%. Evidence has been added to ${result.skill_name || exercise.skill_id}.`;
  } catch (error) {
    out.innerText = `${error.message || 'Could not evaluate this exercise.'} Request ID: ${error.requestId || 'unavailable'}`;
  } finally {
    button.disabled = false;
  }
}

// ==============================================================================
// 4. SKILLS MASTERY VIEW
// ==============================================================================
function renderMasteryViews() {
  const container = document.getElementById('skills-matrix-grid');
  if (!container) return;

  const skills = Object.entries(state.skillsMatrix || {});
  if (!skills.length) {
    container.innerHTML =
      '<p class="text-meta">No skills assessed yet. Complete diagnostic questions or exercises to build mastery evidence.</p>';
    return;
  }
  container.innerHTML = skills.map(([id, s]) => {
    const hasEvidence = s.evidence_count > 0;
    const isMastered = hasEvidence && (s.mastered || (s.p_mastery >= 0.85));
    const proficiency = hasEvidence ? `${(s.p_mastery * 100).toFixed(0)}%` : 'Not assessed';
    const confidence = hasEvidence ? (s.confidence ?? 0).toFixed(2) : '\u2014';
    const progress = hasEvidence ? (s.p_mastery * 100).toFixed(0) : '0';
    return `
      <div class="skill-matrix-card">
        <div class="skill-matrix-header">
          <span class="skill-name-txt">${id.replace('skill_', '').replace(/_/g, ' ')}</span>
          <span class="tag ${isMastered ? 'tag-success' : 'tag-neutral'}">
            ${isMastered ? 'Demonstrated' : hasEvidence ? 'In progress' : 'Not assessed'}
          </span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--ink-3);">
          <span>Proficiency: ${proficiency}</span>
          <span>Confidence: ${confidence}</span>
        </div>
        <div class="progress-bar-track">
          <div class="progress-bar-fill ${isMastered ? 'is-success' : ''}" style="width: ${progress}%;"></div>
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
    reply.innerText = res.reply || 'No response was returned.';
    const grounding = document.createElement('div');
    grounding.className = 'chat-grounding-line';
    grounding.style.marginTop = '4px';
    grounding.innerText = res.facts_used?.student_summary
      ? api.formatStudentSummary(res.facts_used.student_summary)
      : 'Student summary is unavailable for this response.';
    respDiv.replaceChildren(reply, grounding);
    const mode = document.createElement('div');
    mode.className = 'text-meta';
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

async function saveAdminStudentProfile() {
  const token = prompt('Enter the ADMIN_API_TOKEN configured for this service. It is not saved in the browser.');
  if (!token) return;
  try {
    const cgpa = parseFloat(document.getElementById('admin-edit-cgpa').value);
    const hours = parseFloat(document.getElementById('admin-edit-hours').value);
    await api.updateConstraints({
      student_id: state.studentId,
      constraints: { cgpa, available_hours_per_week: hours }
    }, token);
    showToast('Student constraints updated & plan recomputed.', 'success');
    await loadFullStudentContext(state.studentId);
  } catch (err) {
    showToast(`Error: ${err.message} Request ID: ${err.requestId || 'unavailable'}`, 'danger');
  }
}

async function resetDatabasePrompt() {
  if (confirm('Restore database to clean seed state?')) {
    const token = prompt('Enter the ADMIN_API_TOKEN configured for this service. It is not saved in the browser.');
    if (!token) return;
    try {
      await api.resetDatabase(token);
      showToast('Database reset to clean state.', 'success');
      await loadFullStudentContext(state.studentId);
    } catch (err) {
      showToast(`Reset error: ${err.message} Request ID: ${err.requestId || 'unavailable'}`, 'danger');
    }
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
    document.getElementById('simulation-description').innerText =
      response.scenarios[0]?.description || 'No scripted scenarios are available.';
  } catch (error) {
    document.getElementById('simulation-description').innerText =
      `${error.message || 'Could not load scenarios.'} Request ID: ${error.requestId || 'unavailable'}`;
  }
}

function updateScenarioDescription() {
  const selected = document.getElementById('simulation-scenario').value;
  const scenario = state.simulationScenarios.find(item => item.id === selected);
  document.getElementById('simulation-description').innerText =
    scenario?.description || 'No description available.';
}

async function runSelectedScenario() {
  const scenarioId = document.getElementById('simulation-scenario').value;
  const output = document.getElementById('simulation-result');
  output.innerText = 'Running scenario and validating the resulting plan...';
  try {
    const result = await api.simulateScenario({ scenario_id: scenarioId, student_id: state.studentId, params: {} });
    await loadFullStudentContext(state.studentId);
    const diff = result.plan_diff || {};
    output.innerText = `${result.explanation || result.status || 'Scenario complete.'}\n\nAdded: ${(diff.added_courses || []).join(', ') || 'none'}\nRemoved/deferred: ${(diff.removed_courses || []).join(', ') || 'none'}\nValidation: ${result.validation?.is_valid === false ? 'failed' : 'passed'}`;
  } catch (error) {
    output.innerText = `${error.message || 'Scenario failed.'} Request ID: ${error.requestId || 'unavailable'}`;
  }
}
