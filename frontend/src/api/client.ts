import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Har bir so'rovga JWT token va faol Tenant ID ni qo'shish
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const tenantId = localStorage.getItem('active_tenant_id');
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }

  return config;
});

// Response interceptor: 401 xatolikda login sahifasiga yo'naltirish
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      // Login sahifasiga o'tish
      window.dispatchEvent(new Event('auth_unauthorized'));
    }
    return Promise.reject(error);
  }
);
