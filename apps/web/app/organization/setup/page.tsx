'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { useToast } from '@/contexts/ToastContext';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { PxSelect } from '@/components/forms/PxSelect';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const ORGANIZATION_TYPES = [
  'Non-Profit Organization',
  'Charity',
  'Educational Institution', 
  'Healthcare Organization',
  'Religious Organization',
  'Community Group',
  'Government Agency',
  'Corporate Social Responsibility',
  'Environmental Organization',
  'Other'
];

const CAUSE_AREAS = [
  'Education & Youth Development',
  'Health & Wellness',
  'Environment & Sustainability', 
  'Poverty & Social Services',
  'Arts & Culture',
  'Community Development',
  'Human Rights & Justice',
  'Animal Welfare',
  'Disaster Relief',
  'Technology & Innovation'
];

interface OrganizationData {
  organizationName: string;
  organizationType: string;
  description: string;
  website: string;
  location: string;
  causeAreas: string[];
  contactPhone: string;
  foundedYear: string;
}

export default function OrganizationSetupPage() {
  const router = useRouter();
  const { user, tokens } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  
  const [orgData, setOrgData] = useState<OrganizationData>({
    organizationName: '',
    organizationType: '',
    description: '',
    website: '',
    location: '',
    causeAreas: [],
    contactPhone: '',
    foundedYear: ''
  });

  // Redirect volunteers to regular onboarding
  useEffect(() => {
    if (user?.role === 'VOLUNTEER') {
      router.push('/onboarding');
    }
  }, [user, router]);

  const updateData = (field: keyof OrganizationData, value: string | string[]) => {
    setOrgData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const toggleCauseArea = (cause: string) => {
    setOrgData(prev => ({
      ...prev,
      causeAreas: prev.causeAreas.includes(cause)
        ? prev.causeAreas.filter(c => c !== cause)
        : [...prev.causeAreas, cause]
    }));
  };

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      // For now, store organization data in authenticated profile via BFF
      if (!user || !user.id) throw new Error('Not authenticated');
      const tokensRaw = localStorage.getItem('seraaj_tokens');
      const accessToken = tokensRaw ? JSON.parse(tokensRaw).accessToken : undefined;
      if (!accessToken) throw new Error('Missing access token');
      const api = createAuthenticatedVolunteerApi(accessToken);
      await api.updateVolunteerProfile(user.id, {
        name: orgData.organizationName,
        location: orgData.location,
        interests: [`ORG_TYPE:${orgData.organizationType}`, ...orgData.causeAreas]
      });

      showSuccess('🏰 Guild established successfully! Welcome to Seraaj!');
      router.push('/organization/dashboard');
    } catch (error) {
      console.error('Organization setup failed:', error);
      showError('Failed to save organization profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getProgress = () => Math.round((currentStep / 3) * 100);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-6xl mb-4">🏰</div>
              <h2 className="text-2xl font-pixel text-sunBurst mb-4">
                ESTABLISH YOUR GUILD
              </h2>
              <p className="text-ink dark:text-white">
                Set up your organization to find amazing volunteers!
              </p>
            </div>
            
            <div className="space-y-4">
              <PxInput
                label="🏰 Organization Name"
                value={orgData.organizationName}
                onChange={(e) => updateData('organizationName', e.target.value)}
                placeholder="e.g., Hope Foundation"
                required
              />
              
              <PxSelect
                label="📋 Organization Type"
                value={orgData.organizationType}
                onChange={(e) => updateData('organizationType', e.target.value)}
                options={ORGANIZATION_TYPES.map(type => ({ value: type, label: type }))}
                placeholder="Select your organization type"
              />
              
              <PxInput
                label="📍 Location"
                value={orgData.location}
                onChange={(e) => updateData('location', e.target.value)}
                placeholder="e.g., Cairo, Egypt"
                helperText="This helps volunteers find local opportunities"
              />
              
              <PxInput
                label="🌐 Website (Optional)"
                value={orgData.website}
                onChange={(e) => updateData('website', e.target.value)}
                placeholder="https://yourorganization.com"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">📝</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                TELL YOUR STORY
              </h2>
              <p className="text-ink dark:text-white text-sm">Help volunteers understand your mission</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  🎯 Organization Description
                </label>
                <textarea
                  value={orgData.description}
                  onChange={(e) => updateData('description', e.target.value)}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={4}
                  placeholder="What is your organization's mission? What impact do you make?"
                  required
                />
                <p className="text-xs text-ink/60 dark:text-white/60 mt-1">
                  Describe your mission, values, and the impact you create
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <PxInput
                  label="📞 Contact Phone"
                  value={orgData.contactPhone}
                  onChange={(e) => updateData('contactPhone', e.target.value)}
                  placeholder="+20 123 456 7890"
                />
                
                <PxInput
                  label="📅 Founded Year"
                  type="number"
                  value={orgData.foundedYear}
                  onChange={(e) => updateData('foundedYear', e.target.value)}
                  placeholder="2020"
                  min="1900"
                  max={new Date().getFullYear().toString()}
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">❤️</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                YOUR CAUSE AREAS
              </h2>
              <p className="text-ink dark:text-white text-sm">What issues does your organization focus on?</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3">
                {CAUSE_AREAS.map((cause) => (
                  <button
                    key={cause}
                    onClick={() => toggleCauseArea(cause)}
                    className={`clip-px border-px px-3 py-2 text-sm font-pixel transition-all ${
                      orgData.causeAreas.includes(cause)
                        ? 'border-success bg-success/20 text-success'
                        : 'border-electric-teal bg-dark-surface/20 text-white hover:bg-electric-teal/10'
                    }`}
                  >
                    {orgData.causeAreas.includes(cause) ? '✅' : '🤍'} {cause}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="clip-px border-px border-success bg-success/10 p-4">
              <p className="text-sm text-success font-pixel text-center">
                🏰 Selected {orgData.causeAreas.length} cause areas
              </p>
              <p className="text-xs text-success/80 text-center mt-1">
                This helps us match you with volunteers who care about these issues
              </p>
            </div>
            
            {/* Summary */}
            <div className="clip-px border-px border-warning bg-warning/10 p-4">
              <h3 className="font-pixel text-warning text-sm mb-2">🔍 PREVIEW:</h3>
              <div className="text-xs space-y-1">
                <p><strong>Organization:</strong> {orgData.organizationName || 'Not set'}</p>
                <p><strong>Type:</strong> {orgData.organizationType || 'Not set'}</p>
                <p><strong>Location:</strong> {orgData.location || 'Not set'}</p>
                <p><strong>Causes:</strong> {orgData.causeAreas.join(', ') || 'None selected'}</p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (user?.role === 'VOLUNTEER') {
    return null; // Will redirect in useEffect
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <div className="max-w-2xl mx-auto p-6">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-pixel text-primary dark:text-neon-cyan">
                GUILD SETUP
              </h1>
              <div className="text-sm font-pixel text-electric-teal">
                Organization Portal
              </div>
            </div>
            
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-pixel text-white">
                Step {currentStep} of 3
              </span>
              <span className="text-sm font-pixel text-electric-teal">
                {getProgress()}% Complete
              </span>
            </div>
            
            <div className="clip-px bg-dark-surface/20 h-2">
              <div 
                className="bg-gradient-to-r from-sunBurst to-pixel-coral h-full clip-px transition-all duration-500"
                style={{ width: `${getProgress()}%` }}
              />
            </div>
          </div>

          {/* Step Content */}
          <PxCard variant="glow" className="mb-8">
            {renderStep()}
          </PxCard>

          {/* Navigation */}
          <div className="flex justify-between">
            <PxButton
              variant="secondary"
              onClick={prevStep}
              disabled={currentStep === 1}
            >
              ⬅️ Back
            </PxButton>
            
            <PxButton
              variant="primary"
              onClick={nextStep}
              disabled={
                isLoading ||
                (currentStep === 1 && !orgData.organizationName) ||
                (currentStep === 2 && !orgData.description)
              }
            >
              {currentStep === 3 ? (
                isLoading ? '⏳ Creating Guild...' : '🏰 Establish Guild'
              ) : (
                'Next ➡️'
              )}
            </PxButton>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

