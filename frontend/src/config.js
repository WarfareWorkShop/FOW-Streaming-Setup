import axios from 'axios';

const API_BASE_URL =
  (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE_URL) ||
  'http://localhost:5000';

export const CHAT_ENDPOINT = '/api/chat';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default API_BASE_URL;
