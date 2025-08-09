// Generated TypeScript types from JSON schemas
// This is a placeholder - legacy code generation path

export interface Application {
  id: string;
  volunteerId: string;
  opportunityId: string;
  status: string;
  createdAt: string;
  coverLetter?: string;
}

export interface MatchSuggestion {
  id: string;
  volunteerId: string;
  opportunityId: string;
  organizationId: string;
  score: number;
  generatedAt: string;
  status: string;
}

export interface VolunteerProfileView {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  level: string;
  createdAt: string;
}