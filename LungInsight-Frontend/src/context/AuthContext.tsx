import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import * as authApi from '@/api/auth';
import type { User } from '@/types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (fullName: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const ACCESS_TOKEN_KEY = 'lunginsight_access_token';
const REFRESH_TOKEN_KEY = 'lunginsight_refresh_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  // Rehydrate auth state on mount/reload -- without this, a stored token
  // survives a page refresh but the in-memory `user` doesn't, silently
  // bouncing an otherwise-still-logged-in user back to /login.
  useEffect(() => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) {
      setIsInitializing(false);
      return;
    }
    authApi
      .getCurrentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      })
      .finally(() => setIsInitializing(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const tokens = await authApi.login({ email, password });
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      const result = await authApi.register({ email, password, full_name: fullName });
      localStorage.setItem(ACCESS_TOKEN_KEY, result.tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, result.tokens.refresh_token);
      setUser(result.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      setUser(null);
    }
  }, []);

  const updateProfile = useCallback(async (fullName: string) => {
    const updated = await authApi.updateProfile(fullName);
    setUser(updated);
  }, []);

  const value: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    isInitializing,
    login,
    register,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
