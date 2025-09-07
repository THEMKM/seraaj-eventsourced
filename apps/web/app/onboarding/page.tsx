'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { useToast } from '@/contexts/ToastContext';
import { PxButton, PxCard, PxChip, PxModal } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { PxSelect } from '@/components/forms/PxSelect';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Onboarding steps data
const ONBOARDING_STEPS = [
  {
    id: 1,
    title: '🎆 WELCOME HERO!',
    subtitle: 'Your epic volunteering adventure begins here',
    icon: '🚀'
  },
  {
    id: 2,
    title: '📝 BASIC PROFILE',
    subtitle: 'Tell us about yourself, hero!',
    icon: '👤'
  },
  {
    id: 3,
    title: '⚡ SKILLS & POWERS',
    subtitle: 'What superpowers do you bring?',
    icon: '💪'
  },
  {
    id: 4,
    title: '📅 AVAILABILITY',
    subtitle: 'When can you save the world?',
    icon: '⏰'
  },
  {
    id: 5,
    title: '🎯 INTERESTS & CAUSES',
    subtitle: 'What causes spark your passion?',
    icon: '❤️'
  }
];

const SKILL_CATEGORIES = {
  'Technical': ['Programming', 'Web Design', 'Data Analysis', 'IT Support', 'Digital Marketing'],
  'Creative': ['Graphic Design', 'Photography', 'Writing', 'Video Editing', 'Art'],
  'Education': ['Teaching', 'Tutoring', 'Training', 'Curriculum Design', 'Mentoring'],
  'Health': ['Medical', 'Counseling', 'First Aid', 'Mental Health', 'Nursing'],
  'Business': ['Project Management', 'Administration', 'Finance', 'Legal', 'HR'],
  'Social': ['Community Outreach', 'Event Planning', 'Fundraising', 'Public Speaking', 'Translation'],
  'Manual': ['Construction', 'Gardening', 'Cooking', 'Cleaning', 'Maintenance']
};

const INTEREST_CATEGORIES = [
  'Education & Youth',
  'Health & Wellness', 
  'Environment & Sustainability',
  'Community Development',
  'Arts & Culture',
  'Technology & Innovation',
  'Social Justice & Human Rights',
  'Elderly Care',
  'Animal Welfare',
  'Disaster Relief'
];

interface OnboardingData {
  location: string;
  bio: string;
  skills: string[];
  availability: {
    weekdays: boolean;
    weekends: boolean;
    evenings: boolean;
  };
  interests: string[];
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user, tokens } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [showSkipModal, setShowSkipModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    location: '',
    bio: '',
    skills: [],
    availability: {
      weekdays: false,
      weekends: false,
      evenings: false
    },
    interests: []
  });

  // Redirect organization users
  useEffect(() => {
    if (user?.role === 'ORG_ADMIN') {
      router.push('/organization/setup');
    }
  }, [user, router]);

  const updateData = (updates: Partial<OnboardingData>) => {
    setOnboardingData(prev => ({
      ...prev,
      ...updates
    }));
  };

  const toggleSkill = (skill: string) => {
    setOnboardingData(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
  };

  const toggleInterest = (interest: string) => {
    setOnboardingData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const nextStep = () => {
    if (currentStep < 5) {
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
      // Save to BFF using authenticated SDK
      if (!user || !user.id) throw new Error('Not authenticated');
      if (!tokens?.accessToken) throw new Error('Missing access token');
      const api = createAuthenticatedVolunteerApi(tokens.accessToken);
      await api.updateVolunteerProfile(user.id, {
        location: onboardingData.location,
        skills: onboardingData.skills,
        interests: onboardingData.interests,
        availability: onboardingData.availability
      });

      showSuccess('🎆 Hero profile complete! Welcome to your adventure!');
      router.push('/dashboard');
    } catch (error) {
      console.error('Onboarding completion failed:', error);
      showError('Failed to save profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    setShowSkipModal(false);
    router.push('/dashboard');
    showSuccess('🚀 Onboarding skipped! You can complete your profile anytime from Settings.');
  };

  const getProgress = () => Math.round((currentStep / 5) * 100);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="text-center space-y-6">
            <div className="text-6xl mb-4">🎆</div>
            <h2 className="text-2xl font-pixel text-sunBurst mb-4">
              WELCOME TO SERAAJ, {user?.name?.toUpperCase()}!
            </h2>
            <div className="space-y-4 text-ink dark:text-white">
              <p className="text-lg">🚀 Ready to make a difference in the world?</p>
              <p>Let's set up your hero profile so we can find the perfect quests for you!</p>
              <div className="clip-px border-px border-electric-teal bg-electric-teal/10 p-4 space-y-2">
                <p className="font-pixel text-electric-teal text-sm">✨ WHAT TO EXPECT:</p>
                <ul className="text-sm space-y-1 text-left">
                  <li>📝 Share your basic info and location</li>
                  <li>⚡ Tell us about your superpowers (skills)</li>
                  <li>📅 Set your availability preferences</li>
                  <li>❤️ Choose causes you care about</li>
                  <li>🎯 Get matched with perfect opportunities!</li>
                </ul>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">👤</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                TELL US ABOUT YOURSELF
              </h2>
              <p className="text-ink dark:text-white text-sm">Help others get to know the hero behind the mask</p>
            </div>
            
            <div className="space-y-4">
              <PxInput
                label="📍 Your Location"
                value={onboardingData.location}
                onChange={(e) => updateData({ location: e.target.value })}
                placeholder="e.g., Cairo, Egypt"
                helperText="This helps us find local opportunities near you"
              />
              
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📝 Tell Your Story (Optional)
                </label>
                <textarea
                  value={onboardingData.bio}
                  onChange={(e) => updateData({ bio: e.target.value })}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={4}
                  placeholder="What motivates you to volunteer? What's your story?"
                />
                <p className="text-xs text-ink/60 dark:text-white/60 mt-1">
                  Share what drives your passion for helping others
                </p>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">⚡</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                YOUR SUPERPOWERS
              </h2>
              <p className="text-ink dark:text-white text-sm">Select skills you can use to help others</p>
            </div>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {Object.entries(SKILL_CATEGORIES).map(([category, skills]) => (
                <div key={category} className="space-y-2">
                  <h3 className="font-pixel text-sm text-electric-teal">{category.toUpperCase()}</h3>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill) => (
                      <PxChip
                        key={skill}
                        variant={onboardingData.skills.includes(skill) ? "selected" : "default"}
                        size="sm"
                        className="cursor-pointer"
                        onClick={() => toggleSkill(skill)}
                      >
                        {onboardingData.skills.includes(skill) ? '✅' : '➕'} {skill}
                      </PxChip>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="clip-px border-px border-warning bg-warning/10 p-3">
              <p className="text-xs text-warning font-pixel">
                💡 Selected {onboardingData.skills.length} skills - Choose at least 3 for better matches!
              </p>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">📅</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                WHEN CAN YOU SAVE THE WORLD?
              </h2>
              <p className="text-ink dark:text-white text-sm">Set your availability preferences</p>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div 
                  className={`clip-px border-px p-4 cursor-pointer transition-all ${
                    onboardingData.availability.weekdays 
                      ? 'border-success bg-success/20' 
                      : 'border-electric-teal bg-dark-surface/20 hover:bg-electric-teal/10'
                  }`}
                  onClick={() => updateData({
                    availability: {
                      ...onboardingData.availability,
                      weekdays: !onboardingData.availability.weekdays
                    }
                  })}
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">
                      {onboardingData.availability.weekdays ? '✅' : '📅'}
                    </div>
                    <div>
                      <h3 className="font-pixel text-sm text-ink dark:text-white">WEEKDAYS</h3>
                      <p className="text-xs text-ink/60 dark:text-white/60">Monday - Friday</p>
                    </div>
                  </div>
                </div>

                <div 
                  className={`clip-px border-px p-4 cursor-pointer transition-all ${
                    onboardingData.availability.weekends 
                      ? 'border-success bg-success/20' 
                      : 'border-electric-teal bg-dark-surface/20 hover:bg-electric-teal/10'
                  }`}
                  onClick={() => updateData({
                    availability: {
                      ...onboardingData.availability,
                      weekends: !onboardingData.availability.weekends
                    }
                  })}
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">
                      {onboardingData.availability.weekends ? '✅' : '🏖️'}
                    </div>
                    <div>
                      <h3 className="font-pixel text-sm text-ink dark:text-white">WEEKENDS</h3>
                      <p className="text-xs text-ink/60 dark:text-white/60">Saturday - Sunday</p>
                    </div>
                  </div>
                </div>

                <div 
                  className={`clip-px border-px p-4 cursor-pointer transition-all ${
                    onboardingData.availability.evenings 
                      ? 'border-success bg-success/20' 
                      : 'border-electric-teal bg-dark-surface/20 hover:bg-electric-teal/10'
                  }`}
                  onClick={() => updateData({
                    availability: {
                      ...onboardingData.availability,
                      evenings: !onboardingData.availability.evenings
                    }
                  })}
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">
                      {onboardingData.availability.evenings ? '✅' : '🌙'}
                    </div>
                    <div>
                      <h3 className="font-pixel text-sm text-ink dark:text-white">EVENINGS</h3>
                      <p className="text-xs text-ink/60 dark:text-white/60">After work/school hours</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">❤️</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                CAUSES CLOSE TO YOUR HEART
              </h2>
              <p className="text-ink dark:text-white text-sm">What issues do you want to help solve?</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3">
                {INTEREST_CATEGORIES.map((interest) => (
                  <PxChip
                    key={interest}
                    variant={onboardingData.interests.includes(interest) ? "selected" : "default"}
                    size="sm"
                    className="cursor-pointer"
                    onClick={() => toggleInterest(interest)}
                  >
                    {onboardingData.interests.includes(interest) ? '❤️' : '🤍'} {interest}
                  </PxChip>
                ))}
              </div>
            </div>
            
            <div className="clip-px border-px border-success bg-success/10 p-4">
              <p className="text-sm text-success font-pixel text-center">
                🎆 ALMOST DONE! Selected {onboardingData.interests.length} interests
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (user?.role === 'ORG_ADMIN') {
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
                HERO SETUP
              </h1>
              <PxButton
                variant="secondary"
                size="sm"
                onClick={() => setShowSkipModal(true)}
              >
                ⏭️ Skip for Now
              </PxButton>
            </div>
            
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-pixel text-white">
                Step {currentStep} of 5
              </span>
              <span className="text-sm font-pixel text-electric-teal">
                {getProgress()}% Complete
              </span>
            </div>
            
            <div className="clip-px bg-dark-surface/20 h-2">
              <div 
                className="bg-gradient-to-r from-electric-teal to-neon-cyan h-full clip-px transition-all duration-500"
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
              disabled={isLoading}
            >
              {currentStep === 5 ? (
                isLoading ? '⏳ Saving...' : '✨ Complete Setup'
              ) : (
                'Next ➡️'
              )}
            </PxButton>
          </div>
        </div>

        {/* Skip Confirmation Modal */}
        <PxModal
          isOpen={showSkipModal}
          onClose={() => setShowSkipModal(false)}
          title="⏭️ SKIP ONBOARDING?"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-sm">
              You can complete your hero profile later from the Settings page.
            </p>
            <p className="text-sm text-warning">
              ⚠️ Incomplete profiles get fewer quest matches!
            </p>
            <div className="flex space-x-3">
              <PxButton
                variant="warning"
                onClick={handleSkip}
              >
                Skip Anyway
              </PxButton>
              <PxButton
                variant="primary"
                onClick={() => setShowSkipModal(false)}
              >
                Continue Setup
              </PxButton>
            </div>
          </div>
        </PxModal>
      </div>
    </ProtectedRoute>
  );
}

