'use client';

import { useEffect, useMemo, useRef } from 'react';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
import { useAuth } from '@/contexts/AuthContext';
import { SearchProvider, useSearch } from '@/contexts/SearchContext';
import { FilterPanel } from '@/components/search/FilterPanel';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard, PxLoading, PxModal, PxBadge } from '@seraaj/ui';
import { useState } from 'react';

// Create a content component that uses the search context
const OpportunitiesContent = () => {
  const { user } = useAuth();
  const { filters } = useSearch();
  const { 
    opportunities, 
    isLoading, 
    loadQuickMatches, 
    applyToOpportunity, 
    isApplying 
  } = useOpportunities();
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
  const [applicationMessage, setApplicationMessage] = useState('');

  // Filter opportunities based on selected filters
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter(opportunity => {
      // Location filter
      if (filters.location && filters.location !== 'Remote') {
        // Simple string match - in real implementation, this would be more sophisticated
        const hasLocation = opportunity.organizationName?.toLowerCase().includes(filters.location.toLowerCase()) ||
                           opportunity.opportunityTitle?.toLowerCase().includes(filters.location.toLowerCase());
        if (!hasLocation) return false;
      }

      // Causes filter (simplified - assumes opportunity has causes data)
      if (filters.causes.length > 0) {
        // For now, we'll do a simple text search in title/description
        const opportunityText = `${opportunity.opportunityTitle} ${opportunity.organizationName}`.toLowerCase();
        const hasCause = filters.causes.some(cause => 
          opportunityText.includes(cause.toLowerCase())
        );
        if (!hasCause) return false;
      }

      // Time commitment filter (simplified)
      if (filters.timeCommitment.length > 0) {
        // Simple text search for now
        const opportunityText = `${opportunity.opportunityTitle}`.toLowerCase();
        const hasTimeMatch = filters.timeCommitment.some(time => {
          if (time.includes('1-2') && (opportunityText.includes('part') || opportunityText.includes('minimal'))) return true;
          if (time.includes('3-5') && opportunityText.includes('moderate')) return true;
          if (time.includes('flexible') && opportunityText.includes('flexible')) return true;
          if (time.includes('one-time') && opportunityText.includes('event')) return true;
          return false;
        });
        if (!hasTimeMatch) return false;
      }

      return true;
    });
  }, [opportunities, filters]);

  const didInitRef = useRef(false);
  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;
    loadQuickMatches(20);
  }, [loadQuickMatches]);

  const handleApply = (opportunityId: string) => {
    setSelectedOpportunityId(opportunityId);
    setApplicationMessage(`Hi! I&apos;m ${user?.name} and I&apos;m excited about this opportunity. I believe my skills and passion align well with this cause. I would love to contribute and make a positive impact in the community.`);
  };

  const handleConfirmApplication = async () => {
    if (!selectedOpportunityId) return;
    
    await applyToOpportunity(selectedOpportunityId, applicationMessage);
    setSelectedOpportunityId(null);
    setApplicationMessage('');
  };

  const getMatchBadgeVariant = (score: number) => {
    if (score >= 85) return 'premium';
    if (score >= 70) return 'success';
    if (score >= 50) return 'warning';
    return 'default';
  };

  const getMatchEmoji = (score: number) => {
    if (score >= 85) return '🎆';
    if (score >= 70) return '✨';
    if (score >= 50) return '🔥';
    return '💫';
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        
        <main className="max-w-6xl mx-auto p-6">
          <div className="mb-8">
            <h1 className="text-3xl font-pixel text-primary dark:text-neon-cyan mb-2">
              🎯 QUEST BROWSER 🎯
            </h1>
            <p className="text-white text-lg mb-4">
              Discover opportunities perfectly matched to your heroic abilities!
            </p>
            
            <div className="flex space-x-4">
              <PxButton 
                variant="primary" 
                onClick={() => loadQuickMatches(20)}
                disabled={isLoading}
              >
                {isLoading ? '⏳ SCANNING...' : '🔄 REFRESH QUESTS'}
              </PxButton>
              
              <PxButton 
                variant="secondary" 
                onClick={() => loadQuickMatches(20)}
                disabled={isLoading}
              >
                🌌 SHOW MORE
              </PxButton>
            </div>
          </div>

          {/* Filter Panel */}
          <FilterPanel />

          {isLoading && opportunities.length === 0 ? (
            <div className="flex justify-center py-12">
              <PxLoading size="lg" variant="bright" text="Finding perfect quests for you..." />
            </div>
          ) : (
            <>
              {filteredOpportunities.length === 0 && opportunities.length > 0 ? (
                <PxCard variant="default" className="text-center py-12">
                  <div className="text-6xl mb-4">🤷‍♂️</div>
                  <h3 className="text-lg font-pixel text-primary mb-2">
                    NO QUESTS MATCH YOUR FILTERS
                  </h3>
                  <p className="text-white text-sm mb-4">
                    Try adjusting your filters or clearing them to see more opportunities.
                  </p>
                </PxCard>
              ) : opportunities.length === 0 ? (
                <PxCard variant="default" className="text-center py-12">
                  <div className="text-6xl mb-4">🔍</div>
                  <h3 className="text-lg font-pixel text-primary mb-2">
                    NO QUESTS FOUND
                  </h3>
                  <p className="text-white text-sm mb-4">
                    Try refreshing to find new opportunities!
                  </p>
                  <PxButton variant="primary" onClick={() => loadQuickMatches(10)}>
                    🔍 SEARCH FOR QUESTS
                  </PxButton>
                </PxCard>
              ) : (
                <>
                  <div className="mb-4">
                    <PxBadge variant="info" size="md">
                      🎯 Found {filteredOpportunities.length} matching quests
                    </PxBadge>
                  </div>
                  
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {filteredOpportunities.map((match) => {
                      const matchScore = Math.round(match.score * 100);
                      return (
                        <PxCard key={match.id} variant="default" className="h-full">
                          <div className="space-y-4">
                            {/* Header */}
                            <div className="space-y-2">
                              <div className="flex items-start justify-between">
                                <h3 className="text-ink dark:text-white font-pixel text-sm leading-tight">
                                  🏆 {match.opportunityTitle || `QUEST ${match.opportunityId?.toUpperCase() || 'UNKNOWN'}`}
                                </h3>
                                <PxBadge 
                                  variant={getMatchBadgeVariant(matchScore)} 
                                  size="sm"
                                  animated={matchScore >= 90}
                                >
                                  {getMatchEmoji(matchScore)} {matchScore}%
                                </PxBadge>
                              </div>
                              
                              <p className="text-ink dark:text-white text-xs">
                                🏰 {match.organizationName || match.organizationId?.toUpperCase() || 'UNKNOWN ORG'}
                              </p>
                              
                              <p className="text-electric-teal text-xs font-pixel">
                                📍 Location info available in details
                              </p>
                            </div>

                            {/* Match Details */}
                            <div className="space-y-2">
                              <div className="clip-px border-px border-electric-teal/30 bg-primary/5 p-2">
                                <p className="text-xs font-pixel text-electric-teal mb-1">
                                  ✨ MATCH BREAKDOWN:
                                </p>
                                <div className="space-y-1 text-xs text-ink dark:text-white">
                                  <div className="flex justify-between">
                                    <span>📍 Distance:</span>
                                    <span className="text-success">{Math.round(match.scoreComponents.distance * 100)}%</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>🎆 Skills:</span>
                                    <span className="text-warning">{Math.round(match.scoreComponents.skills * 100)}%</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>⏰ Availability:</span>
                                    <span className="text-info">{Math.round(match.scoreComponents.availability * 100)}%</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Explanation */}
                            {match.explanation && match.explanation.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-electric-teal text-xs font-pixel">
                                  📝 WHY IT&apos;S A MATCH:
                                </p>
                                <div className="space-y-1">
                                  {match.explanation.map((reason, index) => (
                                    <div key={index} className="flex items-start space-x-2">
                                      <span className="text-primary text-xs">•</span>
                                      <span className="text-ink dark:text-white text-xs">{reason}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Action */}
                            <div className="pt-2">
                              <PxButton
                                variant={matchScore >= 80 ? "success" : "primary"}
                                size="sm"
                                className="w-full"
                                onClick={() => handleApply(match.opportunityId)}
                                disabled={isApplying}
                              >
                                {isApplying ? '⏳ APPLYING...' : '🚀 JOIN THIS QUEST'}
                              </PxButton>
                            </div>
                          </div>
                        </PxCard>
                      );
                    })}
                  </div>
                </>
              )}
            </>
          )}
        </main>

        {/* Application Modal */}
        <PxModal
          isOpen={!!selectedOpportunityId}
          onClose={() => setSelectedOpportunityId(null)}
          title="📝 HERO APPLICATION"
          size="lg"
        >
          <div className="space-y-6">
            <div className="clip-px border-px border-electric-teal bg-primary/10 p-4">
              <p className="text-sm font-pixel text-primary mb-2">
                ✨ QUEST APPLICATION ✨
              </p>
              <p className="text-xs text-ink dark:text-white">
                Craft your hero message! Tell the quest masters why you&apos;re the perfect candidate for this mission.
              </p>
            </div>
            
            <div className="space-y-2">
              <label className="block text-xs font-pixel text-electric-teal">
                📝 YOUR HERO MESSAGE:
              </label>
              <textarea
                value={applicationMessage}
                onChange={(e) => setApplicationMessage(e.target.value)}
                className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3 min-h-[120px] resize-none"
                placeholder="Tell them about your passion, relevant experience, and why you&apos;re excited about this opportunity..."
                maxLength={500}
              />
              <p className="text-xs text-gray-400">
                {applicationMessage.length}/500 characters
              </p>
            </div>

            <div className="flex space-x-3">
              <PxButton
                variant="success"
                onClick={handleConfirmApplication}
                disabled={isApplying || !applicationMessage.trim()}
              >
                {isApplying ? '⏳ SENDING APPLICATION...' : '🚀 SUBMIT HERO APPLICATION'}
              </PxButton>
              <PxButton
                variant="secondary"
                onClick={() => setSelectedOpportunityId(null)}
                disabled={isApplying}
              >
                ❌ CANCEL
              </PxButton>
            </div>
          </div>
        </PxModal>
      </div>
    </>
  );
};

// Main component with search provider
export default function OpportunitiesPage() {
  return (
    <ProtectedRoute>
      <SearchProvider>
        <OpportunitiesContent />
      </SearchProvider>
    </ProtectedRoute>
  );
}
