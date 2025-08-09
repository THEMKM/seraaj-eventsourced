/**
 * Auto-generated API classes for Seraaj BFF
 */

import { Configuration, BaseAPI } from './runtime';
import {
  ErrorResponse,
  HealthResponse,
  QuickMatchRequest,
  MatchSuggestion,
  SubmitApplicationRequest,
  Application,
  VolunteerDashboardResponse,
} from './types';

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