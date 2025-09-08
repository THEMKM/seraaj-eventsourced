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
      
      // Map availability from hours/week to boolean slots used by backend
      const mapAvailability = (value: string | undefined) => {
        if (!value) return undefined;
        switch (value) {
          case '1-2':
            return { evenings: true };
          case '3-5':
            return { evenings: true, weekends: true };
          case '6-10':
            return { weekdays: true };
          case '10+':
            return { weekdays: true, weekends: true, evenings: true };
          default:
            return undefined;
        }
      };

      // Persist profile via BFF
      const api = createAuthenticatedVolunteerApi(tokens.accessToken);
      const mergedInterests = Array.from(new Set([...(data.interests || []), ...(data.causes || [])]));
      const orgInterests = [
        data.organizationType ? `ORG_TYPE:${data.organizationType}` : undefined,
        ...(data.causes || [])
      ].filter(Boolean) as string[];

      await api.updateVolunteerProfile(user.id, {
        name: (data.userType === 'organization' ? data.organizationName : data.name) || undefined,
        email: data.email || undefined,
        location: data.location || undefined,
        bio: data.bio || undefined,
        skills: data.userType === 'organization' ? undefined : (data.skills?.length ? data.skills : undefined),
        interests: data.userType === 'organization'
          ? (orgInterests.length ? orgInterests : undefined)
          : (mergedInterests.length ? mergedInterests : undefined),
        availability: data.userType === 'organization' ? undefined : mapAvailability(data.availability),
      });

      // Minimal client-side marker to avoid nagging users who completed onboarding
      try {
        localStorage.setItem(`seraaj_onboarding_completed_${user.id}`, 'true');
        // Keep legacy local profile cache for compatibility in dev demos
        const legacyProfileCache = {
          userType: data.userType,
          name: data.userType === 'organization' ? data.organizationName : data.name,
          email: data.email,
          location: data.location,
          bio: data.bio,
          skills: data.userType === 'organization' ? [] : data.skills,
          interests: data.interests,
          causes: data.causes,
          availability: data.userType === 'organization' ? '' : data.availability,
          organizationName: data.organizationName,
          organizationType: data.organizationType,
          organizationSize: data.organizationSize,
          onboardingCompleted: true,
          completedAt: new Date().toISOString(),
        } as any;
        localStorage.setItem(`seraaj_profile_${user.id}`, JSON.stringify(legacyProfileCache));
        localStorage.removeItem(`seraaj_onboarding_skipped_${user.id}`);
      } catch {}

      showSuccess('Onboarding complete! Your profile has been saved.');
      router.push(data.userType === 'organization' ? '/organization/dashboard' : '/dashboard');
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Failed to save onboarding');
    }
  };

  const handleSkip = () => {
    try {
      if (user?.id) {
        localStorage.setItem(`seraaj_onboarding_skipped_${user.id}`, 'true');
        localStorage.removeItem(`seraaj_onboarding_completed_${user.id}`);
      }
    } catch {}
    router.push('/dashboard');
  };

  const handleStepSave = async (data: OnboardingData, stepIndex: number) => {
    try {
      if (!user || !tokens?.accessToken) return; // silently ignore if not ready
      const api = createAuthenticatedVolunteerApi(tokens.accessToken);

      // Helper to map availability selection
      const mapAvailability = (value: string | undefined) => {
        if (!value) return undefined;
        switch (value) {
          case '1-2':
            return { evenings: true };
          case '3-5':
            return { evenings: true, weekends: true };
          case '6-10':
            return { weekdays: true };
          case '10+':
            return { weekdays: true, weekends: true, evenings: true };
          default:
            return undefined;
        }
      };

      if (stepIndex === 2) {
        // Leaving Profile step: persist basic identity + location
        await api.updateVolunteerProfile(user.id, {
          name: (data.userType === 'organization' ? data.organizationName : data.name) || undefined,
          email: data.email || undefined,
          location: data.location || undefined,
          bio: data.bio || undefined,
          // if org type is already selected, tag it in interests for orgs
          interests: data.userType === 'organization' && data.organizationType
            ? [`ORG_TYPE:${data.organizationType}`]
            : undefined,
        });
      } else if (stepIndex === 3) {
        // Leaving Preferences step: persist preferences
        if (data.userType === 'organization') {
          const orgInterests = [
            data.organizationType ? `ORG_TYPE:${data.organizationType}` : undefined,
            ...(data.causes || [])
          ].filter(Boolean) as string[];
          await api.updateVolunteerProfile(user.id, {
            interests: orgInterests.length ? orgInterests : undefined,
          });
        } else {
          const mergedInterests = Array.from(new Set([...(data.interests || []), ...(data.causes || [])]));
          await api.updateVolunteerProfile(user.id, {
            skills: (data.skills && data.skills.length > 0) ? data.skills : undefined,
            interests: mergedInterests.length ? mergedInterests : undefined,
            availability: mapAvailability(data.availability),
          });
        }
      }
    } catch (e) {
      // Non-blocking; surface error once at completion time
      console.warn('Onboarding step save failed:', e);
    }
  };

  const initialUserType: UserType | null = user?.role === 'ORG_ADMIN' ? 'organization' : user ? 'volunteer' : null;

  return (
    <ProtectedRoute>
      <OnboardingFlow 
        onComplete={handleComplete} 
        onSkip={handleSkip}
        onStepSave={handleStepSave}
        initialEmail={user?.email} 
        initialUserType={initialUserType} 
      />
    </ProtectedRoute>
  );
}
