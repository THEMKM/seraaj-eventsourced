// Generated TypeScript types (fallback)


export interface Application.Schema {
  id: string;
  volunteerId: string;
  opportunityId: string;
  organizationId?: string;
  status: string;
  coverLetter?: string;
  submittedAt?: string;
  reviewedAt?: string;
  createdAt: string;
  updatedAt?: string;
}


export interface MatchSuggestion.Schema {
  id: string;
  volunteerId: string;
  opportunityId: string;
  organizationId: string;
  score: number;
  reasons?: string[];
  opportunityTitle?: string;
  organizationName?: string;
  status: string;
  generatedAt: string;
  expiresAt?: string;
}


export interface VolunteerProfileView.Schema {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  level: number;
  status?: string;
  skills?: string[];
  badges?: Record<string, any>[];
  totalHours?: number;
  completedApplications?: number;
  createdAt: string;
  lastActive?: string;
}
