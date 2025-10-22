// src/react-app/context/AuthContext.tsx
// Persistent Authentication Context with localStorage and session management

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
  hobbies: string[];
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (userData: User, rememberMe?: boolean) => void;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'aurion_auth';
const SESSION_KEY = 'aurion_session';

interface StoredAuth {
  user: User;
  timestamp: number;
  rememberMe: boolean;
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from storage
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      // Check localStorage first (persistent)
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const authData: StoredAuth = JSON.parse(stored);
        
        // Check if session is still valid (optional: add expiry check)
        const isValid = await validateSession(authData.user.email);
        
        if (isValid) {
          setUser(authData.user);
          console.log('✅ User session restored from localStorage');
        } else {
          // Session expired, clear storage
          clearAuth();
        }
      } else {
        // Check sessionStorage (for current tab only)
        const sessionStored = sessionStorage.getItem(SESSION_KEY);
        if (sessionStored) {
          const userData: User = JSON.parse(sessionStored);
          setUser(userData);
          console.log('✅ User session restored from sessionStorage');
        }
      }
    } catch (error) {
      console.error('Error initializing auth:', error);
      clearAuth();
    } finally {
      setIsLoading(false);
    }
  };

  const validateSession = async (_email: string): Promise<boolean> => {
    try {
      // Optional: Call backend to validate session
      // For now, we'll assume the session is valid if it exists
      // You can add a /validate-session endpoint to your backend
      
      // const response = await axios.post(`${API_BASE}/validate-session`, { email });
      // return response.data.valid;
      
      return true; // Assume valid for now
    } catch (error) {
      console.error('Session validation error:', error);
      return false;
    }
  };

  const login = (userData: User, rememberMe: boolean = true) => {
    setUser(userData);

    const authData: StoredAuth = {
      user: userData,
      timestamp: Date.now(),
      rememberMe
    };

    if (rememberMe) {
      // Persistent login - survives browser restart
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authData));
      console.log('✅ User logged in (persistent mode)');
    } else {
      // Session only - cleared when browser closes
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(userData));
      console.log('✅ User logged in (session mode)');
    }

    // Also keep in sessionStorage for quick access
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    clearAuth();
    console.log('✅ User logged out');
  };

  const clearAuth = () => {
    localStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(SESSION_KEY);
    // Also clear old storage key if exists
    localStorage.removeItem('aurion_user');
  };

  const updateUser = (userData: Partial<User>) => {
    if (!user) return;

    const updatedUser = { ...user, ...userData };
    setUser(updatedUser);

    // Update storage
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const authData: StoredAuth = JSON.parse(stored);
      authData.user = updatedUser;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authData));
    }

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(updatedUser));
  };

  const checkAuth = async (): Promise<boolean> => {
    if (user) return true;

    // Try to restore from storage
    await initializeAuth();
    return user !== null;
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updateUser,
    checkAuth
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
