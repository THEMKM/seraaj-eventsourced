// Generated BFF SDK with comprehensive API clients

// Core types and enums
export enum UserRole {
  VOLUNTEER = 'VOLUNTEER',
  ORG_ADMIN = 'ORG_ADMIN',
  SUPERADMIN = 'SUPERADMIN'
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  firstName?: string;
  lastName?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

export interface VolunteerDashboardResponse {
  profile: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    level: number;
    status: string;
    skills: string[];
    badges: Array<{
      id: string;
      name: string;
      description: string;
      imageUrl: string;
      earnedAt: string;
    }>;
    totalHours: number;
    completedApplications: number;
    createdAt: string;
    lastActive: string;
    location?: string;
  };
  activeApplications: Array<{
    id: string;
    volunteerId: string;
    opportunityId: string;
    organizationId: string | null;
    status: string;
    coverLetter: string;
    submittedAt: string;
    reviewedAt: string | null;
    createdAt: string;
    updatedAt: string;
  }>;
  recentMatches: Array<{
    id: string;
    volunteerId: string;
    opportunityId: string;
    organizationId: string;
    score: number;
    scoreComponents: {
      distance: number;
      skills: number;
      availability: number;
    };
    explanation: string[];
    generatedAt: string;
    status: string;
  }>;
}

export interface ApiResponse<T = any> {
    data: T;
    success: boolean;
    message?: string;
}

export interface Configuration {
  basePath: string;
  accessToken?: string | (() => string | undefined);
}

// Base HTTP client
export class BaseClient {
  protected config: Configuration;
  
  constructor(config: Configuration) {
    this.config = config;
  }
  
  protected async request<T>(
    method: string,
    path: string,
    data?: any,
    headers: Record<string, string> = {}
  ): Promise<T> {
    const url = `${this.config.basePath}${path}`;
    
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers
    };
    
    // Add authorization header if token available
    const token = typeof this.config.accessToken === 'function' 
      ? this.config.accessToken() 
      : this.config.accessToken;
    
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: data ? JSON.stringify(data) : undefined
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
}

// Auth API client
export class AuthApi extends BaseClient {
  async registerUser(userData: {
    name: string;
    email: string;
    password: string;
    role: UserRole;
  }): Promise<LoginResponse> {
    return this.request<LoginResponse>('POST', '/auth/register', userData);
  }
  
  async loginUser(credentials: {
    email: string;
    password: string;
  }): Promise<LoginResponse> {
    return this.request<LoginResponse>('POST', '/auth/login', credentials);
  }
  
  async refreshTokens(data: {
    refreshToken: string;
  }): Promise<AuthTokens> {
    return this.request<AuthTokens>('POST', '/auth/refresh', data);
  }
  
  async getCurrentUser(): Promise<User> {
    return this.request<User>('GET', '/auth/me');
  }
}

// Volunteer API client
export class VolunteerApi extends BaseClient {
  async getQuickMatch(data: {
    volunteerId: string;
    limit?: number;
  }): Promise<any[]> {
    return this.request<any[]>('POST', '/volunteer/quick-match', data);
  }
  
  async submitApplication(data: {
    volunteerId: string;
    opportunityId: string;
    coverLetter?: string;
  }): Promise<any> {
    return this.request<any>('POST', '/volunteer/apply', data);
  }
  
  async getVolunteerDashboard(volunteerId: string): Promise<VolunteerDashboardResponse> {
    return this.request<VolunteerDashboardResponse>('GET', `/volunteer/${volunteerId}/dashboard`);
  }
  
  async getApplications(volunteerId: string): Promise<any[]> {
    return this.request<any[]>('GET', `/volunteer/${volunteerId}/applications`);
  }
}

// System API client
export class SystemApi extends BaseClient {
  async getHealth(): Promise<{
    status: string;
    timestamp: string;
    version: string;
  }> {
    return this.request('GET', '/health');
  }
}

// BFF Client (unified client)
export class BFFClient extends BaseClient {
  public auth: AuthApi;
  public volunteer: VolunteerApi;
  public system: SystemApi;
  
  constructor(config: Configuration) {
    super(config);
    this.auth = new AuthApi(config);
    this.volunteer = new VolunteerApi(config);
    this.system = new SystemApi(config);
  }
  
  // Legacy methods for backward compatibility
  async get<T>(path: string): Promise<ApiResponse<T>> {
    try {
      const data = await this.request<T>('GET', path);
      return { data, success: true };
    } catch (error) {
      return { data: null as T, success: false, message: (error as Error).message };
    }
  }
  
  async post<T>(path: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const result = await this.request<T>('POST', path, data);
      return { data: result, success: true };
    } catch (error) {
      return { data: null as T, success: false, message: (error as Error).message };
    }
  }
}

// Factory functions
export function createAuthApi(config: Configuration): AuthApi {
  return new AuthApi(config);
}

export function createVolunteerApi(config: Configuration): VolunteerApi {
  return new VolunteerApi(config);
}

export function createSystemApi(config: Configuration): SystemApi {
  return new SystemApi(config);
}

export function createBffClient(config: Configuration): BFFClient {
  return new BFFClient(config);
}

export function createAuthenticatedVolunteerApi(accessToken: string): VolunteerApi {
  return new VolunteerApi({
    basePath: process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api',
    accessToken
  });
}

// Default instances
export const bffClient = new BFFClient({ basePath: '/api' });
