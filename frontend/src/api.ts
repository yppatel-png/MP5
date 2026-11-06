import type { components, paths } from '../types/api';

type Operation<P extends keyof paths, M extends keyof paths[P]> = paths[P][M];
type JsonResponse<O> = O extends {
  responses: {
    200: {
      content: {
        'application/json': infer Body;
      };
    };
  };
}
  ? Body
  : never;

type StudentList = JsonResponse<Operation<'/api/students', 'get'>>;
type StudentProfile = JsonResponse<Operation<'/api/students/profile/{student_id}', 'get'>>;
type StudentSummary = components['schemas']['StudentSummary'];
type Skills = JsonResponse<Operation<'/api/students/skills/{student_id}', 'get'>>;
type ActivePlan = JsonResponse<Operation<'/api/plans/{student_id}', 'get'>>;
type Exercises = JsonResponse<Operation<'/api/practice/exercises', 'get'>>;
type Health = JsonResponse<Operation<'/api/health', 'get'>>;
type SeedConsistency = JsonResponse<Operation<'/api/admin/seed-consistency', 'get'>>;
type ProgrammeCatalog = JsonResponse<Operation<'/api/curricula', 'get'>>;
type ChatRequest = components['schemas']['ChatRequest'];
type ChatResponse = components['schemas']['ChatResponse'];
type StudentProfilePayload = components['schemas']['StudentProfile'];
type OnboardingProfileRequest = components['schemas']['OnboardingProfileRequest'];
type OnboardingProfile = components['schemas']['OnboardingProfileResponse'];
type OnboardingAssistantRequest = components['schemas']['OnboardingAssistantRequest'];
type OnboardingAssistantResponse = components['schemas']['OnboardingAssistantResponse'];

type DashboardData = {
  profile: {
    student_id: string;
    name: string;
    programme: string;
    year: number;
    current_semester: number;
    cgpa: number;
    goal_id: string;
    target_role: string | null;
    available_hours_per_week: number;
    remaining_elective_slots: number | null;
  };
  plan: ActivePlan['plan'];
  planDiff: ActivePlan['diff'];
  certificate: ActivePlan['certificate'] | null;
  summary: StudentSummary;
  skills: Skills;
  exercises: Exercises;
};

function toDashboardData(
  profile: StudentProfile,
  activePlan: {
    plan: ActivePlan['plan'];
    diff: ActivePlan['diff'];
    certificate: ActivePlan['certificate'] | null;
  },
  summary: StudentSummary,
  skills: Skills,
  exercises: Exercises,
): DashboardData {
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
  constructor(
    message: string,
    readonly requestId: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

function formatValidationErrors(detail: unknown): string | null {
  if (!Array.isArray(detail)) return null;
  const issues = detail.flatMap((item: unknown) => {
    if (typeof item !== 'object' || item === null || !('msg' in item)) return [];
    const message = typeof item.msg === 'string' ? item.msg : null;
    if (!message) return [];
    const location = 'loc' in item && Array.isArray(item.loc)
      ? item.loc.slice(1).map((part: unknown) => String(part)).join('.')
      : '';
    return [location ? `${location}: ${message}` : message];
  });
  return issues.length ? issues.join('; ') : 'The request contains invalid data.';
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  externalSignal?: AbortSignal,
): Promise<T> {
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
    const payload: unknown = text ? JSON.parse(text) : null;
    if (!response.ok) {
      const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
        ? (payload as { detail: unknown }).detail
        : null;
      const message = typeof detail === 'string'
        ? detail
        : formatValidationErrors(detail) || `The service returned an error (${response.status}).`;
      throw new ApiRequestError(message, requestId, response.status);
    }
    return payload as T;
  } catch (error) {
    if (externalSignal?.aborted) {
      throw new DOMException('Request cancelled', 'AbortError');
    }
    if (controller.signal.aborted) {
      throw new ApiRequestError('The request timed out after 8 seconds.', requestId);
    }
    if (error instanceof ApiRequestError) throw error;
    if (error instanceof SyntaxError) {
      throw new ApiRequestError('The service returned an unreadable response.', requestId);
    }
    throw new ApiRequestError('Could not connect to the learning service.', requestId);
  } finally {
    window.clearTimeout(timeout);
    externalSignal?.removeEventListener('abort', onAbort);
  }
}

function formatStudentSummary(summary: StudentSummary): string {
  const readiness = summary.readiness_percentage === null
    ? 'Not available'
    : `${summary.readiness_percentage}%`;
  const adherence = summary.adherence_percentage === null
    ? 'Not available'
    : `${summary.adherence_percentage}%`;
  const studied = summary.weekly_hours_studied === null
    ? 'Not available'
    : `${summary.weekly_hours_studied} h`;
  const planned = summary.planned_credits === null
    ? 'Not available'
    : `${summary.planned_credits} / ${summary.credit_cap} credits planned`;
  const headroom = summary.credit_headroom === null
    ? 'Not available'
    : `${summary.credit_headroom} credits headroom`;
  return [
    summary.programme_name,
    `Goal ${summary.goal_name}`,
    `Year ${summary.year}, Semester ${summary.semester_index}`,
    `CGPA ${summary.cgpa}`,
    `${summary.weekly_hours_available} h/week available`,
    `${studied} studied`,
    `${adherence} adherence`,
    `Readiness ${readiness}`,
    planned,
    headroom,
    summary.status_message,
  ].join(' · ');
}

const client = {
  request,
  getStudents(signal?: AbortSignal) {
    return request<StudentList>('/api/students', {}, signal);
  },
  getProgrammes(signal?: AbortSignal) {
    return request<ProgrammeCatalog>('/api/curricula', {}, signal);
  },
  createOnboardingProfile(profile: OnboardingProfileRequest) {
    return request<OnboardingProfile>('/api/onboarding/profiles', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  },
  updateOnboardingProfile(studentId: string, profile: OnboardingProfileRequest) {
    return request<OnboardingProfile>(
      `/api/onboarding/profiles/${encodeURIComponent(studentId)}`,
      { method: 'PUT', body: JSON.stringify(profile) },
    );
  },
  getOnboardingProfile(studentId: string, signal?: AbortSignal) {
    return request<OnboardingProfile>(
      `/api/onboarding/profiles/${encodeURIComponent(studentId)}`,
      {},
      signal,
    );
  },
  sendOnboardingMessage(message: OnboardingAssistantRequest) {
    return request<OnboardingAssistantResponse>('/api/onboarding/assistant', {
      method: 'POST',
      body: JSON.stringify(message),
    });
  },
  getProfile(studentId: string, signal?: AbortSignal) {
    return request<StudentProfile>(
      `/api/students/profile/${encodeURIComponent(studentId)}`,
      {},
      signal,
    );
  },
  getSummary(studentId: string, signal?: AbortSignal) {
    return request<StudentSummary>(
      `/api/students/${encodeURIComponent(studentId)}/summary`,
      {},
      signal,
    );
  },
  getSkills(studentId: string, signal?: AbortSignal) {
    return request<Skills>(
      `/api/students/skills/${encodeURIComponent(studentId)}`,
      {},
      signal,
    );
  },
  getPlan(studentId: string, signal?: AbortSignal) {
    return request<ActivePlan>(`/api/plans/${encodeURIComponent(studentId)}`, {}, signal);
  },
  getExercises(skillId?: string, signal?: AbortSignal) {
    const query = skillId ? `?skill_id=${encodeURIComponent(skillId)}` : '';
    return request<Exercises>(`/api/practice/exercises${query}`, {}, signal);
  },
  saveProfile(profile: StudentProfilePayload) {
    return request<unknown>('/api/students', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  },
  generatePlan(studentId: string, goalId?: string) {
    return request<unknown>('/api/plans/generate', {
      method: 'POST',
      body: JSON.stringify({
        student_id: studentId,
        goal_override: goalId,
        reason_for_change: 'Student onboarding preferences updated',
      }),
    });
  },
  getPlanHistory(studentId: string, signal?: AbortSignal) {
    return request<unknown[]>(
      `/api/plans/${encodeURIComponent(studentId)}/history`,
      {},
      signal,
    );
  },
  getDiagnosticQuestion(studentId: string, answered: string[], signal?: AbortSignal) {
    const query = new URLSearchParams({ answered: answered.join(',') });
    return request<{
      diagnostic_complete: boolean;
      questions_answered: number;
      estimated_questions_remaining?: number;
      message?: string;
      exercise?: {
        exercise_id: string;
        skill_id: string;
        skill_name: string;
        type: string;
        difficulty: number;
        prompt: string;
        options: string[];
      };
    }>(
      `/api/students/${encodeURIComponent(studentId)}/diagnostic/next?${query}`,
      {},
      signal,
    );
  },
  submitDiagnosticAnswer(
    studentId: string,
    body: components['schemas']['AnswerSubmission'],
    signal?: AbortSignal,
  ) {
    return request<Record<string, unknown>>(
      `/api/students/${encodeURIComponent(studentId)}/diagnostic/submit`,
      { method: 'POST', body: JSON.stringify(body) },
      signal,
    );
  },
  submitExercise(body: components['schemas']['ExerciseSubmissionModel']) {
    return request<Record<string, unknown>>('/api/practice/run', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  getSimulationScenarios(signal?: AbortSignal) {
    return request<{ count: number; scenarios: Array<{
      id: string;
      name: string;
      category: string;
      description: string;
    }> }>('/api/adapt/scenarios', {}, signal);
  },
  simulateScenario(body: components['schemas']['SimulateScenarioRequest']) {
    return request<Record<string, unknown>>('/api/adapt/simulate', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  overrideCourse(body: components['schemas']['CourseOverrideRequest']) {
    return request<Record<string, unknown>>('/api/adapt/override', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  getBuddyMemory(studentId: string, signal?: AbortSignal) {
    return request<Record<string, unknown>>(
      `/api/buddy/memory/${encodeURIComponent(studentId)}`,
      {},
      signal,
    );
  },
  getHealth(signal?: AbortSignal) {
    return request<Health>('/api/health', {}, signal);
  },
  getSeedConsistency(signal?: AbortSignal) {
    return request<SeedConsistency>(
      '/api/admin/seed-consistency',
      {},
      signal,
    );
  },
  toDashboardData,
  sendChat(body: ChatRequest, signal?: AbortSignal) {
    return request<ChatResponse>(
      '/api/buddy/chat',
      { method: 'POST', body: JSON.stringify(body) },
      signal,
    );
  },
  updateConstraints(body: components['schemas']['EditConstraintRequest'], token: string) {
    return request<unknown>('/api/admin/constraint', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'X-Admin-Token': token },
    });
  },
  resetDatabase(token: string) {
    return request<unknown>('/api/admin/reset', {
      method: 'POST',
      body: JSON.stringify({}),
      headers: { 'X-Admin-Token': token },
    });
  },
  formatStudentSummary,
};

declare global {
  interface Window {
    LearningBuddyApi: typeof client;
  }
}

window.LearningBuddyApi = client;
