'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
import { useToast } from '@/contexts/ToastContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard, PxChip, PxLoading, PxModal } from '@seraaj/ui';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { VolunteerDashboardResponse } from '@seraaj/sdk-bff';

export default function DashboardPage() {
  const { user, tokens } = useAuth();
  const { opportunities, isLoading: opportunitiesLoading, loadQuickMatches, applyToOpportunity, isApplying } = useOpportunities();
  const { showSuccess, showError } = useToast();
  const [dashboard, setDashboard] = useState<VolunteerDashboardResponse | null>(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
  const [applicationMessage, setApplicationMessage] = useState('');

  useEffect(() => {
    const loadDashboard = async () => {
      if (!user || !tokens?.accessToken) return;

      try {
        setIsLoadingDashboard(true);
        const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
        const dashboardData = await volunteerApi.getVolunteerDashboard(user.id);
        setDashboard(dashboardData);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
        showError('Failed to load dashboard data');
      } finally {
        setIsLoadingDashboard(false);
      }
    };

    loadDashboard();
  }, [user, tokens, showError]);

  const handleQuickMatch = async () => {
    await loadQuickMatches(10);
  };

  const handleApply = (opportunityId: string) => {
    setSelectedOpportunityId(opportunityId);
    setApplicationMessage('I am interested in this opportunity and would like to help! I believe my skills and passion align well with this cause.');
  };

  const handleConfirmApplication = async () => {
    if (!selectedOpportunityId) return;
    
    await applyToOpportunity(selectedOpportunityId, applicationMessage);
    setSelectedOpportunityId(null);
    setApplicationMessage('');
    
    // Reload dashboard to show new application
    if (user && tokens?.accessToken) {
      try {
        const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
        const dashboardData = await volunteerApi.getVolunteerDashboard(user.id);
        setDashboard(dashboardData);
      } catch (error) {
        console.error('Failed to reload dashboard:', error);
      }
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        
        <main className="max-w-6xl mx-auto p-6">
          <div className="mb-8">
            <h1 className="text-3xl font-pixel text-primary dark:text-neon-cyan mb-2">
              🏆 HERO DASHBOARD 🏆
            </h1>
            <p className="text-white text-lg">
              Welcome back, <span className="text-pixel-coral font-pixel">{user?.name?.toUpperCase()}</span>! 
              🚀 Ready for your next quest?
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Profile & Applications */}
            <div className="space-y-6">
              <PxCard variant="default">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">🎆</span>
                  <h2 className="text-lg font-pixel text-primary mb-0">HERO PROFILE</h2>
                </div>
                {isLoadingDashboard ? (
                  <PxLoading text="Loading profile..." />
                ) : dashboard?.profile ? (
                  <div className="space-y-2">
                    <p className="text-ink dark:text-white text-sm">
                      <span className="text-electric-teal font-pixel">✉️ EMAIL:</span> {dashboard.profile.email}
                    </p>
                    <p className="text-ink dark:text-white text-sm">
                      <span className="text-electric-teal font-pixel">📍 LOCATION:</span> {dashboard.profile.location || 'Not specified'}
                    </p>
                    {dashboard.profile.skills && dashboard.profile.skills.length > 0 && (
                      <div>
                        <p className="text-electric-teal text-sm mb-2 font-pixel">🎆 SUPERPOWERS:</p>
                        <div className="flex flex-wrap gap-2">
                          {dashboard.profile.skills.map((skill, index) => (
                            <PxChip 
                              key={index}
                              variant="selected"
                              size="sm"
                            >
                              ⚡ {skill}
                            </PxChip>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-white text-sm">Profile not found</p>
                )}
              </PxCard>

              <PxCard variant="default">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">📜</span>
                  <h2 className="text-lg font-pixel text-primary mb-0">ACTIVE QUESTS</h2>
                </div>
                {isLoadingDashboard ? (
                  <PxLoading text="Loading applications..." />
                ) : dashboard?.activeApplications && dashboard.activeApplications.length > 0 ? (
                  <div className="space-y-3">
                    {dashboard.activeApplications.map((app) => (
                      <div key={app.id} className="clip-px border-px border-electric-teal p-3 bg-dark-surface/20">
                        <p className="text-ink dark:text-white text-sm mb-1 font-pixel">
                          🎯 QUEST: {app.opportunityId}
                        </p>
                        <PxChip 
                          variant={app.status === 'approved' ? 'selected' : 'default'}
                          size="sm"
                          className="mb-2"
                        >
                          {app.status === 'pending' ? '⏳' : app.status === 'approved' ? '✅' : '❌'} {app.status.toUpperCase()}
                        </PxChip>
                        <p className="text-ink dark:text-white text-xs">
                          📅 Applied: {new Date(app.appliedAt).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white text-sm">No active applications</p>
                )}
              </PxCard>
            </div>

            {/* Quick Match */}
            <div className="space-y-6">
              <PxCard variant="glow">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">✨</span>
                  <h2 className="text-lg font-pixel text-sunBurst mb-0">AI MATCHMAKER</h2>
                </div>
                <p className="text-white text-sm mb-4">
                  🚀 Let our AI find the perfect quests for your skill tree!
                </p>
                <PxButton 
                  variant="primary" 
                  onClick={handleQuickMatch}
                  disabled={opportunitiesLoading}
                >
                  {opportunitiesLoading ? '⏳ SCANNING...' : '✨ FIND QUESTS'}
                </PxButton>
              </PxCard>

              {opportunities.length > 0 && (
                <PxCard variant="default">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-2">🎯</span>
                    <h2 className="text-lg font-pixel text-primary mb-0">QUEST MATCHES</h2>
                  </div>
                  <div className="space-y-4">
                    {opportunities.map((match) => {
                      const matchScore = Math.round(match.score * 100);
                      return (
                        <div key={match.id} className="clip-px border-px border-electric-teal p-4 bg-gradient-to-r from-dark-surface/20 to-primary/10 hover:from-primary/10 hover:to-primary/20 transition-all duration-300">
                          <h3 className="text-ink dark:text-white font-pixel text-sm mb-2">
                            🏆 QUEST {match.opportunityId.toUpperCase()}
                          </h3>
                          <p className="text-ink dark:text-white text-xs mb-2">
                            🏰 {match.organizationId.toUpperCase()} • 📍 MENA REGION
                          </p>
                          <p className="text-ink dark:text-white text-xs mb-3">
                            {match.explanation.join(' • ')}
                          </p>
                          <div className="flex items-center justify-between">
                            <PxChip variant="selected" size="sm">
                              ✨ {matchScore}% MATCH
                            </PxChip>
                            <PxButton
                              variant="success"
                              size="sm"
                              onClick={() => handleApply(match.opportunityId)}
                              disabled={isApplying}
                            >
                              {isApplying ? '⏳' : '🚀 JOIN QUEST'}
                            </PxButton>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </PxCard>
              )}
            </div>
          </div>
        </main>

        {/* Application Confirmation Modal */}
        <PxModal
          isOpen={!!selectedOpportunityId}
          onClose={() => setSelectedOpportunityId(null)}
          title="📝 CONFIRM APPLICATION"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-sm">
              You are about to apply for this quest! Add a personal message to make your application stand out:
            </p>
            <textarea
              value={applicationMessage}
              onChange={(e) => setApplicationMessage(e.target.value)}
              className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
              rows={4}
              placeholder="Tell them why you're excited about this opportunity..."
            />
            <div className="flex space-x-3">
              <PxButton
                variant="success"
                onClick={handleConfirmApplication}
                disabled={isApplying}
              >
                {isApplying ? '⏳ APPLYING...' : '🚀 SUBMIT APPLICATION'}
              </PxButton>
              <PxButton
                variant="secondary"
                onClick={() => setSelectedOpportunityId(null)}
                disabled={isApplying}
              >
                CANCEL
              </PxButton>
            </div>
          </div>
        </PxModal>
      </div>
    </ProtectedRoute>
  );
}