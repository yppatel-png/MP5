(() => {
  const api = window.LearningBuddyApi;
  if (!api) {
    console.error('New student onboarding could not start: the typed API client is unavailable.');
    return;
  }

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);

  const state = {
    catalog: null,
    programme: null,
    profile: null,
    selectedCourses: new Set(),
    history: [],
    saving: false,
  };

  function showError(element, error) {
    const requestId = error?.requestId ? ` Request ID: ${error.requestId}` : '';
    element.textContent = `${error?.message || 'Something went wrong. Please try again.'}${requestId}`;
    element.classList.add('is-error');
  }

  function clearStatus(element) {
    element.textContent = '';
    element.classList.remove('is-error');
  }

  function getProgramme(programmeId) {
    return state.catalog.programmes.find(programme => programme.id === programmeId);
  }

  function currentPayload() {
    const form = document.getElementById('bhilai-profile-form');
    const formData = new FormData(form);
    return {
      name: String(formData.get('name') || '').trim(),
      programme_id: String(formData.get('programme_id') || ''),
      current_semester: Number(formData.get('current_semester')),
      cgpa: Number(formData.get('cgpa')),
      available_hours_per_week: Number(formData.get('available_hours_per_week')),
      goal: String(formData.get('goal') || '').trim(),
      interests: String(formData.get('interests') || '')
        .split(',')
        .map(value => value.trim())
        .filter(Boolean)
        .slice(0, 12),
      completed_course_codes: String(formData.get('completed_course_codes') || '')
        .split(',')
        .map(value => value.trim().toUpperCase())
        .filter(Boolean),
      shortlisted_course_codes: [...state.selectedCourses],
    };
  }

  function renderProgrammeOptions() {
    const selector = document.getElementById('bhilai-programme');
    const choices = state.catalog.programmes.map(programme => {
      const disabled = programme.status !== 'curriculum_available';
      const label = disabled
        ? `${programme.name} — curriculum not included in source`
        : programme.name;
      return `<option value="${escapeHtml(programme.id)}" ${disabled ? 'disabled' : ''}>${escapeHtml(label)}</option>`;
    });
    selector.innerHTML = choices.join('');
    state.programme = getProgramme(selector.value);
    renderSemesterOptions();
    renderCoursePicker();
    renderCatalogue();
  }

  function renderSemesterOptions() {
    const selector = document.getElementById('bhilai-semester');
    const semesterCount = state.programme?.semesters.length || 0;
    selector.innerHTML = Array.from({ length: semesterCount }, (_, index) => {
      const semester = index + 1;
      return `<option value="${semester}">Semester ${semester}</option>`;
    }).join('');
  }

  function courseCatalogLabel(course) {
    return `${course.credits} cr · ${course.ltp.join('-')}`;
  }

  function renderCatalogue() {
    const query = document.getElementById('bhilai-course-search')?.value.trim().toLowerCase() || '';
    const rows = state.catalog.catalogue_courses
      .filter(course => `${course.code} ${course.title}`.toLowerCase().includes(query))
      .map(course => {
        const checked = state.selectedCourses.has(course.code);
        const status = course.programme_table_status.startsWith(`${state.programme?.degree} `)
          ? course.programme_table_status
          : 'Catalogue listing; elective eligibility not specified';
        return `
          <label class="bhilai-course-option">
            <input type="checkbox" data-course-code="${escapeHtml(course.code)}" ${checked ? 'checked' : ''}>
            <span>
              <strong>${escapeHtml(course.code)} — ${escapeHtml(course.title)}</strong>
              <small>${escapeHtml(courseCatalogLabel(course))} · PDF p. ${course.page}</small>
              <small>${escapeHtml(status)}</small>
            </span>
          </label>`;
      });
    document.getElementById('bhilai-course-list').innerHTML =
      rows.join('') || '<p class="text-meta">No matching catalogue courses.</p>';
  }

  function renderCoursePicker() {
    const picker = document.getElementById('bhilai-course-list');
    if (!picker) return;
    renderCatalogue();
  }

  function curriculumRows(programme, completed) {
    return programme.semesters.map(semester => {
      const courses = semester.courses.map(course => {
        const isCompleted = completed.includes(course.code);
        const type = course.placeholder
          ? 'Unspecified curriculum slot'
          : (course.category ? `${course.category} · listed in curriculum` : 'Category not specified');
        return `
          <li class="${isCompleted ? 'is-completed' : ''}">
            <span><strong>${escapeHtml(course.code)}</strong> — ${escapeHtml(course.title)}</span>
            <span>${course.credits === null ? 'credit value not stated' : `${course.credits} credits`}</span>
            <small>${escapeHtml(type)}${course.note ? ` · ${escapeHtml(course.note)}` : ''}</small>
          </li>`;
      }).join('');
      const current = semester.semester === state.profile.current_semester;
      return `
        <details class="bhilai-semester" ${current ? 'open' : ''}>
          <summary>Semester ${semester.semester}
            <span>${semester.stated_credits} credits${current ? ' · your selected semester' : ''}</span>
          </summary>
          <ul>${courses}</ul>
        </details>`;
    }).join('');
  }

  function renderWorkspace() {
    const programme = getProgramme(state.profile.programme_id);
    state.programme = programme;
    const sourceNotice = state.catalog.source.limitations
      .map(item => `<li>${escapeHtml(item)}</li>`)
      .join('');
    const catalogueCards = state.profile.shortlisted_course_codes.map(code => {
      const course = state.catalog.catalogue_courses.find(item => item.code === code);
      return course
        ? `<li><strong>${escapeHtml(course.code)} — ${escapeHtml(course.title)}</strong> (${course.credits} credits). Catalogue listing only; elective eligibility is unverified.</li>`
        : '';
    }).join('');
    const workspace = document.getElementById('bhilai-workspace');
    workspace.innerHTML = `
      <header class="bhilai-workspace-header">
        <div>
          <p class="overline">Your saved student profile</p>
          <h2>${escapeHtml(state.profile.name)}</h2>
          <p>${escapeHtml(programme.name)} · Semester ${state.profile.current_semester} · CGPA ${state.profile.cgpa}</p>
        </div>
        <div class="bhilai-workspace-actions">
          <button type="button" class="btn btn-secondary btn-sm" id="bhilai-edit-profile">Edit profile</button>
          <button type="button" class="btn btn-ghost btn-sm" id="bhilai-new-profile">Start another</button>
        </div>
      </header>
      <div class="bhilai-source-warning" role="note">
        This is the official course-of-study reference, not an institute registration or automatically
        validated personalized plan. The supplied document does not establish PE/OE eligibility for
        catalogue-only courses.
      </div>
      <nav class="bhilai-tabs" aria-label="New student sections">
        <button type="button" data-bhilai-tab="curriculum" aria-selected="true">Curriculum</button>
        <button type="button" data-bhilai-tab="catalogue" aria-selected="false">Course catalogue</button>
        <button type="button" data-bhilai-tab="assistant" aria-selected="false">Ask Buddy</button>
      </nav>
      <section data-bhilai-panel="curriculum">
        <p><strong>Minimum:</strong> ${programme.minimum_credits} credits
          ${programme.additional_non_graded_core_units
    ? ` plus ${programme.additional_non_graded_core_units} non-graded core units`
    : ''}.</p>
        <p>Source credit categories: ${Object.entries(programme.credit_categories)
    .map(([category, credits]) => `${escapeHtml(category)} ${credits}`)
    .join(' · ')}.</p>
        <p><strong>Completed courses you reported:</strong>
          ${state.profile.completed_course_codes.map(escapeHtml).join(', ') || 'None entered'}</p>
        <div class="bhilai-semester-list">${curriculumRows(programme, state.profile.completed_course_codes)}</div>
        ${catalogueCards ? `<h3>Courses of interest (not enrollment)</h3><ul>${catalogueCards}</ul>` : ''}
        <details class="bhilai-source-details">
          <summary>Source notes and limitations</summary>
          <ul>${sourceNotice}</ul>
          <p>Source: ${escapeHtml(state.catalog.source.title)}, applicable ${escapeHtml(state.catalog.source.applicable_from)}; curriculum pages ${escapeHtml(state.catalog.source.pages.join(', '))}.</p>
        </details>
      </section>
      <section data-bhilai-panel="catalogue" hidden>
        <label for="bhilai-workspace-search">Search the CSE course descriptions</label>
        <input id="bhilai-workspace-search" class="input" type="search" placeholder="Course code or title">
        <div class="bhilai-catalogue-grid" id="bhilai-workspace-catalogue"></div>
        <p class="text-meta">Catalogue presence alone does not confirm PE/OE eligibility. Shortlisting is for discussion, not enrollment.</p>
      </section>
      <section data-bhilai-panel="assistant" hidden>
        <div class="bhilai-privacy-note">
          Gemini is optional. If you enable it, your programme, semester, reported course codes, goals,
          interests, and chat messages are sent to Google Gemini for that answer. Your name and profile ID
          are not sent. Without consent or a configured key, Buddy answers locally from the supplied source.
        </div>
        <label class="bhilai-consent">
          <input id="bhilai-gemini-consent" type="checkbox">
          I consent to send the listed academic details and my message to Gemini for this reply.
        </label>
        <div class="bhilai-chat" id="bhilai-chat" aria-live="polite">
          <p class="bhilai-chat-message assistant">I can explain the source-listed curriculum and suggest next steps. I will not claim an unspecified catalogue course is PE/OE eligible.</p>
        </div>
        <form id="bhilai-chat-form" class="bhilai-chat-form">
          <label for="bhilai-question">Ask about your next steps or a course code</label>
          <textarea id="bhilai-question" class="input" rows="3" maxlength="2000" required></textarea>
          <button class="btn btn-primary" type="submit">Ask Buddy</button>
          <div id="bhilai-chat-status" class="text-meta" role="status" aria-live="polite"></div>
        </form>
      </section>`;

    document.getElementById('bhilai-profile-form-wrap').hidden = true;
    workspace.hidden = false;
    document.getElementById('bhilai-edit-profile').addEventListener('click', showProfileForm);
    document.getElementById('bhilai-new-profile').addEventListener('click', startNewProfile);
    workspace.querySelectorAll('[data-bhilai-tab]').forEach(button => {
      button.addEventListener('click', () => selectWorkspaceTab(button.dataset.bhilaiTab));
    });
    renderWorkspaceCatalogue();
    document.getElementById('bhilai-workspace-search').addEventListener('input', renderWorkspaceCatalogue);
    document.getElementById('bhilai-chat-form').addEventListener('submit', sendAssistantMessage);
  }

  function selectWorkspaceTab(tabName) {
    document.querySelectorAll('[data-bhilai-tab]').forEach(button => {
      button.setAttribute('aria-selected', String(button.dataset.bhilaiTab === tabName));
    });
    document.querySelectorAll('[data-bhilai-panel]').forEach(panel => {
      panel.hidden = panel.dataset.bhilaiPanel !== tabName;
    });
  }

  function renderWorkspaceCatalogue() {
    const root = document.getElementById('bhilai-workspace-catalogue');
    const search = document.getElementById('bhilai-workspace-search').value.trim().toLowerCase();
    const rows = state.catalog.catalogue_courses
      .filter(course => `${course.code} ${course.title}`.toLowerCase().includes(search))
      .map(course => `
        <article class="bhilai-catalogue-card">
          <strong>${escapeHtml(course.code)} — ${escapeHtml(course.title)}</strong>
          <span>${course.credits} credits · L-T-P ${course.ltp.join('-')} · PDF p. ${course.page}</span>
          <small>${escapeHtml(course.programme_table_status)}</small>
        </article>`);
    root.innerHTML = rows.join('') || '<p class="text-meta">No matching courses.</p>';
  }

  function showProfileForm() {
    document.getElementById('bhilai-workspace').hidden = true;
    document.getElementById('bhilai-profile-form-wrap').hidden = false;
    const form = document.getElementById('bhilai-profile-form');
    if (state.profile) {
      form.elements.name.value = state.profile.name;
      form.elements.programme_id.value = state.profile.programme_id;
      state.programme = getProgramme(state.profile.programme_id);
      renderSemesterOptions();
      form.elements.current_semester.value = String(state.profile.current_semester);
      form.elements.cgpa.value = String(state.profile.cgpa);
      form.elements.available_hours_per_week.value = String(state.profile.available_hours_per_week);
      form.elements.goal.value = state.profile.goal;
      form.elements.interests.value = state.profile.interests.join(', ');
      form.elements.completed_course_codes.value = state.profile.completed_course_codes.join(', ');
      state.selectedCourses = new Set(state.profile.shortlisted_course_codes);
      renderCoursePicker();
    }
  }

  function startNewProfile() {
    state.profile = null;
    state.history = [];
    state.selectedCourses.clear();
    localStorage.removeItem('bhilaiOnboardingProfileId');
    const form = document.getElementById('bhilai-profile-form');
    form.reset();
    form.elements.programme_id.value = 'iit_bhilai_btech_cse_2023';
    state.programme = getProgramme(form.elements.programme_id.value);
    renderSemesterOptions();
    renderCoursePicker();
    document.getElementById('bhilai-workspace').hidden = true;
    document.getElementById('bhilai-profile-form-wrap').hidden = false;
    clearStatus(document.getElementById('bhilai-profile-status'));
  }

  async function saveProfile(event) {
    event.preventDefault();
    if (state.saving) return;
    state.saving = true;
    const status = document.getElementById('bhilai-profile-status');
    clearStatus(status);
    status.textContent = 'Saving your profile…';
    try {
      const payload = currentPayload();
      state.profile = state.profile
        ? await api.updateOnboardingProfile(state.profile.student_id, payload)
        : await api.createOnboardingProfile(payload);
      localStorage.setItem('bhilaiOnboardingProfileId', state.profile.student_id);
      state.history = [];
      renderWorkspace();
    } catch (error) {
      showError(status, error);
    } finally {
      state.saving = false;
      if (!status.classList.contains('is-error')) status.textContent = '';
    }
  }

  function addChatMessage(role, text, mode) {
    const stream = document.getElementById('bhilai-chat');
    const message = document.createElement('p');
    message.className = `bhilai-chat-message ${role}`;
    message.textContent = text;
    stream.appendChild(message);
    if (mode) {
      const label = document.createElement('small');
      label.className = 'bhilai-chat-mode';
      label.textContent = mode === 'gemini'
        ? 'Gemini response'
        : mode === 'offline'
          ? 'Local fallback (Gemini unavailable)'
          : 'Private local response';
      stream.appendChild(label);
    }
    stream.scrollTop = stream.scrollHeight;
  }

  async function sendAssistantMessage(event) {
    event.preventDefault();
    const questionField = document.getElementById('bhilai-question');
    const status = document.getElementById('bhilai-chat-status');
    const question = questionField.value.trim();
    if (!question || !state.profile) return;
    clearStatus(status);
    status.textContent = 'Buddy is preparing a source-grounded answer…';
    const share = document.getElementById('bhilai-gemini-consent').checked;
    const priorHistory = state.history.slice(-8);
    addChatMessage('user', question);
    questionField.value = '';
    try {
      const result = await api.sendOnboardingMessage({
        profile_id: state.profile.student_id,
        question,
        share_with_gemini: share,
        history: priorHistory,
      });
      addChatMessage('assistant', `${result.reply}\n\n${result.privacy_note}`, result.mode);
      state.history = [
        ...priorHistory,
        { role: 'user', content: question },
        { role: 'assistant', content: result.reply },
      ].slice(-8);
    } catch (error) {
      showError(status, error);
      questionField.value = question;
    } finally {
      if (!status.classList.contains('is-error')) status.textContent = '';
    }
  }

  function buildDialog() {
    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = '/static/css/new-student.css';
    document.head.appendChild(stylesheet);

    const dialog = document.createElement('dialog');
    dialog.id = 'bhilai-onboarding-dialog';
    dialog.className = 'bhilai-onboarding-dialog';
    dialog.setAttribute('aria-labelledby', 'bhilai-onboarding-title');
    dialog.innerHTML = `
      <header class="bhilai-dialog-header">
        <div>
          <p class="overline">IIT Bhilai · Computer Science and Engineering</p>
          <h1 id="bhilai-onboarding-title">Start with your own student profile</h1>
          <p class="text-meta">The profile and curriculum data are saved locally in this app's database.</p>
        </div>
        <button type="button" class="btn btn-ghost" id="bhilai-close-dialog" aria-label="Close onboarding">Close</button>
      </header>
      <div id="bhilai-profile-form-wrap">
        <form id="bhilai-profile-form" class="bhilai-profile-form">
          <label>Full name
            <input class="input" name="name" autocomplete="name" maxlength="120" required>
          </label>
          <label>Programme
            <select class="input" name="programme_id" id="bhilai-programme" required></select>
          </label>
          <label>Current semester
            <select class="input" name="current_semester" id="bhilai-semester" required></select>
          </label>
          <label>Current CGPA (0–10)
            <input class="input" type="number" name="cgpa" min="0" max="10" step="0.01" value="0" required>
          </label>
          <label>Study hours available each week
            <input class="input" type="number" name="available_hours_per_week" min="0" max="80" step="0.5" value="10" required>
          </label>
          <label>Goal
            <input class="input" name="goal" maxlength="160" placeholder="e.g. systems research, software engineering" required>
          </label>
          <label class="bhilai-wide">Interests (comma-separated)
            <input class="input" name="interests" maxlength="500" placeholder="AI, algorithms, systems">
          </label>
          <label class="bhilai-wide">Completed course codes (comma-separated)
            <input class="input" name="completed_course_codes" maxlength="800" placeholder="CSL100, CSL201">
            <small>Enter only courses you report as completed. Codes are checked against this programme's named sequence.</small>
          </label>
          <fieldset class="bhilai-wide">
            <legend>Shortlist courses to discuss with Buddy</legend>
            <p class="text-meta">Shortlisting records interest only. Catalogue listing does not confirm PE/OE eligibility or enrollment.</p>
            <input class="input" id="bhilai-course-search" type="search" placeholder="Search course code or title">
            <div class="bhilai-course-list" id="bhilai-course-list"></div>
          </fieldset>
          <button class="btn btn-primary bhilai-wide" id="bhilai-save-profile" type="submit">Create profile and view curriculum</button>
          <div id="bhilai-profile-status" class="text-meta bhilai-wide" role="status" aria-live="polite"></div>
        </form>
        <p class="bhilai-source-warning" id="bhilai-programme-note"></p>
      </div>
      <section id="bhilai-workspace" hidden></section>
    `;
    document.body.appendChild(dialog);

    const selector = document.getElementById('persona-select');
    if (!selector) {
      throw new Error('Student selector is missing; new-student onboarding cannot be opened.');
    }
    const openButton = document.createElement('button');
    openButton.type = 'button';
    openButton.className = 'btn btn-secondary btn-sm bhilai-open-button';
    openButton.textContent = 'New IIT Bhilai student';
    openButton.addEventListener('click', () => openDialog());
    selector.insertAdjacentElement('afterend', openButton);

    document.getElementById('bhilai-close-dialog').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    document.getElementById('bhilai-profile-form').addEventListener('submit', saveProfile);
    document.getElementById('bhilai-programme').addEventListener('change', event => {
      state.programme = getProgramme(event.target.value);
      renderSemesterOptions();
      renderCoursePicker();
      document.getElementById('bhilai-programme-note').textContent =
        state.programme.degree === 'BTech'
          ? 'BTech requirements: 144 credits plus 12 non-graded core units. The source does not name PE/OE course choices.'
          : 'MTech requirements: 54 credits, including thesis. Elective choices are placeholders in the supplied source.';
    });
    document.getElementById('bhilai-course-search').addEventListener('input', renderCoursePicker);
    document.getElementById('bhilai-course-list').addEventListener('change', event => {
      const code = event.target.dataset.courseCode;
      if (!code) return;
      if (event.target.checked) state.selectedCourses.add(code);
      else state.selectedCourses.delete(code);
    });
    return dialog;
  }

  async function openDialog() {
    const dialog = document.getElementById('bhilai-onboarding-dialog');
    dialog.showModal();
    const status = document.getElementById('bhilai-profile-status');
    clearStatus(status);
    status.textContent = 'Loading verified programme and catalogue data…';
    try {
      state.catalog = await api.getProgrammes();
      renderProgrammeOptions();
      const profileId = localStorage.getItem('bhilaiOnboardingProfileId');
      if (profileId) {
        try {
          state.profile = await api.getOnboardingProfile(profileId);
          state.history = [];
          renderWorkspace();
          return;
        } catch (error) {
          if (error.status !== 404) throw error;
          localStorage.removeItem('bhilaiOnboardingProfileId');
        }
      }
      state.profile = null;
      document.getElementById('bhilai-profile-form-wrap').hidden = false;
      document.getElementById('bhilai-workspace').hidden = true;
      status.textContent = '';
      document.getElementById('bhilai-programme-note').textContent =
        'The supplied course-of-study document contains detailed CSE curricula for BTech and MTech. PhD is listed as a degree offering, but its curriculum is not included.';
    } catch (error) {
      showError(status, error);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    buildDialog();
  });
})();
