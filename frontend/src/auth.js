import axios from 'axios';

const REFRESH_STORAGE_KEY = 'fow_refresh_token';

const memoryStore = {
  accessToken: null,
  expiresAt: 0,
  refreshPromise: null,
};

const isTokenFresh = () =>
  typeof memoryStore.accessToken === 'string' && Date.now() < memoryStore.expiresAt - 5000;

export const getRefreshToken = () =>
  (typeof window !== 'undefined' && window.sessionStorage
    ? window.sessionStorage.getItem(REFRESH_STORAGE_KEY)
    : null);

export const setTokens = ({ accessToken, refreshToken, expiresIn }) => {
  if (typeof accessToken === 'string') {
    memoryStore.accessToken = accessToken;
    const duration = Number.isFinite(expiresIn) ? Number(expiresIn) * 1000 : 3600000;
    memoryStore.expiresAt = Date.now() + Math.max(duration, 1000);
  }

  if (typeof window !== 'undefined' && window.sessionStorage) {
    if (refreshToken) {
      window.sessionStorage.setItem(REFRESH_STORAGE_KEY, refreshToken);
    }
  }
};

export const clearTokens = () => {
  memoryStore.accessToken = null;
  memoryStore.expiresAt = 0;
  if (typeof window !== 'undefined' && window.sessionStorage) {
    window.sessionStorage.removeItem(REFRESH_STORAGE_KEY);
  }
};

export const ensureAccessToken = async (apiClient) => {
  if (isTokenFresh()) {
    return memoryStore.accessToken;
  }

  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return null;
  }

  if (!memoryStore.refreshPromise) {
    memoryStore.refreshPromise = apiClient
      .post(
        '/api/auth/refresh',
        {},
        {
          skipAuth: true,
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        },
      )
      .then((response) => {
        const { accessToken, expiresIn } = response.data || {};
        setTokens({ accessToken, refreshToken, expiresIn });
        return memoryStore.accessToken;
      })
      .catch((error) => {
        clearTokens();
        throw error;
      })
      .finally(() => {
        memoryStore.refreshPromise = null;
      });
  }

  try {
    return await memoryStore.refreshPromise;
  } catch (error) {
    return null;
  }
};

export const attachInterceptors = (apiClient) => {
  apiClient.interceptors.request.use(async (config) => {
    if (config.skipAuth) {
      return config;
    }

    const token = await ensureAccessToken(apiClient);
    if (token) {
      // eslint-disable-next-line no-param-reassign
      config.headers = {
        ...(config.headers || {}),
        Authorization: `Bearer ${token}`,
      };
    }
    return config;
  });

  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const refreshToken = getRefreshToken();
      const originalRequest = error?.config;
      if (
        refreshToken &&
        originalRequest &&
        !originalRequest._retry &&
        error?.response?.status === 401
      ) {
        originalRequest._retry = true; // eslint-disable-line no-underscore-dangle
        try {
          await ensureAccessToken(apiClient);
          return apiClient(originalRequest);
        } catch (refreshError) {
          clearTokens();
        }
      }
      throw error;
    },
  );
};

export const isAuthenticated = () => isTokenFresh() || !!getRefreshToken();

export const rememberAccessToken = (accessToken, expiresIn) =>
  setTokens({ accessToken, refreshToken: getRefreshToken(), expiresIn });

export default {
  attachInterceptors,
  ensureAccessToken,
  setTokens,
  clearTokens,
  isAuthenticated,
  rememberAccessToken,
};
