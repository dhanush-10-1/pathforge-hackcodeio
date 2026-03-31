/**
 * PathForge API Client
 * Typed API calls to the backend service with JWT authentication.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const EXTERNAL_QUIZ_URL = process.env.NEXT_PUBLIC_EXTERNAL_QUIZ_URL || 'http://localhost:8900/quiz';

// Token management
const TOKEN_KEY = 'pathforge_token';

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

async function fetchAPI(path: string, options: RequestInit = {}, requiresAuth: boolean = true) {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add Authorization header if authenticated
  if (requiresAuth) {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated. Please login first.');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    headers,
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    if (res.status === 401) {
      clearToken();
    }
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ─── Auth ───
export async function register(name: string, email: string, password: string) {
  const data = await fetchAPI('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  }, false); // Public endpoint
  
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

export async function login(email: string, password: string) {
  const data = await fetchAPI('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }, false); // Public endpoint
  
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

export function logout(): void {
  clearToken();
}

// ─── Resume ───
export async function uploadResume(resumeText: string) {
  const token = getToken();
  if (!token) {
    throw new Error('Not authenticated. Please login first.');
  }

  const formData = new FormData();
  formData.append('resume_text', resumeText);

  const res = await fetch(`${API_URL}/api/resume/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    if (res.status === 401) clearToken();
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function uploadResumeFile(file: File) {
  const token = getToken();
  if (!token) {
    throw new Error('Not authenticated. Please login first.');
  }

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_URL}/api/resume/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    if (res.status === 401) clearToken();
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
  experienceYears?: number | null,
  claimedLevels?: Record<string, number>
) {
  return fetchAPI('/api/quiz/start', {
    method: 'POST',
    body: JSON.stringify({
      target_role: targetRole,
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
