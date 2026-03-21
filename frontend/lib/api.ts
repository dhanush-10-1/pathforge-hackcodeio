/**
 * PathForge API Client
 * Typed API calls to the backend service.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const EXTERNAL_QUIZ_URL = process.env.NEXT_PUBLIC_EXTERNAL_QUIZ_URL || 'http://localhost:8900/quiz';

async function fetchAPI(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ─── Auth ───
export async function register(name: string, email: string, password: string) {
  return fetchAPI('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
}

export async function login(email: string, password: string) {
  return fetchAPI('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

// ─── Resume ───
export async function uploadResume(userId: string, resumeText: string) {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('resume_text', resumeText);

  const res = await fetch(`${API_URL}/api/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function uploadResumeFile(userId: string, file: File) {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('file', file);

  const res = await fetch(`${API_URL}/api/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ─── Quiz ───
export async function startQuiz(targetRole: string) {
  return fetchAPI('/api/quiz/start', {
    method: 'POST',
    body: JSON.stringify({ target_role: targetRole }),
  });
}

export async function startAdaptiveQuizSession(
  targetRole: string,
  userId: string,
  experienceYears?: number | null,
  claimedLevels?: Record<string, number>
) {
  return fetchAPI('/api/quiz/start', {
    method: 'POST',
    body: JSON.stringify({
      target_role: targetRole,
      user_id: userId,
      experience_years: experienceYears ?? undefined,
      claimed_levels: claimedLevels,
    }),
  });
}

export function buildExternalQuizUrl(params: {
  sessionId: string;
  role: string;
  returnUrl?: string;
}) {
  const url = new URL(EXTERNAL_QUIZ_URL);
  url.searchParams.set('session_id', params.sessionId);
  url.searchParams.set('role', params.role);
  if (params.returnUrl) {
    url.searchParams.set('return_url', params.returnUrl);
  }
  return url.toString();
}

export async function submitQuiz(sessionId: string, answers: Record<string, number>) {
  return fetchAPI('/api/quiz/submit', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, answers }),
  });
}

export async function getQuizSession(sessionId: string) {
  return fetchAPI(`/api/quiz/${sessionId}`);
}

export async function getQuizResults(sessionId: string) {
  return fetchAPI(`/api/quiz/${sessionId}/results`);
}

// ─── Pathway ───
export async function generatePathway(sessionId: string) {
  return fetchAPI('/api/pathway/generate', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function getPathway(pathwayId: string) {
  return fetchAPI(`/api/pathway/${pathwayId}`);
}
