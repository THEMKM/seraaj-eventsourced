/**
 * Auto-generated TypeScript types for Seraaj BFF API
 * Generated from: contracts/v1.0.0/api/bff.openapi.yaml
 */

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
  timestamp?: string;
  requestId?: string;
}

export interface HealthResponse {
  status: 'healthy';
  timestamp?: string;
  version?: string;
}

export interface QuickMatchRequest {
  volunteerId: string;
  limit?: number;
}

export interface VolunteerDashboardResponse {
  profile: any; // Will be replaced with actual schema
  activeApplications: any[];
  recentMatches: any[];
}

export interface SubmitApplicationRequest {
  // Will be populated based on actual schema
  [key: string]: any;
}

export interface Application {
  // Will be populated based on actual schema
  [key: string]: any;
}

export interface MatchSuggestion {
  // Will be populated based on actual schema
  [key: string]: any;
}