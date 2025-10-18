import axios from 'axios';

const getEnv = (name) =>
  typeof process !== 'undefined' && process.env ? process.env[name] : undefined;

const normaliseBaseUrl = (url) => {
  if (!url) {
    return undefined;
  }
  try {
    const originFallback =
      typeof window !== 'undefined' && window.location ? window.location.origin : undefined;
    const normalised = new URL(url, originFallback);
    return normalised.origin;
  } catch (error) {
    return undefined;
  }
};

const envBaseUrl = normaliseBaseUrl(getEnv('REACT_APP_API_BASE_URL'));
const fallbackBaseUrl = (() => {
  if (typeof window !== 'undefined' && window.location) {
    return window.location.origin;
  }
  return undefined;
})();

const API_BASE_URL = envBaseUrl || fallbackBaseUrl || 'https://localhost:5000';

const rawTimeout = getEnv('REACT_APP_API_TIMEOUT');
const parsedTimeout = Number.parseInt(rawTimeout ?? '', 10);
const API_TIMEOUT = Number.isFinite(parsedTimeout) && parsedTimeout > 0 ? parsedTimeout : 10000;

export const CHAT_ENDPOINT = '/api/chat';

export const apiClient = axios.create({
  baseURL: API_BASE_URL.replace(/\/$/, ''),
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default API_BASE_URL;
