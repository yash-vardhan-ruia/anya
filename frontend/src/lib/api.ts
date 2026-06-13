import axios from 'axios';
import { API_BASE_URL } from '@/lib/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request Interceptor: Attach JWT ──────────────────────────
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('auth-storage');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          const token = parsed?.state?.accessToken;
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch {
          // ignore parse errors
        }
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response Interceptor: Handle 401 ─────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('auth-storage');
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            const refreshToken = parsed?.state?.refreshToken;
            if (refreshToken) {
              const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refreshToken,
              });
              const newToken = res.data.accessToken;
              parsed.state.accessToken = newToken;
              localStorage.setItem('auth-storage', JSON.stringify(parsed));
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return api(originalRequest);
            }
          } catch {
            // Refresh failed – clear auth and redirect to login
            localStorage.removeItem('auth-storage');
            window.location.href = '/login';
          }
        }
      }
    }

    return Promise.reject(error);
  },
);

export default api;
