"use client";

import React, { useMemo, useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { WelcomeStep } from './steps/WelcomeStep';
import { UserTypeStep } from './steps/UserTypeStep';
import { ProfileStep } from './steps/ProfileStep';
import { PreferencesStep } from './steps/PreferencesStep';
import { CompletionStep } from './steps/CompletionStep';

export type UserType = 'volunteer' | 'organization';

export interface OnboardingData {
  userType: UserType | null;
  name: string;
  email: string;
  location: string;
  bio: string;
  interests: string[]; // general interests
  skills: string[];
  causes: string[]; // cause areas
  availability: {
    weekdays: boolean;
    weekends: boolean;
    evenings: boolean;
  };
  // org fields
  organizationName?: string;
  organizationType?: string;
}

interface OnboardingFlowProps {
  onComplete: (data: OnboardingData) => Promise<void> | void;
  onSkip?: () => void;
  initialEmail?: string;
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete, onSkip, initialEmail }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [data, setData] = useState<OnboardingData>({
    userType: null,
    name: '',
    email: initialEmail || '',
    location: '',
    bio: '',
    interests: [],
    skills: [],
    causes: [],
    availability: { weekdays: false, weekends: false, evenings: false },
  });

  const steps = useMemo(() => ([
    { component: WelcomeStep, title: 'Welcome' },
    { component: UserTypeStep, title: 'Choose Your Journey' },
    { component: ProfileStep, title: 'Basic Profile' },
    { component: PreferencesStep, title: 'Preferences' },
    { component: CompletionStep, title: 'Complete' },
  ]), []);

  const progress = Math.round(((currentStep + 1) / steps.length) * 100);

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setSubmitting(true);
      try {
        await onComplete(data);
      } finally {
        setSubmitting(false);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const updateData = (updates: Partial<OnboardingData>) => {
    setData(prev => ({ ...prev, ...updates }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true;
      case 1: return data.userType !== null;
      case 2:
        if (data.userType === 'organization') {
          return !!data.organizationName && !!data.location;
        }
        return !!data.name && !!data.email && !!data.location;
      case 3:
        if (data.userType === 'organization') {
          return data.causes.length > 0;
        }
        return data.skills.length >= 1 && (data.availability.weekdays || data.availability.weekends || data.availability.evenings);
      case 4: return true;
      default: return false;
    }
  };

  const Current = steps[currentStep].component as any;

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-pixel text-white">Step {currentStep + 1} of {steps.length}</span>
            <span className="text-sm font-pixel text-electric-teal">{progress}%</span>
          </div>
          <div className="clip-px bg-dark-surface/30 h-2">
            <div className="bg-gradient-to-r from-electric-teal to-neon-cyan h-full clip-px transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Card */}
        <PxCard variant="default" className="mb-4">
          <div className="text-center mb-4">
            <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">{steps[currentStep].title}</h2>
          </div>
          <Current data={data} updateData={updateData} onNext={handleNext} />
        </PxCard>

        {/* Nav */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {currentStep > 0 && (
              <PxButton variant="secondary" onClick={handleBack}>Back</PxButton>
            )}
            {onSkip && currentStep === 0 && (
              <PxButton variant="secondary" onClick={onSkip}>Skip</PxButton>
            )}
          </div>
          <PxButton variant="primary" onClick={handleNext} disabled={!canProceed() || submitting}>
            {currentStep === steps.length - 1 ? (submitting ? 'Saving...' : 'Complete') : 'Next'}
          </PxButton>
        </div>
      </div>
    </div>
  );
};

