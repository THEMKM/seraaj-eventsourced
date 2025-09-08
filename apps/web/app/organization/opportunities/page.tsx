'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/navigation/Header';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { bffClient } from '@/lib/bff';
import { PxButton, PxCard, PxChip } from '@seraaj/ui';

interface OpportunityItem {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'filled' | 'completed' | 'cancelled' | 'draft';
  current_volunteers?: number;
}

export default function OrgOpportunitiesListPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { showError } = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [opportunities, setOpportunities] = useState<OpportunityItem[]>([]);

  useEffect(() => {
    if (user?.role === 'VOLUNTEER') {
      router.push('/dashboard');
    }
  }, [user, router]);

  useEffect(() => {
    const load = async () => {
      if (!user || user.role !== 'ORG_ADMIN') return;
      setIsLoading(true);
      try {
        const { data, success, message } = await bffClient.get<OpportunityItem[]>(`/opportunities/organization/${user.id}`);
        if (!success || !Array.isArray(data)) throw new Error(message || 'Failed to load');
        setOpportunities(data);
      } catch (e) {
        console.error('Failed to load org opportunities:', e);
        showError('Failed to load opportunities');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [user, showError]);

  if (user?.role === 'VOLUNTEER') return null;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        <main className="max-w-5xl mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-pixel text-sunBurst">Your Opportunities</h1>
            <PxButton variant="primary" onClick={() => router.push('/organization/opportunities/create')}>Create Opportunity</PxButton>
          </div>

          <PxCard variant="glow">
            {isLoading ? (
              <div className="py-12 text-center text-white/80">Loading...</div>
            ) : opportunities.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-white/70 mb-4">No opportunities yet.</p>
                <PxButton variant="primary" onClick={() => router.push('/organization/opportunities/create')}>Create your first</PxButton>
              </div>
            ) : (
              <div className="space-y-3">
                {opportunities.map((opp) => (
                  <div key={opp.id} className="clip-px border-px border-electric-teal bg-dark-surface/20 p-4 flex items-start justify-between">
                    <div>
                      <h3 className="font-pixel text-white text-sm mb-1">{opp.title}</h3>
                      <p className="text-xs text-white/70 line-clamp-2 max-w-3xl">{opp.description}</p>
                      <div className="mt-2 flex items-center gap-3 text-xs text-white/60">
                        <PxChip variant={opp.status === 'active' ? 'selected' : 'default'} size="sm">{opp.status.toUpperCase()}</PxChip>
                        {typeof opp.current_volunteers === 'number' && (
                          <span>{opp.current_volunteers} active</span>
                        )}
                      </div>
                    </div>
                    <Link href={`/organization/opportunities/${opp.id}`}>
                      <PxButton variant="secondary" size="sm">Manage</PxButton>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </PxCard>
        </main>
      </div>
    </ProtectedRoute>
  );
}

