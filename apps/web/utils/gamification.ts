import { VolunteerDashboardResponse } from '@seraaj/sdk-bff';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  earnedAt: Date | null;
  progress?: number;
  requirement?: number;
}

// XP calculation constants
const XP_PER_APPLICATION = 50;
const XP_PER_APPROVED_APPLICATION = 100;
const XP_PER_COMPLETED_APPLICATION = 200;
const XP_PER_SKILL = 25;

// Level calculation - exponential growth
export function calculateLevel(totalXP: number): number {
  return Math.floor(Math.log2(Math.max(1, totalXP / 100)) + 1);
}

export function getXPForNextLevel(currentLevel: number): number {
  return Math.pow(2, currentLevel) * 100;
}

// Calculate total XP from dashboard data
export function calculateTotalXP(dashboard: VolunteerDashboardResponse): number {
  let totalXP = 0;

  // Base XP from profile skills
  if (dashboard.profile?.skills) {
    totalXP += dashboard.profile.skills.length * XP_PER_SKILL;
  }

  // XP from applications (including active and past)
  if (dashboard.activeApplications) {
    dashboard.activeApplications.forEach(app => {
      totalXP += XP_PER_APPLICATION;
      
      if (app.status === 'approved') {
        totalXP += XP_PER_APPROVED_APPLICATION;
      }
      
      // Assuming completed applications would have a different status
      // This could be enhanced when historical application data is available
    });
  }

  return totalXP;
}

// Generate achievements based on real data
export function generateAchievements(dashboard: VolunteerDashboardResponse): Achievement[] {
  const applications = dashboard.activeApplications || [];
  const skills = dashboard.profile?.skills || [];
  const totalApplications = (dashboard.profile?.completedApplications || 0) + applications.length;
  const approvedApplications = applications.filter(app => app.status === 'approved').length;

  const now = new Date();
  const achievements: Achievement[] = [
    // First steps achievements
    {
      id: 'welcome',
      name: 'Welcome Hero',
      description: 'Created your volunteer profile',
      icon: '🎉',
      earnedAt: dashboard.profile ? new Date(dashboard.profile.createdAt || now) : null
    },
    {
      id: 'first_application',
      name: 'Quest Seeker',
      description: 'Submit your first application',
      icon: '📝',
      earnedAt: totalApplications > 0 ? now : null,
      progress: totalApplications > 0 ? 100 : 0,
      requirement: 1
    },
    {
      id: 'skill_collector',
      name: 'Skill Collector',
      description: 'Add 3 skills to your profile',
      icon: '⚡',
      earnedAt: skills.length >= 3 ? now : null,
      progress: Math.min(100, (skills.length / 3) * 100),
      requirement: 3
    },
    
    // Application achievements
    {
      id: 'applicant_bronze',
      name: 'Bronze Applicant',
      description: 'Submit 5 applications',
      icon: '🥉',
      earnedAt: totalApplications >= 5 ? now : null,
      progress: Math.min(100, (totalApplications / 5) * 100),
      requirement: 5
    },
    {
      id: 'applicant_silver',
      name: 'Silver Applicant',
      description: 'Submit 10 applications',
      icon: '🥈',
      earnedAt: totalApplications >= 10 ? now : null,
      progress: Math.min(100, (totalApplications / 10) * 100),
      requirement: 10
    },
    {
      id: 'applicant_gold',
      name: 'Gold Applicant',
      description: 'Submit 25 applications',
      icon: '🥇',
      earnedAt: totalApplications >= 25 ? now : null,
      progress: Math.min(100, (totalApplications / 25) * 100),
      requirement: 25
    },
    
    // Success achievements
    {
      id: 'first_approval',
      name: 'First Success',
      description: 'Get your first application approved',
      icon: '✨',
      earnedAt: approvedApplications > 0 ? now : null,
      progress: approvedApplications > 0 ? 100 : 0,
      requirement: 1
    },
    {
      id: 'trusted_volunteer',
      name: 'Trusted Volunteer',
      description: 'Get 5 applications approved',
      icon: '🌟',
      earnedAt: approvedApplications >= 5 ? now : null,
      progress: Math.min(100, (approvedApplications / 5) * 100),
      requirement: 5
    },
    
    // Special achievements
    {
      id: 'early_adopter',
      name: 'Early Adopter',
      description: 'One of the first volunteers on Seraaj',
      icon: '🚀',
      earnedAt: dashboard.profile ? now : null // Everyone gets this for being part of the beta
    }
  ];

  return achievements.sort((a, b) => {
    // Sort by earned status, then by progress
    if (a.earnedAt && !b.earnedAt) return -1;
    if (!a.earnedAt && b.earnedAt) return 1;
    if (a.earnedAt && b.earnedAt) return b.earnedAt.getTime() - a.earnedAt.getTime();
    return (b.progress || 0) - (a.progress || 0);
  });
}

// Generate impact stats for dashboard
export function calculateImpactStats(dashboard: VolunteerDashboardResponse) {
  const applications = dashboard.activeApplications || [];
  const totalApplications = (dashboard.profile?.completedApplications || 0) + applications.length;
  const approvedApplications = applications.filter(app => app.status === 'approved').length;
  const pendingApplications = applications.filter(app => app.status === 'pending').length;
  
  // Estimate impact based on applications
  const estimatedHoursPerApplication = 20; // Average volunteer hours per opportunity
  const estimatedHours = approvedApplications * estimatedHoursPerApplication;
  
  return {
    totalApplications,
    approvedApplications,
    pendingApplications,
    estimatedVolunteerHours: estimatedHours,
    organizationsHelped: new Set(applications.map(app => app.opportunityId)).size, // Unique opportunities
    impactScore: Math.min(999, totalApplications * 10 + approvedApplications * 25)
  };
}

// Calculate impact level from impact score and total applications
export function calculateImpactLevel(impactScore: number, totalApplications: number): string {
  if (totalApplications >= 25 && impactScore >= 500) return 'LEGENDARY';
  if (totalApplications >= 15 && impactScore >= 300) return 'EXPERT';
  if (totalApplications >= 8 && impactScore >= 150) return 'VETERAN';
  if (totalApplications >= 3 && impactScore >= 50) return 'EXPERIENCED';
  if (totalApplications >= 1) return 'ACTIVE';
  return 'NEWCOMER';
}