'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { PxButton, PxCard, PxChip, PxModal } from '@seraaj/ui';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';

interface Application {
  id: string;
  volunteerId: string;
  opportunityId: string;
  status: 'pending' | 'approved' | 'rejected';
  message: string;
  appliedAt: string;
  volunteerName?: string;
  opportunityTitle?: string;
}

interface OpportunityStats {
  id: string;
  title: string;
  applicationsCount: number;
  activeVolunteers: number;
  status: 'active' | 'filled' | 'closed';
}

export default function OrganizationDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const [applications, setApplications] = useState<Application[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [reviewAction, setReviewAction] = useState<'accept' | 'reject' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');

  // Redirect volunteers
  useEffect(() => {
    if (user?.role === 'VOLUNTEER') {
      router.push('/dashboard');
    }
  }, [user, router]);

  // Load organization dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      if (!user || user.role !== 'ORG_ADMIN') return;

      try {
        setIsLoading(true);
        
        // Load organization applications and stats
        const { data, success, message } = await bffClient.get<any>(`/organization/${user.id}/dashboard`);
        if (success && data) {
          console.log('Organization dashboard data:', data);
          
          // Map application stats to UI format
          const stats = data.applicationStats || {};
          
          // For now, create mock applications based on stats until we have real application data
          const mockApplications: Application[] = [];
          for (let i = 0; i < (stats.pendingReview || 0); i++) {
            mockApplications.push({
              id: `pending-${i}`,
              volunteerId: `volunteer-${i}`,
              opportunityId: `opportunity-${i}`,
              status: 'pending',
              message: 'Application pending review',
              appliedAt: new Date().toISOString(),
              volunteerName: `Hero ${i + 1}`,
              opportunityTitle: `Quest ${i + 1}`
            });
          }
          
          setApplications(mockApplications);
          
          // Fetch opportunities data via BFF SDK
          try {
            const { data: opportunitiesData, success: okOpp } = await bffClient.get<any[]>(`/opportunities/organization/${user.id}`);
            if (okOpp && Array.isArray(opportunitiesData)) {
              const mappedOpportunities: OpportunityStats[] = opportunitiesData.map((opp: any) => ({
                id: opp.id,
                title: opp.title,
                applicationsCount: 0, // TODO: Get real count from applications service
                activeVolunteers: opp.current_volunteers || 0,
                status: opp.status === 'active' ? 'active' : opp.status === 'filled' ? 'filled' : 'closed'
              }));
              setOpportunities(mappedOpportunities);
            }
          } catch (oppError) {
            console.error('Failed to load opportunities:', oppError);
            setOpportunities([]); // Fallback to empty array
          }
        } else {
          throw new Error(message || 'Failed to load organization dashboard');
        }
      } catch (error) {
        console.error('Failed to load dashboard:', error);
        showError('Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, [user, showError]);

  const handleReviewApplication = async () => {
    if (!selectedApplication || !reviewAction) return;

    try {
      const tokensRaw = localStorage.getItem('seraaj_tokens');
      const accessToken = tokensRaw ? JSON.parse(tokensRaw).accessToken : undefined;
      const bffBase = process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api';
      const response = await fetch(`${bffBase}/applications/${selectedApplication.id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': accessToken ? `Bearer ${accessToken}` : ''
        },
        body: JSON.stringify({
          decision: reviewAction,
          reviewerNotes: reviewNotes,
          reviewerId: user?.id
        })
      });

      if (response.ok) {
        showSuccess(`✅ Application ${reviewAction}ed successfully!`);
        setSelectedApplication(null);
        setReviewAction(null);
        setReviewNotes('');
        // Reload applications
        window.location.reload();
      } else {
        throw new Error('Failed to review application');
      }
    } catch (error) {
      console.error('Review failed:', error);
      showError('Failed to review application. Please try again.');
    }
  };

  if (user?.role === 'VOLUNTEER') {
    return null; // Will redirect in useEffect
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        
        <main className="max-w-6xl mx-auto p-6">
          <div className="mb-8">
            <h1 className="text-3xl font-pixel text-sunBurst mb-2">
              🏰 GUILD COMMAND CENTER 🏰
            </h1>
            <p className="text-white text-lg">
              Welcome back, <span className="text-pixel-coral font-pixel">{user?.name?.toUpperCase()}</span>! 
              🚀 Manage your volunteer opportunities
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className="lg:col-span-1">
              <PxCard variant="glow" className="mb-6">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">⚡</span>
                  <h2 className="text-lg font-pixel text-sunBurst mb-0">QUICK ACTIONS</h2>
                </div>
                <div className="space-y-3">
                  <PxButton
                    variant="primary"
                    size="lg"
                    className="w-full"
                    onClick={() => router.push('/organization/opportunities/create')}
                  >
                    ➕ Post New Quest
                  </PxButton>
                  
                  <PxButton
                    variant="secondary"
                    size="sm"
                    className="w-full"
                    onClick={() => router.push('/organization/opportunities')}
                  >
                    📋 Manage Quests
                  </PxButton>
                  
                  <PxButton
                    variant="secondary"
                    size="sm"
                    className="w-full"
                    onClick={() => router.push('/organization/volunteers')}
                  >
                    👥 View Heroes
                  </PxButton>
                </div>
              </PxCard>

              {/* Organization Stats */}
              <PxCard variant="default">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">📊</span>
                  <h2 className="text-lg font-pixel text-primary mb-0">GUILD STATS</h2>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-white text-sm">🎯 Active Quests</span>
                    <span className="text-electric-teal font-pixel">
                      {opportunities.filter(o => o.status === 'active').length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white text-sm">📝 Pending Applications</span>
                    <span className="text-electric-teal font-pixel">
                      {applications.filter(a => a.status === 'pending').length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white text-sm">👥 Active Heroes</span>
                    <span className="text-electric-teal font-pixel">
                      {opportunities.reduce((sum, o) => sum + o.activeVolunteers, 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white text-sm">✅ Total Applications</span>
                    <span className="text-electric-teal font-pixel">
                      {applications.length}
                    </span>
                  </div>
                </div>
              </PxCard>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Pending Applications */}
              <PxCard variant="default">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <span className="text-2xl mr-2">📝</span>
                    <h2 className="text-lg font-pixel text-primary mb-0">PENDING HERO APPLICATIONS</h2>
                  </div>
                  <PxChip variant="warning" size="sm">
                    {applications.filter(a => a.status === 'pending').length} Pending
                  </PxChip>
                </div>

                {isLoading ? (
                  <div className="text-center py-8">
                    <p className="text-white">⏳ Loading applications...</p>
                  </div>
                ) : applications.filter(a => a.status === 'pending').length > 0 ? (
                  <div className="space-y-3">
                    {applications
                      .filter(a => a.status === 'pending')
                      .map((app) => (
                        <div key={app.id} className="clip-px border-px border-warning bg-warning/10 p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h3 className="font-pixel text-white text-sm">
                                👤 {app.volunteerName || `Hero ${app.volunteerId.slice(0, 8)}`}
                              </h3>
                              <p className="text-xs text-white/60">
                                🎯 Quest: {app.opportunityTitle || app.opportunityId}
                              </p>
                              <p className="text-xs text-white/60">
                                📅 Applied: {new Date(app.appliedAt).toLocaleDateString()}
                              </p>
                            </div>
                            <PxButton
                              variant="primary"
                              size="sm"
                              onClick={() => setSelectedApplication(app)}
                            >
                              📋 Review
                            </PxButton>
                          </div>
                          {app.message && (
                            <div className="mt-2">
                              <p className="text-xs text-white/80 italic">
                                💬 "{app.message}"
                              </p>
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-white/60 text-sm">No pending applications</p>
                    <p className="text-electric-teal text-xs mt-1">
                      💡 Create quests to start receiving hero applications!
                    </p>
                  </div>
                )}
              </PxCard>

              {/* Active Opportunities */}
              <PxCard variant="default">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <span className="text-2xl mr-2">🎯</span>
                    <h2 className="text-lg font-pixel text-primary mb-0">ACTIVE QUESTS</h2>
                  </div>
                  <PxButton
                    variant="success"
                    size="sm"
                    onClick={() => router.push('/organization/opportunities/create')}
                  >
                    ➕ New Quest
                  </PxButton>
                </div>

                {opportunities.length > 0 ? (
                  <div className="space-y-3">
                    {opportunities.map((opp) => (
                      <div key={opp.id} className="clip-px border-px border-electric-teal bg-dark-surface/20 p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-pixel text-white text-sm mb-1">
                              🎯 {opp.title}
                            </h3>
                            <div className="flex items-center space-x-4 text-xs text-white/60">
                              <span>📝 {opp.applicationsCount} applications</span>
                              <span>👥 {opp.activeVolunteers} active heroes</span>
                              <PxChip 
                                variant={opp.status === 'active' ? 'selected' : 'default'} 
                                size="sm"
                              >
                                {opp.status === 'active' ? '🟢' : '🔴'} {opp.status.toUpperCase()}
                              </PxChip>
                            </div>
                          </div>
                          <PxButton
                            variant="secondary"
                            size="sm"
                            onClick={() => router.push(`/organization/opportunities/${opp.id}`)}
                          >
                            📊 Manage
                          </PxButton>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🎯</div>
                    <p className="text-white/60 text-sm mb-2">No quests created yet</p>
                    <p className="text-electric-teal text-xs mb-4">
                      Start by creating your first volunteer opportunity!
                    </p>
                    <PxButton
                      variant="primary"
                      onClick={() => router.push('/organization/opportunities/create')}
                    >
                      🚀 Create First Quest
                    </PxButton>
                  </div>
                )}
              </PxCard>
            </div>
          </div>
        </main>

        {/* Application Review Modal */}
        <PxModal
          isOpen={!!selectedApplication}
          onClose={() => {
            setSelectedApplication(null);
            setReviewAction(null);
            setReviewNotes('');
          }}
          title="📋 REVIEW HERO APPLICATION"
          size="lg"
        >
          {selectedApplication && (
            <div className="space-y-4">
              <div className="clip-px border-px border-electric-teal bg-electric-teal/10 p-4">
                <h3 className="font-pixel text-electric-teal text-sm mb-2">HERO DETAILS</h3>
                <p><strong>Name:</strong> {selectedApplication.volunteerName || 'Unknown Hero'}</p>
                <p><strong>Quest:</strong> {selectedApplication.opportunityTitle || selectedApplication.opportunityId}</p>
                <p><strong>Applied:</strong> {new Date(selectedApplication.appliedAt).toLocaleString()}</p>
              </div>

              {selectedApplication.message && (
                <div className="clip-px border-px border-warning bg-warning/10 p-4">
                  <h3 className="font-pixel text-warning text-sm mb-2">APPLICATION MESSAGE</h3>
                  <p className="text-sm italic">"{selectedApplication.message}"</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📝 Review Notes (Optional)
                </label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={3}
                  placeholder="Add notes for the volunteer (will be sent to them)"
                />
              </div>

              <div className="flex space-x-3">
                <PxButton
                  variant="success"
                  onClick={() => {
                    setReviewAction('accept');
                    handleReviewApplication();
                  }}
                  disabled={!reviewAction}
                >
                  ✅ Accept Hero
                </PxButton>
                <PxButton
                  variant="error"
                  onClick={() => {
                    setReviewAction('reject');
                    handleReviewApplication();
                  }}
                  disabled={!reviewAction}
                >
                  ❌ Decline
                </PxButton>
                <PxButton
                  variant="secondary"
                  onClick={() => {
                    setSelectedApplication(null);
                    setReviewAction(null);
                    setReviewNotes('');
                  }}
                >
                  Cancel
                </PxButton>
              </div>
            </div>
          )}
        </PxModal>
      </div>
    </ProtectedRoute>
  );
}
