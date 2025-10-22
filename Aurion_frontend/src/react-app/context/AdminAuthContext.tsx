// src/react-app/context/AdminAuthContext.tsx
// Admin authentication context

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { adminApi, AdminLoginRequest } from '../services/adminApi';

interface AdminUser {
  admin_id: string;
  email: string;
  role: string;
  display_name?: string;
}

interface AdminAuthContextType {
  admin: AdminUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: AdminLoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export const AdminAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('admin_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if admin is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('admin_token');
      if (storedToken) {
        try {
          const adminData = await adminApi.getCurrentAdmin();
          setAdmin(adminData);
          setToken(storedToken);
        } catch (err) {
          localStorage.removeItem('admin_token');
          setToken(null);
          setAdmin(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (credentials: AdminLoginRequest) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await adminApi.login(credentials);
      
      if (!response.success) {
        throw new Error(response.message || 'Login failed');
      }

      if (response.token) {
        localStorage.setItem('admin_token', response.token);
        setToken(response.token);
        setAdmin({
          admin_id: response.admin_id!,
          email: response.email!,
          role: response.role!,
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await adminApi.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('admin_token');
      setToken(null);
      setAdmin(null);
    }
  };

  return (
    <AdminAuthContext.Provider
      value={{
        admin,
        token,
        isLoading,
        isAuthenticated: !!token && !!admin,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = () => {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within AdminAuthProvider');
  }
  return context;
};
