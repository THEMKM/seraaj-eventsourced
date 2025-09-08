'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/navigation/Header';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { bffClient } from '@/lib/bff';
import { PxButton, PxCard, PxChip, PxModal } from '@seraaj/ui';

interface OpportunityDetail {
  id: string;
  title: string;
  description: string;
  location: string;
  is_remote: boolean;
  skills_required: string[];
  status: string;
}

interface ApplicationItem {
  id: string;
  volunteerId: string;
  opportunityId: string;
  status: 'pending' | 'approved' | 'rejected' | string;
  message?: string;
  appliedAt?: string;
}

export default function ManageOpportunityPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const opportunityId = params?.id as string;
  const { user } = useAuth();
  const { showError, showSuccess } = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [opportunity, setOpportunity] = useState<OpportunityDetail | null>(null);
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [selectedApp, setSelectedApp] = useState<ApplicationItem | null>(null);
  const [decision, setDecision] = useState<'accept' | 'reject' | null>(null);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (user?.role === 'VOLUNTEER') router.push('/dashboard');
  }, [user, router]);

  const loadData = async () => {
    if (!opportunityId) return;
    setIsLoading(true);
    try {
      const [opp, apps] = await Promise.all([
        bffClient.get<OpportunityDetail>(`/opportunity/${opportunityId}`),
        bffClient.get<ApplicationItem[]>(`/opportunities/${opportunityId}/applications`)
      ]);
      if (!opp.success) throw new Error(opp.message);
      setOpportunity(opp.data);
      setApplications(Array.isArray(apps.data) ? apps.data : []);
    } catch (e) {
      console.error('Failed to load opportunity/applications', e);
      showError('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [opportunityId]);

  const pendingApps = useMemo(() => applications.filter(a => (a.status || '').toLowerCase() === 'pending'), [applications]);

  const handleReview = async () => {
    if (!selectedApp || !decision) return;
    try {
      const tokensRaw = localStorage.getItem('seraaj_tokens');
      const accessToken = tokensRaw ? JSON.parse(tokensRaw).accessToken : undefined;
      const bffBase = process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api';
      const res = await fetch(`${bffBase}/applications/${selectedApp.id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
        },
        body: JSON.stringify({ decision, reviewerNotes: notes, reviewerId: user?.id })
      });
      if (!res.ok) throw new Error('Review failed');
      showSuccess(`Application ${decision}ed`);
      setSelectedApp(null);
      setDecision(null);
      setNotes('');
      await loadData();
    } catch (e) {
      console.error('Review failed', e);
      showError('Failed to update application');
    }
  };

  if (user?.role === 'VOLUNTEER') return null;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        <main className="max-w-5xl mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-pixel text-sunBurst">Manage Opportunity</h1>
            <PxButton variant="secondary" size="sm" onClick={() => router.push('/organization/opportunities')}>Back</PxButton>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <PxCard variant="glow">
                {isLoading || !opportunity ? (
                  <div className="py-8 text-center text-white/80">Loading...</div>
                ) : (
                  <div className="space-y-3">
                    <h2 className="font-pixel text-white text-lg">{opportunity.title}</h2>
                    <p className="text-white/80 text-sm whitespace-pre-line">{opportunity.description}</p>
                    <div className="flex items-center gap-3 text-xs text-white/70">
                      <PxChip variant={opportunity.status === 'active' ? 'selected' : 'default'} size="sm">{opportunity.status.toUpperCase()}</PxChip>
                      <span>{opportunity.is_remote ? 'Remote' : opportunity.location}</span>
                    </div>
                    {opportunity.skills_required?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {opportunity.skills_required.map((s) => (
                          <PxChip key={s} size="sm">{s}</PxChip>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </PxCard>

              <PxCard variant="default">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-pixel text-primary">Applications ({applications.length})</h3>
                </div>
                {applications.length === 0 ? (
                  <div className="py-8 text-center text-white/60">No applications yet.</div>
                ) : (
                  <div className="space-y-3">
                    {applications.map((app) => (
                      <div key={app.id} className="clip-px border-px border-electric-teal bg-dark-surface/20 p-4 flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-3">
                            <h4 className="font-pixel text-white text-sm">Application #{app.id.slice(0, 8)}</h4>
                            <PxChip size="sm" variant={app.status === 'pending' ? 'default' : app.status === 'approved' ? 'selected' : 'default'}>
                              {app.status.toUpperCase()}
                            </PxChip>
                          </div>
                          {app.message && (
                            <p className="text-xs text-white/70 mt-1">{app.message}</p>
                          )}
                        </div>
                        {app.status === 'pending' && (
                          <div className="flex gap-2">
                            <PxButton variant="success" size="sm" onClick={() => { setSelectedApp(app); setDecision('accept'); }}>Accept</PxButton>
                            <PxButton variant="secondary" size="sm" onClick={() => { setSelectedApp(app); setDecision('reject'); }}>Reject</PxButton>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </PxCard>
            </div>

            <div className="lg:col-span-1 space-y-6">
              <PxCard variant="default">
                <h3 className="font-pixel text-primary mb-2">Quick Actions</h3>
                <div className="space-y-2">
                  <PxButton variant="primary" size="sm" onClick={() => router.push('/organization/opportunities/create')}>Create New Opportunity</PxButton>
                  <PxButton variant="secondary" size="sm" onClick={() => router.push('/organization/opportunities')}>View All Opportunities</PxButton>
                </div>
              </PxCard>
              {pendingApps.length > 0 && (
                <PxCard variant="glow">
                  <h3 className="font-pixel text-sunBurst mb-2">Pending Reviews</h3>
                  <p className="text-xs text-white/70">{pendingApps.length} application(s) awaiting review.</p>
                </PxCard>
              )}
            </div>
          </div>
        </main>

        <PxModal
          isOpen={!!selectedApp}
          onClose={() => { setSelectedApp(null); setDecision(null); setNotes(''); }}
          title={decision === 'accept' ? 'Accept Application' : 'Reject Application'}
          size="md"
        >
          <div className="space-y-3">
            <p className="text-sm text-white/80">Add optional notes for the volunteer.</p>
            <textarea className="w-full bg-transparent border border-electric-teal p-2 text-white text-sm" rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} />
            <div className="flex justify-end gap-2">
              <PxButton variant="secondary" onClick={() => { setSelectedApp(null); setDecision(null); setNotes(''); }}>Cancel</PxButton>
              <PxButton variant={decision === 'accept' ? 'success' : 'secondary'} onClick={handleReview}>
                {decision === 'accept' ? 'Accept' : 'Reject'}
              </PxButton>
            </div>
          </div>
        </PxModal>
      </div>
    </ProtectedRoute>
  );
}

