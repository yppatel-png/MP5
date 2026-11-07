function toDashboardData(profile, activePlan, summary, skills, exercises) {
    return {
        profile: {
            student_id: profile.student_id,
            name: profile.name,
            programme: profile.programme,
            year: profile.year,
            current_semester: profile.current_semester,
            cgpa: profile.cgpa,
            goal_id: profile.goal_id,
            target_role: profile.target_role ?? null,
            available_hours_per_week: profile.available_hours_per_week,
            remaining_elective_slots: profile.remaining_elective_slots,
        },
        plan: activePlan.plan,
        planDiff: activePlan.diff,
        certificate: activePlan.certificate,
        summary,
        skills,
        exercises: exercises.map(exercise => ({
            exercise_id: exercise.exercise_id,
            title: exercise.title || exercise.prompt,
            prompt: exercise.prompt,
            difficulty: exercise.difficulty,
            type: exercise.type,
            skill_id: exercise.skill_id,
            starter_code: exercise.starter_code,
            options: exercise.options,
        })),
    };
}
class ApiRequestError extends Error {
    requestId;
    status;
    constructor(message, requestId, status) {
        super(message);
        this.requestId = requestId;
        this.status = status;
        this.name = 'ApiRequestError';
    }
}
function formatValidationErrors(detail) {
    if (!Array.isArray(detail))
        return null;
    const issues = detail.flatMap((item) => {
        if (typeof item !== 'object' || item === null || !('msg' in item))
            return [];
        const message = typeof item.msg === 'string' ? item.msg : null;
        if (!message)
            return [];
        const location = 'loc' in item && Array.isArray(item.loc)
            ? item.loc.slice(1).map((part) => String(part)).join('.')
            : '';
        return [location ? `${location}: ${message}` : message];
    });
    return issues.length ? issues.join('; ') : 'The request contains invalid data.';
}
async function request(path, init = {}, externalSignal) {
    const requestId = crypto.randomUUID();
    const controller = new AbortController();
    const onAbort = () => controller.abort();
    externalSignal?.addEventListener('abort', onAbort, { once: true });
    const timeout = window.setTimeout(onAbort, 8000);
    try {
        const response = await fetch(path, {
            ...init,
            signal: controller.signal,
            headers: {
                ...(init.body ? { 'Content-Type': 'application/json' } : {}),
                ...init.headers,
                'X-Request-ID': requestId,
            },
        });
        const text = await response.text();
        const payload = text ? JSON.parse(text) : null;
        if (!response.ok) {
            const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
                ? payload.detail
                : null;
            const message = typeof detail === 'string'
                ? detail
                : formatValidationErrors(detail) || `The service returned an error (${response.status}).`;
            throw new ApiRequestError(message, requestId, response.status);
        }
        return payload;
    }
    catch (error) {
        if (externalSignal?.aborted) {
            throw new DOMException('Request cancelled', 'AbortError');
        }
        if (controller.signal.aborted) {
            throw new ApiRequestError('The request timed out after 8 seconds.', requestId);
        }
        if (error instanceof ApiRequestError)
            throw error;
        if (error instanceof SyntaxError) {
            throw new ApiRequestError('The service returned an unreadable response.', requestId);
        }
        throw new ApiRequestError('Could not connect to the learning service.', requestId);
    }
    finally {
        window.clearTimeout(timeout);
        externalSignal?.removeEventListener('abort', onAbort);
    }
}
function formatStudentSummary(summary) {
    const parts = [
        summary.programme_name,
        `Goal: ${summary.goal_name}`,
        `Year ${summary.year}, Semester ${summary.semester_index}`,
        `CGPA ${summary.cgpa}`,
        `${summary.weekly_hours_available} h/week available`,
    ];
    if (summary.weekly_hours_studied !== null && summary.weekly_hours_studied !== undefined) {
        parts.push(`${summary.weekly_hours_studied} h studied`);
    }
    if (summary.adherence_percentage !== null && summary.adherence_percentage !== undefined) {
        parts.push(`${summary.adherence_percentage}% pace`);
    }
    if (summary.readiness_percentage !== null && summary.readiness_percentage !== undefined) {
        parts.push(`${summary.readiness_percentage}% readiness`);
    }
    if (summary.planned_credits !== null && summary.planned_credits !== undefined && summary.credit_cap) {
        parts.push(`${summary.planned_credits} / ${summary.credit_cap} credits planned`);
    }
    if (summary.status_message) {
        parts.push(summary.status_message);
    }
    return parts.join(' · ');
}
const client = {
    request,
    getStudents(signal) {
        return request('/api/students', {}, signal);
    },
    getProgrammes(signal) {
        return request('/api/curricula', {}, signal);
    },
    createOnboardingProfile(profile) {
        return request('/api/onboarding/profiles', {
            method: 'POST',
            body: JSON.stringify(profile),
        });
    },
    updateOnboardingProfile(studentId, profile) {
        return request(`/api/onboarding/profiles/${encodeURIComponent(studentId)}`, { method: 'PUT', body: JSON.stringify(profile) });
    },
    getOnboardingProfile(studentId, signal) {
        return request(`/api/onboarding/profiles/${encodeURIComponent(studentId)}`, {}, signal);
    },
    sendOnboardingMessage(message) {
        return request('/api/onboarding/assistant', {
            method: 'POST',
            body: JSON.stringify(message),
        });
    },
    getProfile(studentId, signal) {
        return request(`/api/students/profile/${encodeURIComponent(studentId)}`, {}, signal);
    },
    getSummary(studentId, signal) {
        return request(`/api/students/${encodeURIComponent(studentId)}/summary`, {}, signal);
    },
    getSkills(studentId, signal) {
        return request(`/api/students/skills/${encodeURIComponent(studentId)}`, {}, signal);
    },
    getPlan(studentId, signal) {
        return request(`/api/plans/${encodeURIComponent(studentId)}`, {}, signal);
    },
    getExercises(skillId, signal) {
        const query = skillId ? `?skill_id=${encodeURIComponent(skillId)}` : '';
        return request(`/api/practice/exercises${query}`, {}, signal);
    },
    getResources(skillId, signal) {
        const query = skillId ? `?skill_id=${encodeURIComponent(skillId)}` : '';
        return request(`/api/practice/resources${query}`, {}, signal);
    },
    getMasteryReport(studentId, signal) {
        return request(`/api/practice/mastery/${encodeURIComponent(studentId)}`, {}, signal);
    },
    getEvidence(studentId, signal) {
        return request(`/api/students/${encodeURIComponent(studentId)}/evidence`, {}, signal);
    },
    saveProfile(profile) {
        return request('/api/students', {
            method: 'POST',
            body: JSON.stringify(profile),
        });
    },
    generatePlan(studentId, goalId) {
        return request('/api/plans/generate', {
            method: 'POST',
            body: JSON.stringify({
                student_id: studentId,
                goal_override: goalId,
                reason_for_change: 'Student onboarding preferences updated',
            }),
        });
    },
    getPlanHistory(studentId, signal) {
        return request(`/api/plans/${encodeURIComponent(studentId)}/history`, {}, signal);
    },
    getDiagnosticQuestion(studentId, answered, signal) {
        const query = new URLSearchParams({ answered: answered.join(',') });
        return request(`/api/students/${encodeURIComponent(studentId)}/diagnostic/next?${query}`, {}, signal);
    },
    submitDiagnosticAnswer(studentId, body, signal) {
        return request(`/api/students/${encodeURIComponent(studentId)}/diagnostic/submit`, { method: 'POST', body: JSON.stringify(body) }, signal);
    },
    submitExercise(body) {
        return request('/api/practice/run', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },
    getSimulationScenarios(signal) {
        return request('/api/adapt/scenarios', {}, signal);
    },
    simulateScenario(body) {
        return request('/api/adapt/simulate', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },
    overrideCourse(body) {
        return request('/api/adapt/override', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },
    getBuddyMemory(studentId, signal) {
        return request(`/api/buddy/memory/${encodeURIComponent(studentId)}`, {}, signal);
    },
    getHealth(signal) {
        return request('/api/health', {}, signal);
    },
    getSeedConsistency(signal) {
        return request('/api/admin/seed-consistency', {}, signal);
    },
    getEligibleCourses(studentId, semester, signal) {
        return request(`/api/plans/${encodeURIComponent(studentId)}/eligible?semester=${encodeURIComponent(semester)}`, {}, signal);
    },
    addPlanCourse(studentId, semester, courseCode) {
        return request(`/api/plans/${encodeURIComponent(studentId)}/courses/add`, {
            method: 'POST',
            body: JSON.stringify({ semester: Number(semester), course_code: courseCode })
        });
    },
    dropPlanCourse(studentId, semester, courseCode) {
        return request(`/api/plans/${encodeURIComponent(studentId)}/courses/drop`, {
            method: 'POST',
            body: JSON.stringify({ semester: Number(semester), course_code: courseCode })
        });
    },
    swapPlanCourse(studentId, semester, dropCode, addCode) {
        return request(`/api/plans/${encodeURIComponent(studentId)}/courses/swap`, {
            method: 'POST',
            body: JSON.stringify({ semester: Number(semester), drop_code: dropCode, add_code: addCode })
        });
    },
    toDashboardData,
    sendChat(body, signal) {
        return request('/api/buddy/chat', { method: 'POST', body: JSON.stringify(body) }, signal);
    },
    getStudents(signal) {
        return request('/api/students', {}, signal);
    },
    getCourses(signal) {
        return request('/api/courses', {}, signal);
    },
    editCourse(body, token) {
        return request('/api/admin/course', {
            method: 'POST',
            body: JSON.stringify(body),
            headers: { 'X-Admin-Token': token },
        });
    },
    editGrade(body, token) {
        return request('/api/admin/grade', {
            method: 'POST',
            body: JSON.stringify(body),
            headers: { 'X-Admin-Token': token },
        });
    },
    updateConstraints(body, token) {
        return request('/api/admin/constraint', {
            method: 'POST',
            body: JSON.stringify(body),
            headers: { 'X-Admin-Token': token },
        });
    },
    resetDatabase(token) {
        return request('/api/admin/reset', {
            method: 'POST',
            body: JSON.stringify({}),
            headers: { 'X-Admin-Token': token },
        });
    },
    formatStudentSummary,
};
window.LearningBuddyApi = client;
