'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthTokens, UserRole } from '@seraaj/sdk-bff';
import { authApi, authenticatedAuthApi } from '@/lib/bff';

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: UserRole.VOLUNTEER | UserRole.ORG_ADMIN) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  reloadUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const didInitRef = React.useRef(false);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (didInitRef.current) return;
        didInitRef.current = true;
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
              const currentUser = await authenticatedAuthApi.getCurrentUser();
              await updateAuthState(currentUser, parsedTokens);
            } catch (error) {
              // Clear invalid session without noisy logs
              logout();
            }
          }
        }
      } catch (error) {
        // Suppress initialization noise in dev
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
        const currentUser = await authenticatedAuthApi.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
        return;
      }
    }
    
    setTokens(tokenData);
    localStorage.setItem('seraaj_tokens', JSON.stringify(tokenData));
    
    // Note: authApi is configured without dynamic tokens
    // Token will be retrieved dynamically from localStorage by other API clients
  };

  // Helper function to extract detailed error information from API responses
  const parseApiError = (error: any): string => {
    // Check for network/connection issues first
    if (!navigator.onLine) {
      return 'No internet connection. Please check your network and try again.';
    }

    if (error?.message?.includes('fetch') || error?.code === 'NETWORK_ERROR') {
      return 'Unable to connect to server. Please try again in a few moments.';
    }

    // Now we have enhanced error information from the updated SDK
    const status = error?.status;
    const errorMessage = error?.message || 'Request failed';
    
    // Handle specific HTTP status codes with meaningful messages
    if (status === 401 || errorMessage === 'Invalid credentials') {
      return 'Invalid email or password. Please check your credentials and try again.';
    }
    
    if (status === 422) {
      // Enhanced SDK now provides detailed validation messages
      return errorMessage; // e.g., "Validation failed: password: String should have at least 8 characters"
    }

    if (status === 409) {
      return 'An account with this email already exists. Please try logging in instead.';
    }

    if (status === 429) {
      return 'Too many attempts. Please wait a few minutes before trying again.';
    }

    if (status >= 500) {
      return 'Server error. Please try again in a few moments.';
    }

    // Return the actual server error message
    return errorMessage;
  };

  const login = async (email: string, password: string): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await authApi.loginUser({ email, password });
      await updateAuthState(response.user, response.tokens);
    } catch (error: any) {
      setIsLoading(false);
      
      const errorMessage = parseApiError(error);
      
      // Create a more informative error object
      const enhancedError = new Error(errorMessage);
      (enhancedError as any).cause = error;
      throw enhancedError;
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
    } catch (error: any) {
      setIsLoading(false);
      
      const errorMessage = parseApiError(error);
      
      // Create a more informative error object
      const enhancedError = new Error(errorMessage);
      (enhancedError as any).cause = error;
      throw enhancedError;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    setUser(null);
    setTokens(null);
    localStorage.removeItem('seraaj_tokens');
    // Note: tokens are cleared from localStorage
    // Other API clients will detect this automatically
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

  const reloadUser = async (): Promise<void> => {
    try {
      const currentUser = await authenticatedAuthApi.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      // If this fails, keep existing user; caller may handle
      console.error('Failed to reload user profile:', error);
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
      refreshAuth,
      reloadUser
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
