'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard } from '@seraaj/ui';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { VolunteerDashboardResponse, MatchSuggestion } from '@seraaj/sdk-bff';

interface DashboardData {
  dashboard: VolunteerDashboardResponse | null;
  quickMatches: MatchSuggestion[] | null;
  isLoading: boolean;
  error: string | null;
}

export default function DashboardPage() {
  const { user, tokens } = useAuth();
  const [data, setData] = useState<DashboardData>({
    dashboard: null,
    quickMatches: null,
    isLoading: true,
    error: null
  });

  useEffect(() => {
    const loadDashboardData = async () => {
      if (!user || !tokens?.accessToken) return;

      try {
        setData(prev => ({ ...prev, isLoading: true, error: null }));
        
        const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
        
        // Load dashboard data and quick matches in parallel
        const [dashboardResult, quickMatchResult] = await Promise.allSettled([
          volunteerApi.getVolunteerDashboard(user.id),
          volunteerApi.getQuickMatch({ volunteerId: user.id, limit: 5 })
        ]);

        setData({
          dashboard: dashboardResult.status === 'fulfilled' ? dashboardResult.value : null,
          quickMatches: quickMatchResult.status === 'fulfilled' ? quickMatchResult.value : null,
          isLoading: false,
          error: dashboardResult.status === 'rejected' ? 
            `Failed to load dashboard: ${dashboardResult.reason}` : null
        });
      } catch (error) {
        console.error('Failed to load dashboard:', error);
        setData(prev => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to load dashboard'
        }));
      }
    };

    loadDashboardData();
  }, [user, tokens]);

  const handleQuickMatch = async () => {
    if (!user || !tokens?.accessToken) return;

    try {
      const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
      const matches = await volunteerApi.getQuickMatch({ 
        volunteerId: user.id, 
        limit: 10 
      });
      setData(prev => ({ ...prev, quickMatches: matches }));
    } catch (error) {
      console.error('Quick match failed:', error);
    }
  };

  const handleApply = async (opportunityId: string) => {
    if (!user || !tokens?.accessToken) return;

    try {
      const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
      await volunteerApi.submitApplication({
        volunteerId: user.id,
        opportunityId,
        message: 'I am interested in this opportunity and would like to help!'
      });
      
      // Reload dashboard to show new application
      const dashboard = await volunteerApi.getVolunteerDashboard(user.id);
      setData(prev => ({ ...prev, dashboard }));
    } catch (error) {
      console.error('Application failed:', error);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        
        <main className="max-w-6xl mx-auto p-6">
          <div className="mb-8">
            <h1 className="text-2xl font-pixel text-sunBurst mb-2">
              VOLUNTEER DASHBOARD
            </h1>
            <p className="text-white">Welcome back, {user?.name}!</p>
          </div>

          {data.error && (
            <PxCard variant="default" className="mb-6">
              <p className="text-error text-sm">{data.error}</p>
            </PxCard>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Profile & Applications */}
            <div className="space-y-6">
              <PxCard variant="default">
                <h2 className="text-lg font-pixel text-sunBurst mb-4">PROFILE</h2>
                {data.isLoading ? (
                  <p className="text-white text-sm">Loading profile...</p>
                ) : data.dashboard?.profile ? (
                  <div className="space-y-2">
                    <p className="text-white text-sm">
                      <span className="text-electricTeal">Email:</span> {data.dashboard.profile.email}
                    </p>
                    <p className="text-white text-sm">
                      <span className="text-electricTeal">Location:</span> {data.dashboard.profile.location || 'Not specified'}
                    </p>
                    {data.dashboard.profile.skills && data.dashboard.profile.skills.length > 0 && (
                      <div>
                        <p className="text-electricTeal text-sm mb-1">Skills:</p>
                        <div className="flex flex-wrap gap-1">
                          {data.dashboard.profile.skills.map((skill, index) => (
                            <span 
                              key={index}
                              className="px-2 py-1 bg-electricTeal text-ink text-xs font-pixel rounded"
                            >
                              {skill}
                            </span>
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
                <h2 className="text-lg font-pixel text-sunBurst mb-4">ACTIVE APPLICATIONS</h2>
                {data.isLoading ? (
                  <p className="text-white text-sm">Loading applications...</p>
                ) : data.dashboard?.activeApplications && data.dashboard.activeApplications.length > 0 ? (
                  <div className="space-y-3">
                    {data.dashboard.activeApplications.map((app) => (
                      <div key={app.id} className="border border-electricTeal rounded p-3">
                        <p className="text-white text-sm mb-1">
                          Application to {app.opportunityId}
                        </p>
                        <p className="text-electricTeal text-xs">
                          Status: {app.status.toUpperCase()}
                        </p>
                        <p className="text-white text-xs">
                          Applied: {new Date(app.appliedAt).toLocaleDateString()}
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
                <h2 className="text-lg font-pixel text-sunBurst mb-4">QUICK MATCH</h2>
                <p className="text-white text-sm mb-4">
                  Find opportunities that match your skills and interests
                </p>
                <PxButton 
                  variant="primary" 
                  onClick={handleQuickMatch}
                  disabled={data.isLoading}
                >
                  {data.isLoading ? 'MATCHING...' : 'FIND MATCHES'}
                </PxButton>
              </PxCard>

              {data.quickMatches && (
                <PxCard variant="default">
                  <h2 className="text-lg font-pixel text-sunBurst mb-4">RECENT MATCHES</h2>
                  <div className="space-y-4">
                    {data.quickMatches.map((match) => (
                      <div key={match.id} className="border border-electricTeal rounded p-4">
                        <h3 className="text-white font-pixel text-sm mb-2">
                          {match.title}
                        </h3>
                        <p className="text-white text-xs mb-2">
                          {match.organizationName} • {match.location}
                        </p>
                        <p className="text-white text-xs mb-3 line-clamp-2">
                          {match.description}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-sunBurst text-xs font-pixel">
                            {match.matchScore}% MATCH
                          </span>
                          <PxButton
                            variant="success"
                            size="sm"
                            onClick={() => handleApply(match.id)}
                          >
                            APPLY
                          </PxButton>
                        </div>
                      </div>
                    ))}
                  </div>
                </PxCard>
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}