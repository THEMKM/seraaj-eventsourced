/**
 * Type definitions for @seraaj/sdk-bff
 * Generated from BFF OpenAPI specification v1.1.0
 */

export enum UserRole {
  VOLUNTEER = "VOLUNTEER",
  ORG_ADMIN = "ORG_ADMIN", 
  SUPERADMIN = "SUPERADMIN"
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  isVerified: boolean;
  createdAt: string;
  updatedAt?: string;
  lastLoginAt?: string;
  profileImageUrl?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: "Bearer";
}

export interface RegisterUserRequest {
  email: string;
  password: string;
  name: string;
  role: UserRole.VOLUNTEER | UserRole.ORG_ADMIN;
}

export interface LoginUserRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface HealthResponse {
  status: string;
  timestamp?: string;
  version?: string;
}

export interface QuickMatchRequest {
  volunteerId: string;
  limit?: number;
}

export interface MatchSuggestion {
  id: string;
  title: string;
  description: string;
  organizationName: string;
  requiredSkills: string[];
  location: string;
  timeCommitment: string;
  matchScore: number;
}

export interface SubmitApplicationRequest {
  volunteerId: string;
  opportunityId: string;
  message?: string;
}

export interface Application {
  id: string;
  volunteerId: string;
  opportunityId: string;
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn';
  message?: string;
  appliedAt: string;
  reviewedAt?: string;
  reviewerNotes?: string;
}

export interface VolunteerProfile {
  id: string;
  userId: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  skills?: string[];
  interests?: string[];
  availability?: {
    weekdays?: boolean;
    weekends?: boolean;
    evenings?: boolean;
  };
  profileImageUrl?: string;
}

export interface VolunteerDashboardResponse {
  profile: VolunteerProfile;
  activeApplications: Application[];
  recentMatches: MatchSuggestion[];
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}