'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { PxButton, PxCard, PxChip } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { PxSelect } from '@/components/forms/PxSelect';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';

const SKILL_CATEGORIES = {
  'Technical': ['Programming', 'Web Design', 'Data Analysis', 'IT Support', 'Digital Marketing'],
  'Creative': ['Graphic Design', 'Photography', 'Writing', 'Video Editing', 'Art'],
  'Education': ['Teaching', 'Tutoring', 'Training', 'Curriculum Design', 'Mentoring'],
  'Health': ['Medical', 'Counseling', 'First Aid', 'Mental Health', 'Nursing'],
  'Business': ['Project Management', 'Administration', 'Finance', 'Legal', 'HR'],
  'Social': ['Community Outreach', 'Event Planning', 'Fundraising', 'Public Speaking', 'Translation'],
  'Manual': ['Construction', 'Gardening', 'Cooking', 'Cleaning', 'Maintenance']
};

const TIME_COMMITMENTS = [
  { value: 'flexible', label: 'Flexible Schedule' },
  { value: '1-2h-week', label: '1-2 hours per week' },
  { value: '3-5h-week', label: '3-5 hours per week' },
  { value: '6-10h-week', label: '6-10 hours per week' },
  { value: 'weekend-only', label: 'Weekends only' },
  { value: 'one-time', label: 'One-time event' },
  { value: 'ongoing', label: 'Ongoing commitment' }
];

const CATEGORIES = [
  'Education & Youth',
  'Health & Wellness',
  'Environment & Sustainability',
  'Community Development',
  'Arts & Culture',
  'Technology & Innovation',
  'Social Justice & Human Rights',
  'Elderly Care',
  'Animal Welfare',
  'Disaster Relief',
  'Other'
];

interface OpportunityData {
  title: string;
  description: string;
  category: string;
  location: string;
  isRemote: boolean;
  skillsRequired: string[];
  timeCommitment: string;
  startDate: string;
  endDate: string;
  maxVolunteers: number;
  applicationDeadline: string;
  contactEmail: string;
  requirements: string;
  benefits: string;
}

export default function CreateOpportunityPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  
  const [oppData, setOppData] = useState<OpportunityData>({
    title: '',
    description: '',
    category: '',
    location: '',
    isRemote: false,
    skillsRequired: [],
    timeCommitment: '',
    startDate: '',
    endDate: '',
    maxVolunteers: 1,
    applicationDeadline: '',
    contactEmail: user?.email || '',
    requirements: '',
    benefits: ''
  });

  // Redirect volunteers
  useEffect(() => {
    if (user?.role === 'VOLUNTEER') {
      router.push('/dashboard');
    }
  }, [user, router]);

  const updateData = (field: keyof OpportunityData, value: any) => {
    setOppData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const toggleSkill = (skill: string) => {
    setOppData(prev => ({
      ...prev,
      skillsRequired: prev.skillsRequired.includes(skill)
        ? prev.skillsRequired.filter(s => s !== skill)
        : [...prev.skillsRequired, skill]
    }));
  };

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      // Submit via BFF -> Opportunities service
      const bffBase = process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api';
      const response = await fetch(`${bffBase}/opportunities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          organization_id: user?.id,
          title: oppData.title,
          description: oppData.description,
          category: oppData.category || null,
          location: oppData.isRemote ? 'Remote' : oppData.location,
          is_remote: !!oppData.isRemote,
          skills_required: oppData.skillsRequired,
          time_commitment: oppData.timeCommitment || null,
          start_date: oppData.startDate,
          end_date: oppData.endDate || null,
          max_volunteers: oppData.maxVolunteers,
          application_deadline: oppData.applicationDeadline || null,
          contact_email: oppData.contactEmail,
          requirements: oppData.requirements || null,
          benefits: oppData.benefits || null
        })
      });

      if (response.ok) {
        showSuccess('🎆 Quest posted successfully! Heroes can now apply!');
        router.push('/organization/opportunities');
      } else {
        throw new Error('Failed to create opportunity');
      }
    } catch (error) {
      console.error('Failed to create opportunity:', error);
      showError('Failed to create quest. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getProgress = () => Math.round((currentStep / 4) * 100);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">🎯</div>
              <h2 className="text-xl font-pixel text-sunBurst">
                BASIC QUEST DETAILS
              </h2>
              <p className="text-ink dark:text-white text-sm">Start by describing your volunteer opportunity</p>
            </div>
            
            <div className="space-y-4">
              <PxInput
                label="🎯 Quest Title"
                value={oppData.title}
                onChange={(e) => updateData('title', e.target.value)}
                placeholder="e.g., Community Garden Maintenance Helper"
                required
                helperText="Make it engaging and descriptive"
              />
              
              <PxSelect
                label="🏷️ Category"
                value={oppData.category}
                onChange={(e) => updateData('category', e.target.value)}
                options={CATEGORIES.map(cat => ({ value: cat, label: cat }))}
                placeholder="Select a category"
              />
              
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📝 Quest Description
                </label>
                <textarea
                  value={oppData.description}
                  onChange={(e) => updateData('description', e.target.value)}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={5}
                  placeholder="Describe what volunteers will do, why it matters, and what impact they'll make..."
                  required
                />
                <p className="text-xs text-ink/60 dark:text-white/60 mt-1">
                  Be specific about tasks and the impact volunteers will make
                </p>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-4xl mb-2">📍</div>
              <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan">
                LOCATION & REQUIREMENTS
              </h2>
              <p className="text-ink dark:text-white text-sm">Where will heroes serve?</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <PxInput
                    label="📍 Location"
                    value={oppData.location}
                    onChange={(e) => updateData('location', e.target.value)}
                    placeholder="e.g., Downtown Community Center"
                    disabled={oppData.isRemote}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="remote"
                    checked={oppData.isRemote}
                    onChange={(e) => updateData('isRemote', e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label htmlFor="remote" className="text-sm font-pixel text-white">
                    🌐 Remote Quest
                  </label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📝 Additional Requirements (Optional)
                </label>
                <textarea
                  value={oppData.requirements}
                  onChange={(e) => updateData('requirements', e.target.value)}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={3}
                  placeholder="Any special requirements, certifications, or qualifications needed..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  🎁 What Heroes Gain (Optional)
                </label>
                <textarea
                  value={oppData.benefits}
                  onChange={(e) => updateData('benefits', e.target.value)}
                  className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
                  rows={3}
                  placeholder="Skills they'll develop, experience they'll gain, recognition they'll receive..."
                />
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
                REQUIRED SUPERPOWERS
              </h2>
              <p className="text-ink dark:text-white text-sm">What skills do heroes need?</p>
            </div>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {Object.entries(SKILL_CATEGORIES).map(([category, skills]) => (
                <div key={category} className="space-y-2">
                  <h3 className="font-pixel text-sm text-electric-teal">{category.toUpperCase()}</h3>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill) => (
                      <PxChip
                        key={skill}
                        variant={oppData.skillsRequired.includes(skill) ? "selected" : "default"}
                        size="sm"
                        className="cursor-pointer"
                        onClick={() => toggleSkill(skill)}
                      >
                        {oppData.skillsRequired.includes(skill) ? '✅' : '➕'} {skill}
                      </PxChip>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="clip-px border-px border-info bg-info/10 p-3">
              <p className="text-xs text-info font-pixel">
                💡 Selected {oppData.skillsRequired.length} skills - Leave empty if no specific skills required
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
                TIMELINE & LOGISTICS
              </h2>
              <p className="text-ink dark:text-white text-sm">When does the quest begin?</p>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <PxInput
                  label="📅 Start Date"
                  type="date"
                  value={oppData.startDate}
                  onChange={(e) => updateData('startDate', e.target.value)}
                  required
                />
                
                <PxInput
                  label="🏁 End Date (Optional)"
                  type="date"
                  value={oppData.endDate}
                  onChange={(e) => updateData('endDate', e.target.value)}
                  helperText="Leave blank for ongoing"
                />
              </div>
              
              <PxSelect
                label="⏰ Time Commitment"
                value={oppData.timeCommitment}
                onChange={(e) => updateData('timeCommitment', e.target.value)}
                options={TIME_COMMITMENTS}
                placeholder="Select time commitment"
              />
              
              <div className="grid grid-cols-2 gap-4">
                <PxInput
                  label="👥 Max Heroes"
                  type="number"
                  value={oppData.maxVolunteers.toString()}
                  onChange={(e) => updateData('maxVolunteers', parseInt(e.target.value) || 1)}
                  min="1"
                  max="100"
                />
                
                <PxInput
                  label="📋 Application Deadline"
                  type="date"
                  value={oppData.applicationDeadline}
                  onChange={(e) => updateData('applicationDeadline', e.target.value)}
                  helperText="Optional"
                />
              </div>
              
              <PxInput
                label="📧 Contact Email"
                type="email"
                value={oppData.contactEmail}
                onChange={(e) => updateData('contactEmail', e.target.value)}
                required
                helperText="Where heroes can reach you"
              />
            </div>
            
            {/* Summary */}
            <div className="clip-px border-px border-success bg-success/10 p-4">
              <h3 className="font-pixel text-success text-sm mb-2">🎯 QUEST SUMMARY:</h3>
              <div className="text-xs space-y-1">
                <p><strong>Title:</strong> {oppData.title || 'Not set'}</p>
                <p><strong>Category:</strong> {oppData.category || 'Not set'}</p>
                <p><strong>Location:</strong> {oppData.isRemote ? 'Remote' : oppData.location || 'Not set'}</p>
                <p><strong>Skills:</strong> {oppData.skillsRequired.length > 0 ? oppData.skillsRequired.join(', ') : 'None required'}</p>
                <p><strong>Start:</strong> {oppData.startDate || 'Not set'}</p>
                <p><strong>Max Heroes:</strong> {oppData.maxVolunteers}</p>
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
        <Header />
        
        <div className="max-w-2xl mx-auto p-6">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-pixel text-sunBurst">
                CREATE NEW QUEST
              </h1>
              <PxButton
                variant="secondary"
                size="sm"
                onClick={() => router.push('/organization/dashboard')}
              >
                ← Back to Guild
              </PxButton>
            </div>
            
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-pixel text-white">
                Step {currentStep} of 4
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
                (currentStep === 1 && (!oppData.title || !oppData.description)) ||
                (currentStep === 4 && (!oppData.startDate || !oppData.contactEmail))
              }
            >
              {currentStep === 4 ? (
                isLoading ? '⏳ Creating Quest...' : '🚀 Launch Quest'
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
