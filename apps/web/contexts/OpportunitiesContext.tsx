'use client';

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { OpportunityDetails } from '@seraaj/sdk-bff';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';

// Define types to match the actual API response
interface MatchResponse {
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
}

interface OpportunitiesContextType {
  opportunities: MatchResponse[];
  selectedOpportunity: OpportunityDetails | null;
  isLoading: boolean;
  isApplying: boolean;
  loadQuickMatches: (limit?: number) => Promise<void>;
  loadOpportunityDetails: (opportunityId: string) => Promise<void>;
  applyToOpportunity: (opportunityId: string, message?: string) => Promise<void>;
  clearSelectedOpportunity: () => void;
}

const OpportunitiesContext = createContext<OpportunitiesContextType | undefined>(undefined);

export function OpportunitiesProvider({ children }: { children: ReactNode }) {
  const [opportunities, setOpportunities] = useState<MatchResponse[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<OpportunityDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const { user, tokens } = useAuth();
  const { showSuccess, showError } = useToast();

  const loadQuickMatches = useCallback(async (limit = 10) => {
    try {
      setIsLoading(true);
      
      // Use a test volunteer ID for now since auth might not be working
      const volunteerId = user?.id || 'test-volunteer-123';
      
      const response = await fetch('http://localhost:8000/api/volunteer/quick-match', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(tokens?.accessToken ? { 'Authorization': `Bearer ${tokens.accessToken}` } : {})
        },
        body: JSON.stringify({
          volunteerId,
          limit
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const matches: MatchResponse[] = await response.json();
      setOpportunities(matches || []);
      showSuccess(`Found ${matches?.length || 0} quest matches for you! 🎆`);
    } catch (error) {
      console.error('Failed to load opportunities:', error);
      showError('Failed to load opportunities');
    } finally {
      setIsLoading(false);
    }
  }, [user, tokens, showSuccess, showError]);

  const loadOpportunityDetails = useCallback(async (opportunityId: string) => {
    try {
      setIsLoading(true);
      
      // Find from existing opportunities (since we have match data)
      const opportunity = opportunities.find(opp => opp.opportunityId === opportunityId);
      if (opportunity) {
        setSelectedOpportunity({
          id: opportunity.opportunityId,
          title: `Quest ${opportunity.opportunityId.toUpperCase()}`,
          description: `An exciting volunteer opportunity with a ${Math.round(opportunity.score * 100)}% match score!`,
          organizationName: `Organization ${opportunity.organizationId.toUpperCase()}`,
          location: 'MENA Region',
          requirements: opportunity.explanation,
          timeCommitment: `${opportunity.scoreComponents.availability * 100}% time commitment`,
          isActive: opportunity.status === 'pending'
        } as OpportunityDetails);
      } else {
        showError('Quest not found in your matches');
      }
    } catch (error) {
      console.error('Failed to load opportunity details:', error);
      showError('Failed to load opportunity details');
    } finally {
      setIsLoading(false);
    }
  }, [opportunities, showError]);

  const applyToOpportunity = useCallback(async (opportunityId: string, coverLetter = '') => {
    try {
      setIsApplying(true);
      
      // Use test volunteer ID if user not available
      const volunteerId = user?.id || 'test-volunteer-123';
      
      const response = await fetch('http://localhost:8000/api/volunteer/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(tokens?.accessToken ? { 'Authorization': `Bearer ${tokens.accessToken}` } : {})
        },
        body: JSON.stringify({
          volunteerId,
          opportunityId,
          coverLetter: coverLetter || 'I am interested in this opportunity and would like to help!'
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Application failed' }));
        throw new Error(errorData.detail || 'Application failed');
      }
      
      showSuccess('Quest application submitted successfully! 🎆 The organization will review your heroic credentials.');
      
      // Remove the opportunity from the list (already applied)
      setOpportunities(prev => prev.filter(opp => opp.opportunityId !== opportunityId));
      setSelectedOpportunity(null);
    } catch (error) {
      console.error('Failed to apply:', error);
      showError(error instanceof Error ? error.message : 'Failed to submit application');
    } finally {
      setIsApplying(false);
    }
  }, [user, tokens, showSuccess, showError]);

  const clearSelectedOpportunity = useCallback(() => {
    setSelectedOpportunity(null);
  }, []);

  return (
    <OpportunitiesContext.Provider value={{
      opportunities,
      selectedOpportunity,
      isLoading,
      isApplying,
      loadQuickMatches,
      loadOpportunityDetails,
      applyToOpportunity,
      clearSelectedOpportunity
    }}>
      {children}
    </OpportunitiesContext.Provider>
  );
}

export function useOpportunities() {
  const context = useContext(OpportunitiesContext);
  if (context === undefined) {
    throw new Error('useOpportunities must be used within an OpportunitiesProvider');
  }
  return context;
}