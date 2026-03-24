import type { UserProfile } from '@/types/user';
import { clearSession, getCurrentUser, getToken } from '@/utils/auth';

export interface SessionState {
  token: string | null;
  user: UserProfile | null;
}

export function readSession(): SessionState {
  return {
    token: getToken(),
    user: getCurrentUser(),
  };
}

export function logout(): void {
  clearSession();
}

