import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider, useAuth } from '@/context/AuthContext';

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts unauthenticated with no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('sets the user and stores tokens after register', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.register('new@example.com', 'SecurePass123', 'New User');
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
    expect(result.current.user?.email).toBe('new@example.com');
    expect(localStorage.getItem('lunginsight_access_token')).toBeTruthy();
  });

  it('sets the user after login', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('demo@lunginsight.ai', 'SecurePass123');
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
  });

  it('clears the user and tokens on logout', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('demo@lunginsight.ai', 'SecurePass123');
    });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('lunginsight_access_token')).toBeNull();
  });

  it('throws when useAuth is used outside a provider', () => {
    expect(() => renderHook(() => useAuth())).toThrow(/useAuth must be used within an AuthProvider/);
  });

  it('rehydrates the user from a stored access token on mount', async () => {
    localStorage.setItem('lunginsight_access_token', 'existing-mock-token');
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isInitializing).toBe(true);

    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('finishes initializing immediately when there is no stored token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isInitializing).toBe(false));
    expect(result.current.isAuthenticated).toBe(false);
  });
});
