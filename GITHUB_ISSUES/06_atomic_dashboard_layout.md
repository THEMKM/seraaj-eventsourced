# Create Gaming-Themed Dashboard with Opportunity Cards

## 📋 **Task Description**
Build the main dashboard page that volunteers see after onboarding. Focus on a gaming aesthetic with opportunity cards showing match scores, quest-style language, and pixel-art design elements.

## 🔍 **Current State**
The dashboard at `apps/web/app/organization/dashboard/page.tsx` exists but is basic. We need to transform it into a hero dashboard for volunteers.

## 🎯 **Exact Steps to Follow**

### Step 1: Read the existing dashboard to understand structure
Use the Read tool to examine `apps/web/app/organization/dashboard/page.tsx` first to understand the current implementation.

### Step 2: Create OpportunityCard component
Create `apps/web/components/dashboard/OpportunityCard.tsx`:

```typescript
import React from 'react';
import { PxButton, PxCard, PxBadge } from '@seraaj/ui';

interface Opportunity {
  id: string;
  opportunityTitle: string;
  organizationName: string;
  location?: string;
  timeCommitment?: string;
  matchScore?: number;
  causes?: string[];
  skillsNeeded?: string[];
  description?: string;
  remoteAllowed?: boolean;
}

interface OpportunityCardProps {
  opportunity: Opportunity;
  onViewDetails: (id: string) => void;
  onQuickApply: (id: string) => void;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onViewDetails,
  onQuickApply
}) => {
  const getMatchScoreColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getMatchScoreText = (score?: number) => {
    if (!score) return 'No Match Data';
    if (score >= 0.8) return 'PERFECT MATCH!';
    if (score >= 0.6) return 'Good Match';
    if (score >= 0.4) return 'Fair Match';
    return 'Low Match';
  };

  return (
    <PxCard className="relative overflow-hidden group hover:scale-105 transition-all duration-300 border-2 border-electric-teal/30 hover:border-electric-teal">
      {/* Match Score Badge */}
      {opportunity.matchScore && (
        <div className="absolute top-4 right-4 z-10">
          <div className={`font-pixel text-sm px-3 py-1 rounded-full bg-dark-surface border-2 ${
            opportunity.matchScore >= 0.8 ? 'border-green-400' : 
            opportunity.matchScore >= 0.6 ? 'border-yellow-400' : 'border-red-400'
          }`}>
            <span className={getMatchScoreColor(opportunity.matchScore)}>
              {Math.round(opportunity.matchScore * 100)}% {getMatchScoreText(opportunity.matchScore)}
            </span>
          </div>
        </div>
      )}

      <div className="p-6">
        {/* Header */}
        <div className="mb-4">
          <h3 className="text-lg font-pixel text-primary mb-2 pr-20">
            🎯 {opportunity.opportunityTitle}
          </h3>
          <p className="text-electric-teal text-sm font-pixel">
            🏰 {opportunity.organizationName}
          </p>
        </div>

        {/* Location & Remote */}
        <div className="flex gap-2 mb-4">
          {opportunity.location && (
            <PxBadge variant="secondary" size="sm">
              📍 {opportunity.location}
            </PxBadge>
          )}
          {opportunity.remoteAllowed && (
            <PxBadge variant="success" size="sm">
              🌐 Remote OK
            </PxBadge>
          )}
          {opportunity.timeCommitment && (
            <PxBadge variant="info" size="sm">
              ⏰ {opportunity.timeCommitment}
            </PxBadge>
          )}
        </div>

        {/* Description */}
        {opportunity.description && (
          <p className="text-gray-300 text-sm mb-4 line-clamp-3">
            {opportunity.description}
          </p>
        )}

        {/* Skills Needed */}
        {opportunity.skillsNeeded && opportunity.skillsNeeded.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-pixel text-electric-teal mb-2">
              🛠️ SKILLS NEEDED:
            </p>
            <div className="flex flex-wrap gap-1">
              {opportunity.skillsNeeded.slice(0, 3).map((skill, index) => (
                <span 
                  key={index}
                  className="text-xs bg-gray-700 text-white px-2 py-1 rounded font-pixel"
                >
                  {skill}
                </span>
              ))}
              {opportunity.skillsNeeded.length > 3 && (
                <span className="text-xs text-gray-400 font-pixel">
                  +{opportunity.skillsNeeded.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Causes */}
        {opportunity.causes && opportunity.causes.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-pixel text-electric-teal mb-2">
              ❤️ CAUSES:
            </p>
            <div className="flex flex-wrap gap-1">
              {opportunity.causes.slice(0, 2).map((cause, index) => (
                <span 
                  key={index}
                  className="text-xs bg-primary/20 text-primary px-2 py-1 rounded font-pixel"
                >
                  {cause}
                </span>
              ))}
              {opportunity.causes.length > 2 && (
                <span className="text-xs text-gray-400 font-pixel">
                  +{opportunity.causes.length - 2} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 mt-6">
          <PxButton 
            variant="secondary" 
            size="sm" 
            onClick={() => onViewDetails(opportunity.id)}
            className="flex-1"
          >
            📋 View Quest
          </PxButton>
          <PxButton 
            variant="primary" 
            size="sm" 
            onClick={() => onQuickApply(opportunity.id)}
            className="flex-1"
          >
            ⚔️ Accept Quest
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
};
```

### Step 3: Create DashboardStats component
Create `apps/web/components/dashboard/DashboardStats.tsx`:

```typescript
import React from 'react';
import { PxCard } from '@seraaj/ui';

interface StatsData {
  totalApplications: number;
  activeApplications: number;
  completedQuests: number;
  impactHours: number;
}

interface DashboardStatsProps {
  stats: StatsData;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <PxCard className="text-center p-4 border-2 border-electric-teal/30">
        <div className="text-2xl font-pixel text-primary mb-1">
          {stats.totalApplications}
        </div>
        <div className="text-sm font-pixel text-electric-teal">
          🎯 TOTAL QUESTS
        </div>
      </PxCard>

      <PxCard className="text-center p-4 border-2 border-yellow-400/30">
        <div className="text-2xl font-pixel text-yellow-400 mb-1">
          {stats.activeApplications}
        </div>
        <div className="text-sm font-pixel text-yellow-400">
          ⚔️ ACTIVE QUESTS
        </div>
      </PxCard>

      <PxCard className="text-center p-4 border-2 border-green-400/30">
        <div className="text-2xl font-pixel text-green-400 mb-1">
          {stats.completedQuests}
        </div>
        <div className="text-sm font-pixel text-green-400">
          ✅ COMPLETED
        </div>
      </PxCard>

      <PxCard className="text-center p-4 border-2 border-purple-400/30">
        <div className="text-2xl font-pixel text-purple-400 mb-1">
          {stats.impactHours}h
        </div>
        <div className="text-sm font-pixel text-purple-400">
          💫 IMPACT HOURS
        </div>
      </PxCard>
    </div>
  );
};
```

### Step 4: Update the dashboard page
Create a new volunteer dashboard at `apps/web/app/dashboard/page.tsx` (note: different from organization dashboard):

```typescript
'use client';

import React, { useEffect, useState } from 'react';
import { Header } from '@/components/navigation/Header';
import { OpportunityCard } from '@/components/dashboard/OpportunityCard';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
import { PxButton, PxLoading, PxCard } from '@seraaj/ui';
import { useRouter } from 'next/navigation';

const DashboardContent = () => {
  const router = useRouter();
  const { opportunities, isLoading, loadQuickMatches } = useOpportunities();
  const [stats, setStats] = useState({
    totalApplications: 0,
    activeApplications: 0,
    completedQuests: 0,
    impactHours: 0
  });

  // Load personalized matches on mount
  useEffect(() => {
    loadQuickMatches(12); // Load 12 personalized matches
  }, [loadQuickMatches]);

  // Mock stats for now - in real implementation, fetch from API
  useEffect(() => {
    setStats({
      totalApplications: 5,
      activeApplications: 2,
      completedQuests: 3,
      impactHours: 47
    });
  }, []);

  const handleViewDetails = (opportunityId: string) => {
    router.push(`/opportunities/${opportunityId}`);
  };

  const handleQuickApply = (opportunityId: string) => {
    // In real implementation, this would open application flow
    router.push(`/opportunities/${opportunityId}/apply`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-7xl mx-auto p-6">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary mb-4">
            🏰 HERO COMMAND CENTER 🏰
          </h1>
          <p className="text-white text-lg mb-6">
            Welcome back, brave hero! Your next epic quest awaits...
          </p>
        </div>

        {/* Stats Dashboard */}
        <DashboardStats stats={stats} />

        {/* Quick Actions */}
        <div className="flex gap-4 mb-8 justify-center">
          <PxButton 
            variant="primary"
            onClick={() => router.push('/opportunities')}
            className="flex items-center gap-2"
          >
            🎯 Browse All Quests
          </PxButton>
          <PxButton 
            variant="secondary"
            onClick={() => router.push('/profile')}
            className="flex items-center gap-2"
          >
            ⚙️ Upgrade Skills
          </PxButton>
          <PxButton 
            variant="secondary"
            onClick={() => router.push('/applications')}
            className="flex items-center gap-2"
          >
            📋 Quest Log
          </PxButton>
        </div>

        {/* Personalized Matches Section */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <h2 className="text-2xl font-pixel text-electric-teal">
              ⚡ PERFECT MATCHES FOR YOU ⚡
            </h2>
            <div className="flex-1 border-b border-electric-teal/30"></div>
            <PxButton 
              variant="secondary" 
              size="sm"
              onClick={() => router.push('/opportunities')}
            >
              See All →
            </PxButton>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <PxLoading size="lg" variant="bright" text="Finding your perfect quests..." />
            </div>
          ) : opportunities.length === 0 ? (
            <PxCard className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-pixel text-primary mb-2">
                NO QUESTS FOUND
              </h3>
              <p className="text-white text-sm mb-4">
                Complete your profile to get personalized quest recommendations!
              </p>
              <PxButton variant="primary" onClick={() => router.push('/profile')}>
                Complete Profile →
              </PxButton>
            </PxCard>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {opportunities.slice(0, 6).map((opportunity) => (
                <OpportunityCard
                  key={opportunity.id}
                  opportunity={opportunity}
                  onViewDetails={handleViewDetails}
                  onQuickApply={handleQuickApply}
                />
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-2xl font-pixel text-electric-teal mb-6">
            📜 RECENT QUEST ACTIVITY 📜
          </h2>
          <PxCard className="p-6">
            <div className="space-y-4">
              {/* Mock recent activity - replace with real data */}
              <div className="flex items-center gap-4 p-3 bg-dark-surface rounded-lg">
                <div className="text-2xl">✅</div>
                <div className="flex-1">
                  <p className="font-pixel text-green-400 text-sm">QUEST COMPLETED</p>
                  <p className="text-white">Community Garden Cleanup</p>
                  <p className="text-gray-400 text-xs">2 days ago • 4 hours contributed</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 p-3 bg-dark-surface rounded-lg">
                <div className="text-2xl">📝</div>
                <div className="flex-1">
                  <p className="font-pixel text-yellow-400 text-sm">APPLICATION SENT</p>
                  <p className="text-white">Youth Mentoring Program</p>
                  <p className="text-gray-400 text-xs">1 week ago • Pending review</p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 bg-dark-surface rounded-lg">
                <div className="text-2xl">🎯</div>
                <div className="flex-1">
                  <p className="font-pixel text-blue-400 text-sm">NEW MATCH FOUND</p>
                  <p className="text-white">Teaching Assistant Role</p>
                  <p className="text-gray-400 text-xs">3 days ago • 95% match</p>
                </div>
              </div>
            </div>
          </PxCard>
        </div>
      </main>
    </div>
  );
};

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
```

### Step 5: Add PxBadge component if needed
If PxBadge doesn't exist, create `packages/ui/src/components/Badge/Badge.tsx`:

```typescript
import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-pixel rounded-full border',
        {
          // Variants
          'bg-primary/20 text-primary border-primary': variant === 'primary',
          'bg-gray-700 text-gray-300 border-gray-600': variant === 'secondary',
          'bg-green-500/20 text-green-400 border-green-400': variant === 'success',
          'bg-yellow-500/20 text-yellow-400 border-yellow-400': variant === 'warning',
          'bg-red-500/20 text-red-400 border-red-400': variant === 'error',
          'bg-blue-500/20 text-blue-400 border-blue-400': variant === 'info',
          // Sizes
          'text-xs px-2 py-1': size === 'sm',
          'text-sm px-3 py-1': size === 'md',
          'text-base px-4 py-2': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
```

Export in `packages/ui/src/index.ts`:
```typescript
export { Badge as PxBadge } from './components/Badge/Badge';
export type { BadgeProps as PxBadgeProps } from './components/Badge/Badge';
```

## ✅ **Definition of Done**
- [ ] OpportunityCard component shows all opportunity details with gaming theme
- [ ] Match scores display with color coding (green/yellow/red)
- [ ] DashboardStats shows hero statistics with pixel styling
- [ ] Dashboard page has gaming aesthetic (command center theme)
- [ ] Quick action buttons navigate to correct pages
- [ ] Recent activity section shows mock data
- [ ] Loading states work correctly
- [ ] Empty states show helpful messaging
- [ ] All components use consistent Px styling
- [ ] Responsive design works on mobile

## 🧪 **How to Test**
1. Navigate to `/dashboard` after login
2. Verify hero command center header appears
3. Check stats cards show numbers and icons
4. Test quick action buttons navigate correctly
5. Verify opportunity cards show match scores
6. Test "Accept Quest" and "View Quest" buttons
7. Check loading and empty states
8. Test responsive design on mobile
9. Verify gaming theme consistency

**This should take 4-5 hours to implement and test thoroughly.**