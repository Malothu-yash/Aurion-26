// src/react-app/services/adminApi.ts
// Admin API client for backend communication

import axios from 'axios';
import { ENV } from '@/config/env';

const API_BASE_URL = ENV.API_BASE_URL;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginResponse {
  success: boolean;
  token?: string;
  admin_id?: string;
  email?: string;
  role?: string;
  message?: string;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  suspended_users: number;
  total_memory_usage: number;
  server_uptime: number;
  cpu_usage: number;
  memory_usage: number;
  timestamp: string;
}

export interface APIUsageStats {
  provider: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate?: number;
}

export interface User {
  _id: string;
  email: string;
  display_name: string;
  role: string;
  status?: string;
  created_at: string;
  last_login?: string;
  hobbies?: string[];
}

export interface UsersResponse {
  total: number;
  users: User[];
  page: number;
  pages: number;
}

export const adminApi = {
  // Authentication
  login: async (credentials: AdminLoginRequest): Promise<AdminLoginResponse> => {
    const response = await api.post('/admin/login', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/admin/logout');
    localStorage.removeItem('admin_token');
  },

  getCurrentAdmin: async () => {
    const response = await api.get('/admin/me');
    return response.data;
  },

  // Dashboard
  getDashboardStats: async (): Promise<{ system: SystemStats; api_usage: APIUsageStats[] }> => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },

  // User Management
  getUsers: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    status?: string;
  }): Promise<UsersResponse> => {
    const response = await api.get('/admin/users', { params });
    return response.data;
  },

  getUserDetails: async (userId: string) => {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId: string, updates: Partial<User>) => {
    const response = await api.patch(`/admin/users/${userId}`, updates);
    return response.data;
  },

  deleteUser: async (userId: string) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },

  suspendUser: async (userId: string) => {
    const response = await api.post(`/admin/users/${userId}/suspend`);
    return response.data;
  },

  reactivateUser: async (userId: string) => {
    const response = await api.post(`/admin/users/${userId}/reactivate`);
    return response.data;
  },

  promoteUser: async (userId: string) => {
    const response = await api.post(`/admin/users/${userId}/promote`);
    return response.data;
  },

  // API Management
  getAPIUsage: async () => {
    const response = await api.get('/admin/api/usage');
    return response.data;
  },

  updateAPIKey: async (provider: string, apiKey: string, enabled: boolean = true) => {
    const response = await api.post('/admin/api/update-key', {
      provider,
      api_key: apiKey,
      enabled,
    });
    return response.data;
  },

  // Memory Management
  getMemoryStats: async () => {
    const response = await api.get('/admin/memory/stats');
    return response.data;
  },

  getUserMemory: async (userId: string) => {
    const response = await api.get(`/admin/memory/user/${userId}`);
    return response.data;
  },

  // Logs
  getAuditLogs: async (skip: number = 0, limit: number = 50) => {
    const response = await api.get('/admin/logs/audit', { params: { skip, limit } });
    return response.data;
  },

  getSystemLogs: async (skip: number = 0, limit: number = 100) => {
    const response = await api.get('/admin/logs/system', { params: { skip, limit } });
    return response.data;
  },

  // Server Control
  getServerStatus: async () => {
    const response = await api.get('/admin/server/status');
    return response.data;
  },

  serverAction: async (action: 'start' | 'stop' | 'restart') => {
    const response = await api.post('/admin/server/action', { action });
    return response.data;
  },

  // Admin Management
  createAdmin: async (data: {
    email: string;
    password: string;
    display_name: string;
    role: string;
  }) => {
    const response = await api.post('/admin/admins/create', data);
    return response.data;
  },
};

export default adminApi;
