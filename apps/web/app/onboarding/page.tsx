"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { OnboardingFlow, OnboardingData, UserType } from '@/components/onboarding/OnboardingFlow';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';

export default function OnboardingPage() {
  const router = useRouter();
  const { user, tokens } = useAuth();
  const { showError, showSuccess } = useToast();

  const handleComplete = async (data: OnboardingData) => {
    try {
      if (!user || !tokens?.accessToken) throw new Error('Not authenticated');
      const api = createAuthenticatedVolunteerApi(tokens.accessToken);

      const interests = Array.from(new Set([...(data.interests || []), ...(data.causes || [])]));
      await api.updateVolunteerProfile(user.id, {
        name: data.userType === 'organization' ? data.organizationName : data.name,
        email: data.email,
        location: data.location,
        skills: data.userType === 'organization' ? [] : data.skills,
        interests,
        availability: data.userType === 'organization' ? undefined : data.availability,
      });

      showSuccess('Onboarding complete!');
      router.push(data.userType === 'organization' ? '/organization/dashboard' : '/dashboard');
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Failed to save onboarding');
    }
  };

  const initialUserType: UserType | null = user?.role === 'ORG_ADMIN' ? 'organization' : user ? 'volunteer' : null;

  return (
    <ProtectedRoute>
      <OnboardingFlow onComplete={handleComplete} initialEmail={user?.email} initialUserType={initialUserType} />
    </ProtectedRoute>
  );
}
