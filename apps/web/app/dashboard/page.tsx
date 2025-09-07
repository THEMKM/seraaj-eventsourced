'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
import { useToast } from '@/contexts/ToastContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard, PxChip, PxLoading, PxModal } from '@seraaj/ui';
import { createAuthenticatedVolunteerApi } from '@/lib/bff';
import { VolunteerDashboardResponse } from '@seraaj/sdk-bff';
import { XPProgressBar } from '@/components/dashboard/XPProgressBar';
import { AchievementBadge, Achievement } from '@/components/dashboard/AchievementBadge';
import { calculateTotalXP, calculateLevel, getXPForNextLevel, generateAchievements, calculateImpactStats } from '@/utils/gamification';
import { AvatarDisplay, AvatarSelector } from '@/components/avatar/AvatarSelector';
import { AvatarConfig, AvatarClass, AvatarPose, calculateAvatarClass, getUnlockedAccessories } from '@/components/avatar/AvatarSystem';

export default function DashboardPage() {
  const { user, tokens } = useAuth();
  const { opportunities, isLoading: opportunitiesLoading, loadQuickMatches, applyToOpportunity, isApplying } = useOpportunities();
  const { showError } = useToast();
  const [dashboard, setDashboard] = useState<VolunteerDashboardResponse | null>(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
  const [applicationMessage, setApplicationMessage] = useState('');
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [gamificationData, setGamificationData] = useState<{
    totalXP: number;
    level: number;
    nextLevelXP: number;
    impactStats: ReturnType<typeof calculateImpactStats>;
  } | null>(null);
  const [avatarConfig, setAvatarConfig] = useState<AvatarConfig | null>(null);
  const [isAvatarSelectorOpen, setIsAvatarSelectorOpen] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      if (!user || !tokens?.accessToken) return;

      try {
        setIsLoadingDashboard(true);
        const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
        const dashboardData = await volunteerApi.getVolunteerDashboard(user.id);
        setDashboard(dashboardData);

        // Calculate gamification data
        const totalXP = calculateTotalXP(dashboardData);
        const level = calculateLevel(totalXP);
        const nextLevelXP = getXPForNextLevel(level);
        const impactStats = calculateImpactStats(dashboardData);
        
        setGamificationData({ totalXP, level, nextLevelXP, impactStats });
        setAchievements(generateAchievements(dashboardData));

        // Initialize avatar configuration
        const avatarClass = calculateAvatarClass(level, generateAchievements(dashboardData));
        const unlockedAccessories = getUnlockedAccessories(generateAchievements(dashboardData), level);
        const defaultAvatarConfig: AvatarConfig = {
          class: avatarClass,
          level: level,
          pose: AvatarPose.DEFAULT,
          accessories: unlockedAccessories.slice(0, 2) // Show first 2 unlocked accessories
        };
        setAvatarConfig(defaultAvatarConfig);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
        showError('Failed to load dashboard data');
      } finally {
        setIsLoadingDashboard(false);
      }
    };

    loadDashboard();
  }, [user, tokens, showError]);

  const handleQuickMatch = async () => {
    await loadQuickMatches(8);
  };

  const handleApply = (opportunityId: string) => {
    setSelectedOpportunityId(opportunityId);
    setApplicationMessage('I am interested in this opportunity and would like to help! I believe my skills and passion align well with this cause.');
  };

  const handleConfirmApplication = async () => {
    if (!selectedOpportunityId) return;
    
    await applyToOpportunity(selectedOpportunityId, applicationMessage);
    setSelectedOpportunityId(null);
    setApplicationMessage('');
    
    // Reload dashboard to show new application
    if (user && tokens?.accessToken) {
      try {
        const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
        const dashboardData = await volunteerApi.getVolunteerDashboard(user.id);
        setDashboard(dashboardData);

        // Recalculate gamification data
        const totalXP = calculateTotalXP(dashboardData);
        const level = calculateLevel(totalXP);
        const nextLevelXP = getXPForNextLevel(level);
        const impactStats = calculateImpactStats(dashboardData);
        
        setGamificationData({ totalXP, level, nextLevelXP, impactStats });
        setAchievements(generateAchievements(dashboardData));
      } catch (error) {
        console.error('Failed to reload dashboard:', error);
      }
    }
  };

  const handleAvatarSave = (newConfig: AvatarConfig) => {
    setAvatarConfig(newConfig);
    // TODO: Save avatar config to user profile/preferences
    console.log('Avatar saved:', newConfig);
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        
        <main className="max-w-6xl mx-auto p-6">
          <div className="mb-8">
            <div className="flex items-center gap-6 mb-4">
              <div>
                <h1 className="text-3xl font-pixel text-primary dark:text-neon-cyan mb-2">
                  🏆 HERO DASHBOARD 🏆
                </h1>
                <p className="text-white text-lg">
                  Welcome back, <span className="text-pixel-coral font-pixel">{user?.name?.toUpperCase()}</span>! 
                  🚀 Ready for your next quest?
                </p>
              </div>
              
              {/* Avatar Display */}
              {avatarConfig && gamificationData && !isLoadingDashboard && (
                <div className="flex-shrink-0">
                  <AvatarDisplay
                    config={avatarConfig}
                    size="lg"
                    showLevel={true}
                    clickable={true}
                    onClick={() => setIsAvatarSelectorOpen(true)}
                    className="animate-bounce-slow"
                  />
                </div>
              )}
            </div>
            
            {/* XP Progress Bar */}
            {gamificationData && !isLoadingDashboard && (
              <div className="mt-4">
                <XPProgressBar
                  currentXP={gamificationData.totalXP}
                  level={gamificationData.level}
                  nextLevelXP={gamificationData.nextLevelXP}
                />
              </div>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Profile & Applications */}
            <div className="space-y-6">
              {/* Impact Stats Card */}
              {gamificationData && !isLoadingDashboard && (
                <PxCard variant="glow">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-2">📊</span>
                    <h2 className="text-lg font-pixel text-sunBurst mb-0">IMPACT STATS</h2>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-pixel text-electric-teal">
                        {gamificationData.impactStats.totalApplications}
                      </div>
                      <div className="text-white text-xs font-pixel">APPLICATIONS</div>
                    </div>
                    <div>
                      <div className="text-2xl font-pixel text-pixel-coral">
                        {gamificationData.impactStats.estimatedVolunteerHours}
                      </div>
                      <div className="text-white text-xs font-pixel">HOURS COMMITTED</div>
                    </div>
                    <div>
                      <div className="text-2xl font-pixel text-neon-cyan">
                        {gamificationData.impactStats.organizationsHelped}
                      </div>
                      <div className="text-white text-xs font-pixel">OPPORTUNITIES</div>
                    </div>
                    <div>
                      <div className="text-2xl font-pixel text-sunBurst">
                        {gamificationData.impactStats.impactScore}
                      </div>
                      <div className="text-white text-xs font-pixel">IMPACT SCORE</div>
                    </div>
                  </div>
                </PxCard>
              )}

              {/* Achievements Card */}
              {achievements.length > 0 && !isLoadingDashboard && (
                <PxCard variant="default">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-2">🏅</span>
                    <h2 className="text-lg font-pixel text-primary mb-0">ACHIEVEMENTS</h2>
                  </div>
                  <div className="grid grid-cols-5 gap-3">
                    {achievements.slice(0, 10).map((achievement) => (
                      <AchievementBadge 
                        key={achievement.id} 
                        achievement={achievement}
                        size="md"
                      />
                    ))}
                  </div>
                  {achievements.length > 10 && (
                    <div className="mt-3 text-center">
                      <span className="text-electric-teal font-pixel text-sm">
                        +{achievements.length - 10} more achievements
                      </span>
                    </div>
                  )}
                </PxCard>
              )}

              <PxCard variant="default">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">🎆</span>
                  <h2 className="text-lg font-pixel text-primary mb-0">HERO PROFILE</h2>
                </div>
                {isLoadingDashboard ? (
                  <PxLoading text="Loading profile..." />
                ) : dashboard?.profile ? (
                  <div className="space-y-2">
                    <p className="text-ink dark:text-white text-sm">
                      <span className="text-electric-teal font-pixel">✉️ EMAIL:</span> {dashboard.profile.email}
                    </p>
                    <p className="text-ink dark:text-white text-sm">
                      <span className="text-electric-teal font-pixel">📍 LOCATION:</span> {dashboard.profile.location || 'Not specified'}
                    </p>
                    {dashboard.profile.skills && dashboard.profile.skills.length > 0 && (
                      <div>
                        <p className="text-electric-teal text-sm mb-2 font-pixel">🎆 SUPERPOWERS:</p>
                        <div className="flex flex-wrap gap-2">
                          {dashboard.profile.skills.map((skill, index) => (
                            <PxChip 
                              key={index}
                              variant="selected"
                              size="sm"
                            >
                              ⚡ {skill}
                            </PxChip>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-white text-sm">Profile not found</p>
                )}
              </PxCard>

              <PxCard variant="default">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">📜</span>
                  <h2 className="text-lg font-pixel text-primary mb-0">ACTIVE QUESTS</h2>
                </div>
                {isLoadingDashboard ? (
                  <PxLoading text="Loading applications..." />
                ) : dashboard?.activeApplications && dashboard.activeApplications.length > 0 ? (
                  <div className="space-y-3">
                    {dashboard.activeApplications.map((app) => (
                      <div key={app.id} className="clip-px border-px border-electric-teal p-3 bg-dark-surface/20">
                        <p className="text-ink dark:text-white text-sm mb-1 font-pixel">
                          🎯 QUEST: {app.opportunityId}
                        </p>
                        <PxChip 
                          variant={app.status === 'approved' ? 'selected' : 'default'}
                          size="sm"
                          className="mb-2"
                        >
                          {app.status === 'pending' ? '⏳' : app.status === 'approved' ? '✅' : '❌'} {app.status.toUpperCase()}
                        </PxChip>
                        <p className="text-ink dark:text-white text-xs">
                          📅 Applied: {new Date(app.submittedAt).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white text-sm">No active applications</p>
                )}
              </PxCard>
            </div>

            {/* Quick Match */}
            <div className="space-y-6">
              <PxCard variant="glow">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-2">✨</span>
                  <h2 className="text-lg font-pixel text-sunBurst mb-0">AI MATCHMAKER</h2>
                </div>
                <p className="text-white text-sm mb-4">
                  🚀 Let our AI find the perfect quests for your skill tree!
                </p>
                <PxButton 
                  variant="primary" 
                  onClick={handleQuickMatch}
                  disabled={opportunitiesLoading}
                >
                  {opportunitiesLoading ? '⏳ SCANNING...' : '✨ FIND QUESTS'}
                </PxButton>
              </PxCard>

              {opportunities.length > 0 && (
                <PxCard variant="default">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-2">🎯</span>
                    <h2 className="text-lg font-pixel text-primary mb-0">QUEST MATCHES</h2>
                  </div>
                  <div className="space-y-4">
                    {opportunities.map((match) => {
                      const matchScore = Math.round(match.score * 100);
                      return (
                        <div key={match.id} className="clip-px border-px border-electric-teal p-4 bg-gradient-to-r from-dark-surface/20 to-primary/10 hover:from-primary/10 hover:to-primary/20 transition-all duration-300">
                          <h3 className="text-ink dark:text-white font-pixel text-sm mb-2">
                            🏆 QUEST {match.opportunityId.toUpperCase()}
                          </h3>
                          <p className="text-ink dark:text-white text-xs mb-2">
                            🏰 {match.organizationId.toUpperCase()} • 📍 MENA REGION
                          </p>
                          <p className="text-ink dark:text-white text-xs mb-3">
                            {match.explanation.join(' • ')}
                          </p>
                          <div className="flex items-center justify-between">
                            <PxChip variant="selected" size="sm">
                              ✨ {matchScore}% MATCH
                            </PxChip>
                            <PxButton
                              variant="success"
                              size="sm"
                              onClick={() => handleApply(match.opportunityId)}
                              disabled={isApplying}
                            >
                              {isApplying ? '⏳' : '🚀 JOIN QUEST'}
                            </PxButton>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </PxCard>
              )}
            </div>
          </div>
        </main>

        {/* Application Confirmation Modal */}
        <PxModal
          isOpen={!!selectedOpportunityId}
          onClose={() => setSelectedOpportunityId(null)}
          title="📝 CONFIRM APPLICATION"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-sm">
              You are about to apply for this quest! Add a personal message to make your application stand out:
            </p>
            <textarea
              value={applicationMessage}
              onChange={(e) => setApplicationMessage(e.target.value)}
              className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
              rows={4}
              placeholder="Tell them why you're excited about this opportunity..."
            />
            <div className="flex space-x-3">
              <PxButton
                variant="success"
                onClick={handleConfirmApplication}
                disabled={isApplying}
              >
                {isApplying ? '⏳ APPLYING...' : '🚀 SUBMIT APPLICATION'}
              </PxButton>
              <PxButton
                variant="secondary"
                onClick={() => setSelectedOpportunityId(null)}
                disabled={isApplying}
              >
                CANCEL
              </PxButton>
            </div>
          </div>
        </PxModal>

        {/* Avatar Customization Modal */}
        {avatarConfig && gamificationData && (
          <AvatarSelector
            currentConfig={avatarConfig}
            userLevel={gamificationData.level}
            achievements={achievements}
            onConfigChange={setAvatarConfig}
            onSave={handleAvatarSave}
            isOpen={isAvatarSelectorOpen}
            onClose={() => setIsAvatarSelectorOpen(false)}
          />
        )}
      </div>
    </ProtectedRoute>
  );
}