import type { LoginResponse, UserProfile } from '@/types/user';

const TOKEN_KEY = 'mason_access_token';
const USER_KEY = 'mason_current_user';

export function persistSession(session: LoginResponse): void {
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getCurrentUser(): UserProfile | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    clearSession();
    return null;
  }
}

export function isAuthenticated(): boolean {
  return Boolean(getToken() && getCurrentUser());
}

