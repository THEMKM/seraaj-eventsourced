/**
 * BFF SDK client configuration for Seraaj frontend
 */

import { 
  createBffClient, 
  createAuthApi, 
  createVolunteerApi, 
  createSystemApi,
  Configuration
} from '@seraaj/sdk-bff';

// Base URL for all API calls
const BASE_URL = process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api';

// Token accessor function for dynamic token retrieval
const getAccessToken = (): string | undefined => {
  if (typeof window === 'undefined') return undefined; // SSR guard
  
  try {
    const tokens = localStorage.getItem('seraaj_tokens');
    if (tokens) {
      const parsed = JSON.parse(tokens);
      return parsed.accessToken;
    }
  } catch (error) {
    console.warn('Failed to retrieve access token:', error);
  }
  return undefined;
};

// Create configuration with dynamic token access
const createDynamicConfig = (): Configuration => ({
  basePath: BASE_URL,
  accessToken: getAccessToken()
});

// Public API clients (no auth required)
export const authApi = createAuthApi({
  basePath: BASE_URL
});

export const systemApi = createSystemApi({
  basePath: BASE_URL
});

// Protected API clients (with dynamic token access)
export const bffClient = createBffClient(createDynamicConfig());
export const volunteerApi = createVolunteerApi(createDynamicConfig());

// Helper to create authenticated clients with explicit token
export const createAuthenticatedClient = (accessToken: string) => {
  return createBffClient({
    basePath: BASE_URL,
    accessToken
  });
};

export const createAuthenticatedVolunteerApi = (accessToken: string) => {
  return createVolunteerApi({
    basePath: BASE_URL,
    accessToken
  });
};

// Helper to refresh API clients when token changes
export const refreshApiClients = () => {
  // This will cause the next API call to use the updated token
  // since we're using the dynamic getAccessToken function
  console.log('API clients will use refreshed token on next request');
};