import api from '@/api';
import type { LoginRequest, LoginResponse } from '@/types/user';

const authApi = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/login', payload);
    return data;
  },
};

export default authApi;

