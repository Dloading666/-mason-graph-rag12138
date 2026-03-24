export type UserRole = 'normal' | 'purchase' | 'admin';

export interface UserProfile {
  username: string;
  display_name: string;
  role: UserRole;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

