import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import { mockUser } from '@/mocks/data';
import type { RegisterResponse, TokenResponse, User } from '@/types';

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  if (MOCK_MODE) {
    await mockDelay();
    return {
      user: { ...mockUser, email: payload.email, full_name: payload.full_name ?? null },
      tokens: { access_token: 'mock-access-token', refresh_token: 'mock-refresh-token', token_type: 'bearer' },
    };
  }
  const { data } = await apiClient.post<RegisterResponse>('/api/v1/auth/register', payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  if (MOCK_MODE) {
    await mockDelay();
    return { access_token: 'mock-access-token', refresh_token: 'mock-refresh-token', token_type: 'bearer' };
  }
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload);
  return data;
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  if (MOCK_MODE) {
    await mockDelay(200);
    return { access_token: 'mock-access-token', refresh_token: refreshToken, token_type: 'bearer' };
  }
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: refreshToken });
  return data;
}

export async function logout(): Promise<{ message: string }> {
  if (MOCK_MODE) {
    await mockDelay(200);
    return { message: 'Logged out successfully.' };
  }
  const { data } = await apiClient.post<{ message: string }>('/api/v1/auth/logout');
  return data;
}

export async function getCurrentUser(): Promise<User> {
  if (MOCK_MODE) {
    await mockDelay(200);
    return mockUser;
  }
  const { data } = await apiClient.get<User>('/api/v1/auth/me');
  return data;
}

export async function updateProfile(fullName: string): Promise<User> {
  if (MOCK_MODE) {
    await mockDelay(200);
    mockUser.full_name = fullName || null;
    return mockUser;
  }
  const { data } = await apiClient.patch<User>('/api/v1/auth/me', { full_name: fullName });
  return data;
}
