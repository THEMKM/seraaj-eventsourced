# Build Application Workflow System

## 📋 **Task Description**
Create the complete application workflow allowing volunteers to apply for opportunities and track application status. Includes application form, status tracking, and quest log interface.

## 🔍 **Current State**
No application system exists. Need to build from scratch with gaming theme and event-driven architecture.

## 🎯 **Exact Steps to Follow**

### Step 1: Examine existing BFF structure
Use Read tool to examine `bff/main.py` to understand how to add new application endpoints.

### Step 2: Create ApplicationForm component  
Create `apps/web/components/applications/ApplicationForm.tsx`:

```typescript
import React, { useState } from 'react';
import { PxButton, PxCard, PxInput } from '@seraaj/ui';

interface ApplicationData {
  opportunityId: string;
  motivationLetter: string;
  availableHours: string;
  startDate: string;
  relevantExperience: string;
  questions: Record<string, string>;
}

interface ApplicationFormProps {
  opportunityId: string;
  opportunityTitle: string;
  organizationName: string;
  customQuestions?: Array<{
    id: string;
    question: string;
    required: boolean;
    type: 'text' | 'textarea' | 'select';
    options?: string[];
  }>;
  onSubmit: (data: ApplicationData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export const ApplicationForm: React.FC<ApplicationFormProps> = ({
  opportunityId,
  opportunityTitle,
  organizationName,
  customQuestions = [],
  onSubmit,
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState<ApplicationData>({
    opportunityId,
    motivationLetter: '',
    availableHours: '',
    startDate: '',
    relevantExperience: '',
    questions: {}
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.motivationLetter.trim()) {
      newErrors.motivationLetter = 'Please tell us why you want this quest';
    }

    if (!formData.availableHours) {
      newErrors.availableHours = 'Please specify your availability';
    }

    if (!formData.startDate) {
      newErrors.startDate = 'Please choose when you can start';
    }

    // Validate custom questions
    customQuestions.forEach(q => {
      if (q.required && !formData.questions[q.id]?.trim()) {
        newErrors[`question_${q.id}`] = 'This field is required';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const updateFormData = (field: keyof ApplicationData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const updateCustomQuestion = (questionId: string, answer: string) => {
    setFormData(prev => ({
      ...prev,
      questions: { ...prev.questions, [questionId]: answer }
    }));
    if (errors[`question_${questionId}`]) {
      setErrors(prev => ({ ...prev, [`question_${questionId}`]: '' }));
    }
  };

  return (
    <PxCard className="max-w-3xl mx-auto p-8">
      <div className="text-center mb-8">
        <div className="text-6xl mb-4">⚔️</div>
        <h2 className="text-2xl font-pixel text-primary mb-2">
          ACCEPT QUEST
        </h2>
        <h3 className="text-xl text-electric-teal mb-2">
          {opportunityTitle}
        </h3>
        <p className="text-gray-300">
          at <span className="text-white font-pixel">{organizationName}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Motivation Letter */}
        <div>
          <label className="block text-sm font-pixel text-electric-teal mb-2">
            💫 Why do you want this quest? *
          </label>
          <textarea
            value={formData.motivationLetter}
            onChange={(e) => updateFormData('motivationLetter', e.target.value)}
            rows={4}
            className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg resize-none"
            placeholder="Tell the quest giver why you're the perfect hero for this mission..."
          />
          {errors.motivationLetter && (
            <p className="text-red-400 text-sm mt-1">{errors.motivationLetter}</p>
          )}
        </div>

        {/* Available Hours */}
        <div>
          <label className="block text-sm font-pixel text-electric-teal mb-2">
            ⏰ How many hours per week can you commit? *
          </label>
          <select
            value={formData.availableHours}
            onChange={(e) => updateFormData('availableHours', e.target.value)}
            className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
          >
            <option value="">Select your availability</option>
            <option value="1-2">1-2 hours/week</option>
            <option value="3-5">3-5 hours/week</option>
            <option value="6-10">6-10 hours/week</option>
            <option value="10+">10+ hours/week</option>
            <option value="flexible">Flexible schedule</option>
          </select>
          {errors.availableHours && (
            <p className="text-red-400 text-sm mt-1">{errors.availableHours}</p>
          )}
        </div>

        {/* Start Date */}
        <div>
          <label className="block text-sm font-pixel text-electric-teal mb-2">
            📅 When can you start your quest? *
          </label>
          <input
            type="date"
            value={formData.startDate}
            onChange={(e) => updateFormData('startDate', e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
          />
          {errors.startDate && (
            <p className="text-red-400 text-sm mt-1">{errors.startDate}</p>
          )}
        </div>

        {/* Relevant Experience */}
        <div>
          <label className="block text-sm font-pixel text-electric-teal mb-2">
            🛠️ Relevant Experience (Optional)
          </label>
          <textarea
            value={formData.relevantExperience}
            onChange={(e) => updateFormData('relevantExperience', e.target.value)}
            rows={3}
            className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg resize-none"
            placeholder="Describe any relevant experience, skills, or previous quests..."
          />
        </div>

        {/* Custom Questions */}
        {customQuestions.map((question) => (
          <div key={question.id}>
            <label className="block text-sm font-pixel text-electric-teal mb-2">
              ❓ {question.question} {question.required && '*'}
            </label>
            {question.type === 'textarea' ? (
              <textarea
                value={formData.questions[question.id] || ''}
                onChange={(e) => updateCustomQuestion(question.id, e.target.value)}
                rows={3}
                className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg resize-none"
              />
            ) : question.type === 'select' ? (
              <select
                value={formData.questions[question.id] || ''}
                onChange={(e) => updateCustomQuestion(question.id, e.target.value)}
                className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
              >
                <option value="">Select an option</option>
                {question.options?.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={formData.questions[question.id] || ''}
                onChange={(e) => updateCustomQuestion(question.id, e.target.value)}
                className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
              />
            )}
            {errors[`question_${question.id}`] && (
              <p className="text-red-400 text-sm mt-1">{errors[`question_${question.id}`]}</p>
            )}
          </div>
        ))}

        {/* Action Buttons */}
        <div className="flex gap-4 pt-6 border-t border-electric-teal/30">
          <PxButton
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1"
          >
            🚪 Cancel Quest
          </PxButton>
          <PxButton
            type="submit"
            variant="primary"
            loading={isSubmitting}
            className="flex-1"
          >
            ⚔️ Submit Application
          </PxButton>
        </div>
      </form>
    </PxCard>
  );
};
```

### Step 3: Create ApplicationStatusCard component
Create `apps/web/components/applications/ApplicationStatusCard.tsx`:

```typescript
import React from 'react';
import { PxCard, PxBadge, PxButton } from '@seraaj/ui';

interface Application {
  id: string;
  opportunityId: string;
  opportunityTitle: string;
  organizationName: string;
  status: 'pending' | 'reviewing' | 'accepted' | 'rejected' | 'completed';
  appliedDate: string;
  responseDate?: string;
  message?: string;
}

interface ApplicationStatusCardProps {
  application: Application;
  onViewDetails: (id: string) => void;
  onWithdraw?: (id: string) => void;
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'pending':
      return {
        badge: 'warning' as const,
        icon: '⏳',
        text: 'PENDING REVIEW',
        description: 'Quest giver is reviewing your application'
      };
    case 'reviewing':
      return {
        badge: 'info' as const,
        icon: '👀',
        text: 'UNDER REVIEW',
        description: 'Your heroic credentials are being evaluated'
      };
    case 'accepted':
      return {
        badge: 'success' as const,
        icon: '✅',
        text: 'QUEST ACCEPTED',
        description: 'Congratulations! Your quest begins soon'
      };
    case 'rejected':
      return {
        badge: 'error' as const,
        icon: '❌',
        text: 'QUEST DECLINED',
        description: 'This quest was not a match, but keep exploring'
      };
    case 'completed':
      return {
        badge: 'success' as const,
        icon: '🏆',
        text: 'QUEST COMPLETED',
        description: 'Well done, hero! Quest successfully completed'
      };
    default:
      return {
        badge: 'secondary' as const,
        icon: '❓',
        text: 'UNKNOWN STATUS',
        description: 'Status unclear'
      };
  }
};

export const ApplicationStatusCard: React.FC<ApplicationStatusCardProps> = ({
  application,
  onViewDetails,
  onWithdraw
}) => {
  const statusConfig = getStatusConfig(application.status);
  const appliedDate = new Date(application.appliedDate).toLocaleDateString();
  const responseDate = application.responseDate ? new Date(application.responseDate).toLocaleDateString() : null;

  return (
    <PxCard className="p-6 border-2 border-electric-teal/30 hover:border-electric-teal transition-all">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-pixel text-primary mb-2">
            🎯 {application.opportunityTitle}
          </h3>
          <p className="text-electric-teal text-sm font-pixel mb-2">
            🏰 {application.organizationName}
          </p>
          <p className="text-gray-400 text-sm">
            Applied: {appliedDate}
          </p>
        </div>
        
        <PxBadge variant={statusConfig.badge} size="md">
          {statusConfig.icon} {statusConfig.text}
        </PxBadge>
      </div>

      <p className="text-gray-300 text-sm mb-4">
        {statusConfig.description}
      </p>

      {responseDate && (
        <p className="text-gray-400 text-xs mb-4">
          Response received: {responseDate}
        </p>
      )}

      {application.message && (
        <div className="bg-dark-surface p-4 rounded-lg mb-4">
          <p className="text-sm font-pixel text-electric-teal mb-2">
            📝 MESSAGE FROM QUEST GIVER:
          </p>
          <p className="text-white text-sm">{application.message}</p>
        </div>
      )}

      <div className="flex gap-3">
        <PxButton
          variant="secondary"
          size="sm"
          onClick={() => onViewDetails(application.id)}
          className="flex-1"
        >
          📋 View Details
        </PxButton>
        
        {(application.status === 'pending' || application.status === 'reviewing') && onWithdraw && (
          <PxButton
            variant="error"
            size="sm"
            onClick={() => onWithdraw(application.id)}
            className="flex-1"
          >
            🚪 Withdraw
          </PxButton>
        )}
        
        {application.status === 'accepted' && (
          <PxButton
            variant="success"
            size="sm"
            onClick={() => onViewDetails(application.id)}
            className="flex-1"
          >
            🚀 Start Quest
          </PxButton>
        )}
      </div>
    </PxCard>
  );
};
```

### Step 4: Create Applications page (Quest Log)
Create `apps/web/app/applications/page.tsx`:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/navigation/Header';
import { ApplicationStatusCard } from '@/components/applications/ApplicationStatusCard';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PxLoading, PxCard, PxButton } from '@seraaj/ui';
import { useRouter } from 'next/navigation';

// Mock application data - replace with real API calls
const mockApplications = [
  {
    id: '1',
    opportunityId: 'opp-1',
    opportunityTitle: 'Community Garden Mentor',
    organizationName: 'Green Earth Initiative',
    status: 'accepted' as const,
    appliedDate: '2024-01-15',
    responseDate: '2024-01-18',
    message: 'Welcome to the team! We are excited to have you help with our community garden project. Please report to the main entrance this Saturday at 9 AM.'
  },
  {
    id: '2',
    opportunityId: 'opp-2',
    opportunityTitle: 'Youth Coding Workshop Assistant',
    organizationName: 'Tech for Tomorrow',
    status: 'reviewing' as const,
    appliedDate: '2024-01-20'
  },
  {
    id: '3',
    opportunityId: 'opp-3',
    opportunityTitle: 'Food Bank Volunteer',
    organizationName: 'Helping Hands',
    status: 'completed' as const,
    appliedDate: '2023-12-01',
    responseDate: '2023-12-03',
    message: 'Thank you for your incredible dedication! You helped distribute food to over 200 families.'
  }
];

const ApplicationsContent = () => {
  const router = useRouter();
  const [applications, setApplications] = useState(mockApplications);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending' | 'accepted' | 'completed'>('all');

  const filteredApplications = applications.filter(app => {
    if (filter === 'all') return true;
    if (filter === 'pending') return app.status === 'pending' || app.status === 'reviewing';
    return app.status === filter;
  });

  const handleViewDetails = (applicationId: string) => {
    // Navigate to application details or opportunity page
    const application = applications.find(app => app.id === applicationId);
    if (application) {
      router.push(`/opportunities/${application.opportunityId}`);
    }
  };

  const handleWithdraw = (applicationId: string) => {
    // In real implementation, call API to withdraw application
    setApplications(prev => 
      prev.filter(app => app.id !== applicationId)
    );
  };

  const getStatusCounts = () => {
    return {
      all: applications.length,
      pending: applications.filter(app => app.status === 'pending' || app.status === 'reviewing').length,
      accepted: applications.filter(app => app.status === 'accepted').length,
      completed: applications.filter(app => app.status === 'completed').length,
    };
  };

  const counts = getStatusCounts();

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-6xl mx-auto p-6">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary mb-4">
            📜 QUEST LOG 📜
          </h1>
          <p className="text-white text-lg">
            Track all your heroic adventures and application status
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-8 justify-center flex-wrap">
          <PxButton
            variant={filter === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            📋 All Quests ({counts.all})
          </PxButton>
          <PxButton
            variant={filter === 'pending' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('pending')}
          >
            ⏳ Pending ({counts.pending})
          </PxButton>
          <PxButton
            variant={filter === 'accepted' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('accepted')}
          >
            ✅ Accepted ({counts.accepted})
          </PxButton>
          <PxButton
            variant={filter === 'completed' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('completed')}
          >
            🏆 Completed ({counts.completed})
          </PxButton>
        </div>

        {/* Applications List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <PxLoading size="lg" variant="bright" text="Loading your quest log..." />
          </div>
        ) : filteredApplications.length === 0 ? (
          <PxCard className="text-center py-12">
            <div className="text-6xl mb-4">
              {filter === 'all' ? '🔍' : '📭'}
            </div>
            <h3 className="text-lg font-pixel text-primary mb-2">
              {filter === 'all' ? 'NO QUESTS IN YOUR LOG' : `NO ${filter.toUpperCase()} QUESTS`}
            </h3>
            <p className="text-white text-sm mb-4">
              {filter === 'all' 
                ? 'Start your heroic journey by applying to opportunities!'
                : `No ${filter} applications found. Try a different filter.`
              }
            </p>
            {filter === 'all' && (
              <PxButton variant="primary" onClick={() => router.push('/opportunities')}>
                🎯 Find Quests →
              </PxButton>
            )}
          </PxCard>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-1">
            {filteredApplications.map((application) => (
              <ApplicationStatusCard
                key={application.id}
                application={application}
                onViewDetails={handleViewDetails}
                onWithdraw={handleWithdraw}
              />
            ))}
          </div>
        )}

        {/* Quick Action */}
        {applications.length > 0 && (
          <div className="text-center mt-12">
            <PxButton
              variant="primary"
              size="lg"
              onClick={() => router.push('/opportunities')}
              className="animate-pulse"
            >
              🎯 Find More Epic Quests
            </PxButton>
          </div>
        )}
      </main>
    </div>
  );
};

export default function ApplicationsPage() {
  return (
    <ProtectedRoute>
      <ApplicationsContent />
    </ProtectedRoute>
  );
}
```

### Step 5: Create Apply page for specific opportunities
Create `apps/web/app/opportunities/[id]/apply/page.tsx`:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/navigation/Header';
import { ApplicationForm } from '@/components/applications/ApplicationForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PxLoading, PxCard } from '@seraaj/ui';
import { useRouter, useParams } from 'next/navigation';

const ApplyPageContent = () => {
  const router = useRouter();
  const params = useParams();
  const opportunityId = params.id as string;
  
  const [opportunity, setOpportunity] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Mock opportunity data - replace with real API call
  useEffect(() => {
    const mockOpportunity = {
      id: opportunityId,
      title: 'Community Garden Mentor',
      organizationName: 'Green Earth Initiative',
      customQuestions: [
        {
          id: 'experience',
          question: 'Do you have experience with gardening or agriculture?',
          required: true,
          type: 'textarea' as const
        },
        {
          id: 'transport',
          question: 'Do you have reliable transportation?',
          required: true,
          type: 'select' as const,
          options: ['Yes, I have my own car', 'Yes, public transport', 'No, but can arrange', 'No']
        }
      ]
    };
    
    setTimeout(() => {
      setOpportunity(mockOpportunity);
      setIsLoading(false);
    }, 1000);
  }, [opportunityId]);

  const handleSubmit = async (applicationData: any) => {
    setIsSubmitting(true);
    
    try {
      // Mock API call - replace with real submission
      console.log('Submitting application:', applicationData);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Redirect to applications page with success message
      router.push('/applications?success=true');
    } catch (error) {
      console.error('Application submission failed:', error);
      // Handle error state
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        <div className="flex justify-center items-center py-24">
          <PxLoading size="lg" variant="bright" text="Preparing quest application..." />
        </div>
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        <div className="flex justify-center items-center py-24">
          <PxCard className="text-center p-8">
            <div className="text-6xl mb-4">❌</div>
            <h2 className="text-xl font-pixel text-primary mb-2">
              QUEST NOT FOUND
            </h2>
            <p className="text-white mb-4">
              This opportunity no longer exists or has been removed.
            </p>
          </PxCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      <div className="py-8">
        <ApplicationForm
          opportunityId={opportunity.id}
          opportunityTitle={opportunity.title}
          organizationName={opportunity.organizationName}
          customQuestions={opportunity.customQuestions}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  );
};

export default function ApplyPage() {
  return (
    <ProtectedRoute>
      <ApplyPageContent />
    </ProtectedRoute>
  );
}
```

## ✅ **Definition of Done**
- [ ] ApplicationForm component collects all required application data
- [ ] Form validation works for required fields
- [ ] Custom questions from organizations display correctly
- [ ] ApplicationStatusCard shows all application statuses with proper styling
- [ ] Applications page (Quest Log) shows filtered applications
- [ ] Status filtering works (All, Pending, Accepted, Completed)
- [ ] Apply page loads opportunity details and shows form
- [ ] Application submission redirects to applications page
- [ ] Gaming theme consistent throughout (quest language, icons)
- [ ] Empty states show helpful messages
- [ ] Loading states work correctly

## 🧪 **How to Test**
1. Navigate to an opportunity and click "Accept Quest"
2. Fill out application form with validation testing
3. Submit application and verify redirect to quest log
4. Check applications page shows submitted application
5. Test status filtering on applications page
6. Test withdraw functionality for pending applications
7. Verify gaming theme and quest language throughout
8. Test form validation and error states
9. Check responsive design on mobile

**This should take 5-6 hours to implement and test thoroughly.**