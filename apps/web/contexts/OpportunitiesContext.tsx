'use client';

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
// Removed import of non-existent types - using local interfaces instead
import { volunteerApi } from '@/lib/bff';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';

// Local interface since it's not in the SDK yet
interface OpportunityDetails {
  id: string;
  title: string;
  description: string;
  organizationName: string;
  location: string;
  requirements: string[];
  timeCommitment: string;
  isActive: boolean;
}

// Define the actual API response structure (doesn't match contract yet)
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
  opportunityTitle?: string;
  organizationName?: string;
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
  const { user } = useAuth();
  const { showSuccess, showError, showInfo } = useToast();

  const loadQuickMatches = useCallback(async (limit = 10) => {
    try {
      setIsLoading(true);
      
      // Use the SDK but cast the result since there's a contract mismatch
      const volunteerId = user?.id || 'test-volunteer-123';
      
      const rawMatches = await volunteerApi.getQuickMatch({
        volunteerId,
        limit
      }) as unknown as any[];
      
      setOpportunities(rawMatches || []);
      showSuccess(`Found ${rawMatches?.length || 0} quest matches for you!`);
    } catch (error) {
      console.error('Failed to load opportunities:', error);
      const err: any = error as any;
      if (err?.status === 404) {
        setOpportunities([]);
        showInfo('No opportunities match your profile yet. Try updating your preferences or check back later.');
      } else {
        showError('Failed to load opportunities');
      }
    } finally {
      setIsLoading(false);
    }
  }, [user, showSuccess, showError, showInfo]);

  const loadOpportunityDetails = useCallback(async (opportunityId: string) => {
    try {
      setIsLoading(true);
      
      // Get real opportunity details from the API
      const opportunityDetails = await volunteerApi.getOpportunityDetails(opportunityId);
      
      setSelectedOpportunity({
        id: opportunityDetails.id,
        title: opportunityDetails.title,
        description: opportunityDetails.description,
        organizationName: `Organization ${opportunityDetails.organization_id}`, // TODO: Get real org name when organizations API is available
        location: opportunityDetails.is_remote ? 'Remote' : opportunityDetails.location,
        requirements: opportunityDetails.requirements ? [opportunityDetails.requirements] : [],
        timeCommitment: opportunityDetails.time_commitment || 'Time commitment not specified',
        isActive: opportunityDetails.status === 'active'
      } as OpportunityDetails);
    } catch (error) {
      console.error('Failed to load opportunity details:', error);
      showError('Failed to load opportunity details');
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  const applyToOpportunity = useCallback(async (opportunityId: string, coverLetter = '') => {
    try {
      setIsApplying(true);
      
      // Use test volunteer ID if user not available
      const volunteerId = user?.id || 'test-volunteer-123';
      
      // Use the SDK instead of direct HTTP calls
      await volunteerApi.submitApplication({
        volunteerId,
        opportunityId,
        coverLetter: coverLetter || 'I am interested in this opportunity and would like to help!'
      });
      
      showSuccess('Quest application submitted successfully! dYZ+ The organization will review your heroic credentials.');
      
      // Remove the opportunity from the list (already applied) - use opportunityId
      setOpportunities(prev => prev.filter(opp => opp.opportunityId !== opportunityId));
      setSelectedOpportunity(null);
    } catch (error) {
      console.error('Failed to apply:', error);
      showError(error instanceof Error ? error.message : 'Failed to submit application');
    } finally {
      setIsApplying(false);
    }
  }, [user, showSuccess, showError]);

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

