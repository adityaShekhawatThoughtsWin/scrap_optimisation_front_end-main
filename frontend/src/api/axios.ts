import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL ?? '';
const API_BASE = API_URL ? `${API_URL}/api/v1` : '/api/v1';

export const formDataApi = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});
export const api = axios.create({
  baseURL: API_BASE,
});

formDataApi.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken');
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});