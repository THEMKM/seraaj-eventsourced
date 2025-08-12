'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthTokens, UserRole } from '@seraaj/sdk-bff';
import { authApi } from '@/lib/bff';

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: UserRole.VOLUNTEER | UserRole.ORG_ADMIN) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedTokens = localStorage.getItem('seraaj_tokens');
        if (storedTokens) {
          const parsedTokens: AuthTokens = JSON.parse(storedTokens);
          
          // Check if token is expired
          if (isTokenExpired(parsedTokens)) {
            // Try to refresh the token
            try {
              const newTokens = await authApi.refreshTokens({ 
                refreshToken: parsedTokens.refreshToken 
              });
              await updateAuthState(null, newTokens);
            } catch (error) {
              console.error('Failed to refresh token:', error);
              logout();
            }
          } else {
            // Token is valid, get current user
            try {
              const currentUser = await authApi.getCurrentUser();
              await updateAuthState(currentUser, parsedTokens);
            } catch (error) {
              console.error('Failed to get current user:', error);
              logout();
            }
          }
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const isTokenExpired = (tokens: AuthTokens): boolean => {
    if (!tokens.accessToken) return true;
    
    try {
      const payload = JSON.parse(atob(tokens.accessToken.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch (error) {
      return true;
    }
  };

  const updateAuthState = async (userData: User | null, tokenData: AuthTokens) => {
    if (userData) {
      setUser(userData);
    } else if (tokenData) {
      // Fetch user data if not provided
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
        return;
      }
    }
    
    setTokens(tokenData);
    localStorage.setItem('seraaj_tokens', JSON.stringify(tokenData));
    
    // Update auth API token for future requests
    authApi.configuration.accessToken = tokenData.accessToken;
  };

  const login = async (email: string, password: string): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await authApi.loginUser({ email, password });
      await updateAuthState(response.user, response.tokens);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (
    name: string, 
    email: string, 
    password: string, 
    role: UserRole.VOLUNTEER | UserRole.ORG_ADMIN
  ): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await authApi.registerUser({ name, email, password, role });
      await updateAuthState(response.user, response.tokens);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    setUser(null);
    setTokens(null);
    localStorage.removeItem('seraaj_tokens');
    // Clear auth API token
    if (authApi.configuration) {
      authApi.configuration.accessToken = undefined;
    }
  };

  const refreshAuth = async (): Promise<void> => {
    if (!tokens?.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const newTokens = await authApi.refreshTokens({ 
        refreshToken: tokens.refreshToken 
      });
      await updateAuthState(null, newTokens);
    } catch (error) {
      logout();
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      tokens,
      isAuthenticated: !!user && !!tokens,
      isLoading,
      login,
      register,
      logout,
      refreshAuth
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}