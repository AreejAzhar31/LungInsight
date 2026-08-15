import axios from 'axios';

// Points at LungInsight-Backend once it's deployed. Set VITE_API_BASE_URL
// in a .env file to override for local development against a running
// backend instance.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attaches the stored access token to every outgoing request, matching the
// backend's `Authorization: Bearer <token>` expectation exactly.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('lunginsight_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On a 401, clear stale tokens so the app falls back to the logged-out
// state rather than looping on requests with a dead token. Real refresh-
// token rotation (calling POST /api/v1/auth/refresh) is a one-line addition
// here once the backend is live end-to-end with this frontend.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('lunginsight_access_token');
      localStorage.removeItem('lunginsight_refresh_token');
    }
    return Promise.reject(error);
  }
);
