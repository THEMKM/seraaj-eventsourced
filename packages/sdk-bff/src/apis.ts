/**
 * API classes for @seraaj/sdk-bff
 * Generated from BFF OpenAPI specification v1.1.0
 */

import { Configuration, BaseAPI } from './runtime';
import {
  RegisterUserRequest,
  LoginUserRequest,
  RefreshTokenRequest,
  AuthResponse,
  AuthTokens,
  User,
  HealthResponse,
  QuickMatchRequest,
  MatchSuggestion,
  SubmitApplicationRequest,
  Application,
  VolunteerDashboardResponse,
} from './types';

export class AuthenticationApi extends BaseAPI {
  constructor(configuration?: Configuration) {
    super(configuration);
  }

  /**
   * Register a new user account
   */
  async registerUser(requestParameters: RegisterUserRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(requestParameters),
    });
  }

  /**
   * Login with email and password
   */
  async loginUser(requestParameters: LoginUserRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(requestParameters),
    });
  }

  /**
   * Refresh access token
   */
  async refreshTokens(requestParameters: RefreshTokenRequest): Promise<AuthTokens> {
    return this.request<AuthTokens>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify(requestParameters),
    });
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me', {
      method: 'GET',
    });
  }
}

export class SystemApi extends BaseAPI {
  constructor(configuration?: Configuration) {
    super(configuration);
  }

  /**
   * Health check endpoint
   */
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health', {
      method: 'GET',
    });
  }
}

export class VolunteerApi extends BaseAPI {
  constructor(configuration?: Configuration) {
    super(configuration);
  }

  /**
   * Get quick match suggestions for a volunteer
   */
  async getQuickMatch(requestParameters: QuickMatchRequest): Promise<MatchSuggestion[]> {
    return this.request<MatchSuggestion[]>('/volunteer/quick-match', {
      method: 'POST',
      body: JSON.stringify(requestParameters),
    });
  }

  /**
   * Submit a volunteer application
   */
  async submitApplication(requestParameters: SubmitApplicationRequest): Promise<Application> {
    return this.request<Application>('/volunteer/apply', {
      method: 'POST',
      body: JSON.stringify(requestParameters),
    });
  }

  /**
   * Get volunteer dashboard data
   */
  async getVolunteerDashboard(volunteerId: string): Promise<VolunteerDashboardResponse> {
    return this.request<VolunteerDashboardResponse>(`/volunteer/${volunteerId}/dashboard`, {
      method: 'GET',
    });
  }
}

// Default API - combines all APIs for convenience
export class DefaultApi extends BaseAPI {
  public authenticationApi: AuthenticationApi;
  public systemApi: SystemApi;
  public volunteerApi: VolunteerApi;

  constructor(configuration?: Configuration) {
    super(configuration);
    this.authenticationApi = new AuthenticationApi(configuration);
    this.systemApi = new SystemApi(configuration);
    this.volunteerApi = new VolunteerApi(configuration);
  }
}