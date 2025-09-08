'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
              <PxInput
                label="Hero Name"
                type="text"
                value={isEditing ? editName : (user?.name || '')}
                onChange={isEditing ? (e) => setEditName(e.target.value) : undefined}
                placeholder="Enter your hero name"
                readOnly={!isEditing}
              />
              <PxInput
                label="Email Contact"
                type="email"
                value={isEditing ? editEmail : (user?.email || '')}
                onChange={isEditing ? (e) => setEditEmail(e.target.value) : undefined}
                placeholder="hero@example.com"
                readOnly={!isEditing}
              />
              <PxInput
                label="Location"
                type="text"
                value={isEditing ? editLocation : ((dashboardData?.profile as any)?.location || '')}
                onChange={isEditing ? (e) => setEditLocation(e.target.value) : undefined}
                placeholder="City, Country"
                readOnly={!isEditing}
              />
              <div className="space-y-1">
                <label className="text-sm font-pixel text-ink dark:text-white">Bio</label>
                <textarea
                  className="w-full bg-transparent border border-electric-teal text-white p-2"
                  rows={3}
                  value={isEditing ? editBio : ((dashboardData?.profile as any)?.bio || '')}
                  onChange={isEditing ? (e) => setEditBio(e.target.value) : undefined}
                  placeholder="Tell us about yourself"
                  readOnly={!isEditing}
                />
              </div>
              <PxInput
                label="Skills (comma separated)"
                type="text"
                value={isEditing ? editSkillsText : (((dashboardData?.profile as any)?.skills || []).join(', '))}
                onChange={isEditing ? (e) => setEditSkillsText(e.target.value) : undefined}
                placeholder="e.g., teaching, first aid, Python"
                readOnly={!isEditing}
              />
              <PxInput
                label="Interests (comma separated)"
                type="text"
                value={isEditing ? editInterestsText : (((dashboardData?.profile as any)?.interests || []).join(', '))}
                onChange={isEditing ? (e) => setEditInterestsText(e.target.value) : undefined}
                placeholder="e.g., Education, Health, Environment"
                readOnly={!isEditing}
              />
              <div className="space-y-1">
                <label className="text-sm font-pixel text-ink dark:text-white">Availability (hrs/week)</label>
                <select
                  className="w-full bg-transparent border border-electric-teal text-white p-2"
                  value={editAvailability}
                  onChange={isEditing ? (e) => setEditAvailability(e.target.value) : undefined}
                  disabled={!isEditing}
                >
                  <option value="">Select availability...</option>
                  <option value="1-2">1-2</option>
                  <option value="3-5">3-5</option>
                  <option value="6-10">6-10</option>
                  <option value="10+">10+</option>
                </select>
              </div>
        // Initialize avatar configuration
        const avatarClass = calculateAvatarClass(level, generatedAchievements);
        const unlockedAccessories = getUnlockedAccessories(generatedAchievements, level);
        const defaultAvatarConfig: AvatarConfig = {
          class: avatarClass,
          level: level,
          pose: AvatarPose.DEFAULT,
          accessories: unlockedAccessories.slice(0, 2)
        };
        setAvatarConfig(defaultAvatarConfig);
      } catch (error) {
        console.error('Failed to load profile data:', error);
      }
    };

    loadProfileData();
  }, [user, tokens]);

  const handleEditClick = () => {
    setIsEditing(true);
    setEditName(user?.name || '');
    setEditEmail(user?.email || '');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditName(user?.name || '');
    setEditEmail(user?.email || '');
    const p: any = dashboardData?.profile || {};
    setEditLocation(p?.location || '');
    setEditBio(p?.bio || '');
    setEditSkillsText(Array.isArray(p?.skills) ? p.skills.join(', ') : '');
    setEditInterestsText(Array.isArray(p?.interests) ? p.interests.join(', ') : '');
    const avail = p?.availability as any;
    if (avail) {
      const a = avail as { weekdays?: boolean; weekends?: boolean; evenings?: boolean };
      if (a.weekdays && a.weekends && a.evenings) setEditAvailability('10+');
      else if (a.weekdays) setEditAvailability('6-10');
      else if (a.evenings && a.weekends) setEditAvailability('3-5');
      else if (a.evenings) setEditAvailability('1-2');
      else setEditAvailability('');
    } else {
      setEditAvailability('');
    }
  };

  const handleSaveProfile = async () => {
    if (!editName.trim()) {
      showError('Hero name cannot be empty!');
      return;
    }

    if (!editEmail.trim()) {
      showError('Email contact cannot be empty!');
      return;
    }

    try {
      setIsSaving(true);
      
      if (!user || !tokens?.accessToken) {
        throw new Error('Not authenticated');
      }

      const api = createAuthenticatedVolunteerApi(tokens.accessToken);
      // Map availability selection to backend flags (aligned with onboarding)
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

      const skills = editSkillsText.split(',').map(s => s.trim()).filter(Boolean);
      const interests = editInterestsText.split(',').map(s => s.trim()).filter(Boolean);

      await api.updateVolunteerProfile(user.id, {
        name: editName.trim(),
        email: editEmail.trim(),
        location: editLocation.trim() || undefined,
        bio: editBio.trim() || undefined,
        skills: skills.length ? skills : undefined,
        interests: interests.length ? interests : undefined,
        availability: mapAvailability(editAvailability),
      });
      showSuccess('Profile updated successfully!');
      setIsEditing(false);
      
      // Refresh user data in context to reflect changes
      await reloadUser();
      
    } catch (error) {
      console.error('Failed to save profile:', error);
      showError(error instanceof Error ? error.message : 'Failed to save profile changes');
    } finally {
      setIsSaving(false);
    }
  };

  // Background completion state for UI feedback
  const [completingIds, setCompletingIds] = useState<Set<string>>(new Set());

  const handleCompleteApplication = async (applicationId: string) => {
    if (!user || !tokens?.accessToken) return;
    try {
      setCompletingIds((prev) => new Set(prev).add(applicationId));
      const volunteerApi = createAuthenticatedVolunteerApi(tokens.accessToken);
      await volunteerApi.completeApplication(applicationId);
      // Reload dashboard/profile data
      const fetchedDashboardData = await volunteerApi.getVolunteerDashboard(user.id);
      setDashboardData(fetchedDashboardData);
      // Optionally recalc achievements/level here if you show them in profile widgets
    } catch (error) {
      console.error('Failed to complete application:', error);
      showError('Failed to mark application as completed.');
    } finally {
      setCompletingIds((prev) => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  };

  const handleAvatarSave = (newConfig: AvatarConfig) => {
    setAvatarConfig(newConfig);
    setIsAvatarSelectorOpen(false);
    showSuccess('Avatar updated successfully! 🎭 Your hero appearance has been saved.');
    // TODO: Save avatar config to user profile/preferences in backend
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
      <main className="max-w-4xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-pixel text-primary dark:text-neon-cyan mb-2">
            👤 HERO PROFILE 👤
          </h1>
          <p className="text-white text-lg">
            Manage your personal info and settings
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Avatar Card */}
          {avatarConfig && (
            <PxCard variant="glow" className="col-span-full">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-3xl mr-3">🎭</span>
                  <h2 className="text-xl font-pixel text-sunBurst mb-0">HERO AVATAR</h2>
                </div>
                <PxButton 
                  variant="secondary" 
                  size="sm" 
                  onClick={() => setIsAvatarSelectorOpen(true)}
                >
                  ✨ CUSTOMIZE
                </PxButton>
              </div>
              <div className="flex items-center justify-center space-x-6 py-6">
                <AvatarDisplay
                  config={avatarConfig}
                  size="lg"
                  showLevel={true}
                  clickable={true}
                  onClick={() => setIsAvatarSelectorOpen(true)}
                  className="animate-bounce-slow"
                />
                <div className="text-center">
                  <h3 className="font-pixel text-electric-teal text-lg mb-2">
                    {avatarConfig.class.toUpperCase()} - LEVEL {userLevel}
                  </h3>
                  <div className="space-y-1">
                    <p className="text-white text-sm">🎯 Pose: {avatarConfig.pose}</p>
                    <p className="text-white text-sm">🏆 Accessories: {avatarConfig.accessories.length}</p>
                    <p className="text-white text-sm">✨ Unlocked Items: {getUnlockedAccessories(achievements, userLevel).length}</p>
                  </div>
                </div>
              </div>
            </PxCard>
          )}

          <PxCard variant="default" className="col-span-full md:col-span-1">
            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">🎆</span>
              <h2 className="text-xl font-pixel text-primary mb-0">HERO DATA</h2>
            </div>
            <div className="space-y-4">
              <PxInput
                label="📛 HERO NAME"
                type="text"
                value={isEditing ? editName : (user?.name || '')}
                onChange={isEditing ? (e) => setEditName(e.target.value) : undefined}
                placeholder="Enter your hero name"
                readOnly={!isEditing}
              />
              <PxInput
                label="Email Contact"
                type="email"
                value={isEditing ? editEmail : (user?.email || '')}
                onChange={isEditing ? (e) => setEditEmail(e.target.value) : undefined}
                placeholder="hero@example.com"
                readOnly={!isEditing}

              <PxInput
                label="Location"
                type="text"
                value={isEditing ? editLocation : ((dashboardData?.profile as any)?.location || '')}
                onChange={isEditing ? (e) => setEditLocation(e.target.value) : undefined}
                placeholder="City, Country"
                readOnly={!isEditing}
              />
              <div className="space-y-1">
                <label className="text-sm font-pixel text-ink dark:text-white">Bio</label>
                <textarea
                  className="w-full bg-transparent border border-electric-teal text-white p-2"
                  rows={3}
                  value={isEditing ? editBio : ((dashboardData?.profile as any)?.bio || '')}
                  onChange={isEditing ? (e) => setEditBio(e.target.value) : undefined}
                  placeholder="Tell us about yourself"
                  readOnly={!isEditing}
                />
              </div>
              <PxInput
                label="Skills (comma separated)"
                type="text"
                value={isEditing ? editSkillsText : (((dashboardData?.profile as any)?.skills || []).join(', '))}
                onChange={isEditing ? (e) => setEditSkillsText(e.target.value) : undefined}
                placeholder="e.g., teaching, first aid, Python"
                readOnly={!isEditing}
              />
              <PxInput
                label="Interests (comma separated)"
                type="text"
                value={isEditing ? editInterestsText : (((dashboardData?.profile as any)?.interests || []).join(', '))}
                onChange={isEditing ? (e) => setEditInterestsText(e.target.value) : undefined}
                placeholder="e.g., Education, Health, Environment"
                readOnly={!isEditing}
              />
              <div className="space-y-1">
                <label className="text-sm font-pixel text-ink dark:text-white">Availability (hrs/week)</label>
                <select
                  className="w-full bg-transparent border border-electric-teal text-white p-2"
                  value={editAvailability}
                  onChange={isEditing ? (e) => setEditAvailability(e.target.value) : undefined}
                  disabled={!isEditing}
                >
                  <option value="">Select availability...</option>
                  <option value="1-2">1-2</option>
                  <option value="3-5">3-5</option>
                  <option value="6-10">6-10</option>
                  <option value="10+">10+</option>
                </select>
              </div>
              />
              <div>
                <p className="text-sm font-pixel text-ink dark:text-white mb-2">🎖️ CLASS:</p>
                <PxChip variant="selected" size="sm">
                  {user?.role === UserRole.VOLUNTEER ? '🎆 HERO' : '🏰 GUILD MASTER'}
                </PxChip>
              </div>
              
              {isEditing ? (
                <div className="flex space-x-3">
                  <PxButton 
                    variant="success" 
                    onClick={handleSaveProfile}
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </PxButton>
                  <PxButton 
                    variant="secondary" 
                    onClick={handleCancelEdit}
                    disabled={isSaving}
                  >
                    Cancel
                  </PxButton>
              ) : (
                <PxButton variant="primary" onClick={handleEditClick}>
                  Edit Profile
                </PxButton>
              )}
            </div>
          </PxCard>

          <PxCard variant="glow" className="hidden col-span-full md:col-span-1">
            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">📈</span>
              <h2 className="text-xl font-pixel text-sunBurst mb-0">HERO STATS</h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center clip-px border-px border-electric-teal p-3">
                  <div className="text-2xl font-pixel text-primary mb-1">
                    {impactStats?.estimatedVolunteerHours || 0}
                  </div>
                  <div className="text-xs text-white">⏱️ HOURS</div>
                </div>
                <div className="text-center clip-px border-px border-electric-teal p-3">
                  <div className="text-2xl font-pixel text-primary mb-1">
                    {impactStats?.totalApplications || 0}
                  </div>
                  <div className="text-xs text-white">🎯 QUESTS</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-white">🏰 Guilds Helped:</span>
                  <PxChip variant="selected" size="sm">
                    {impactStats?.organizationsHelped || 0}
                  </PxChip>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">🌟 Impact Level:</span>
                  <PxChip variant="selected" size="sm" className="bg-pixel-coral">
                    🔥 {impactStats?.impactLevel || 'NEWCOMER'}
                  </PxChip>
                </div>
              </div>
              
              <div>
                <p className="text-sm font-pixel text-white mb-2">🏅 ACHIEVEMENT BADGES:</p>
                <div className="flex flex-wrap gap-2">
                  {achievements.slice(0, 6).map((achievement) => (
                    <PxChip 
                      key={achievement.id}
                      variant={achievement.earnedAt ? "selected" : "default"}
                      size="sm"
                      className={achievement.earnedAt ? "" : "opacity-50"}
                    >
                      {achievement.icon} {achievement.name.toUpperCase()}
                    </PxChip>
                  ))}
                  {achievements.length === 0 && (
                    <PxChip variant="default" size="sm" className="opacity-50">
                      🎆 NEWCOMER
                    </PxChip>
                  )}
                </div>
              </div>
            </div>
          </PxCard>

          <PxCard variant="default" className="hidden col-span-full">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-2">📅</span>
              <h2 className="text-xl font-pixel text-primary mb-0">
                QUEST JOURNAL
              </h2>
            </div>
            <div className="space-y-4">
              {user && tokens?.accessToken && (
                <>
                  {/* Recent Applications */}
                  {dashboardData?.activeApplications?.slice(0, 3).map((application: {
                    id: string;
                    volunteerId: string;
                    opportunityId: string;
                    organizationId: string | null;
                    status: string;
                    coverLetter: string;
                    submittedAt: string;
                    reviewedAt: string | null;
                    createdAt: string;
                    updatedAt: string;
                  }) => {
                    const statusConfigs: Record<string, { icon: string; text: string; border: string; bg: string; timeText: string }> = {
                      approved: { icon: '✅', text: 'QUEST APPROVED!', border: 'border-success', bg: 'bg-success/10', timeText: 'Ready to start' },
                      pending: { icon: '⏳', text: 'QUEST PENDING', border: 'border-warning', bg: 'bg-warning/10', timeText: 'Awaiting guild approval' },
                      rejected: { icon: '❌', text: 'QUEST DECLINED', border: 'border-error', bg: 'bg-error/10', timeText: 'Application not accepted' },
                      withdrawn: { icon: '🔄', text: 'QUEST WITHDRAWN', border: 'border-info', bg: 'bg-info/10', timeText: 'Application withdrawn' }
                    };
                    const statusConfig = statusConfigs[application.status] || { icon: '📝', text: 'QUEST SUBMITTED', border: 'border-info', bg: 'bg-info/10', timeText: 'Application submitted' };

                    return (
                      <div key={application.id} className={`clip-px border-px ${statusConfig.border} p-3 ${statusConfig.bg}`}>
                        <div className="flex items-center mb-1">
                          <span className="text-lg mr-2">{statusConfig.icon}</span>
                          <p className="text-ink dark:text-white text-sm font-pixel">
                            {statusConfig.text}
                          </p>
                        </div>
                        <p className="text-xs text-ink dark:text-gray-300 ml-6">
                          🎯 Opportunity ID: {application.opportunityId} • {statusConfig.timeText}
                        </p>
                        {application.status === 'approved' && (
                          <div className="mt-2 ml-6">
                            <PxButton
                              variant="success"
                              size="sm"
                              onClick={() => handleCompleteApplication(application.id)}
                              disabled={completingIds.has(application.id)}
                            >
                              {completingIds.has(application.id) ? 'Completing…' : 'Mark Completed'}
                            </PxButton>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  
                  {/* Show message when no active applications */}
                  {(!dashboardData?.activeApplications || dashboardData.activeApplications.length === 0) && (
                    <div className="clip-px border-px border-info p-3 bg-info/10">
                      <div className="flex items-center mb-1">
                        <span className="text-lg mr-2">🎯</span>
                        <p className="text-ink dark:text-white text-sm font-pixel">
                          READY FOR NEW QUESTS!
                        </p>
                      </div>
                      <p className="text-xs text-ink dark:text-gray-300 ml-6">
                        🚀 Start your hero journey by applying to opportunities
                      </p>
                    </div>
                  )}
                </>
              )}

              {/* Fallback for when not authenticated or data is loading */}
              {(!user || !tokens?.accessToken) && (
                <div className="clip-px border-px border-info p-3 bg-info/10">
                  <div className="flex items-center mb-1">
                    <span className="text-lg mr-2">⏳</span>
                    <p className="text-ink dark:text-white text-sm font-pixel">
                      LOADING QUEST JOURNAL...
                    </p>
                  </div>
                  <p className="text-xs text-ink dark:text-gray-300 ml-6">🔄 Retrieving your adventure data</p>
                </div>
              )}
            </div>
            
            <div className="mt-6 pt-4 border-t border-ink/20 dark:border-dark-border">
              <div className="grid md:grid-cols-3 gap-3">
                <PxButton variant="primary" size="sm" className="w-full">
                  🎯 DASHBOARD
                </PxButton>
                <PxButton variant="secondary" size="sm" className="w-full">
                  🔍 NEW QUESTS
                </PxButton>
                <PxButton variant="success" size="sm" className="w-full">
                  ✨ QUICK MATCH
                </PxButton>
              </div>
            </div>
          </PxCard>
        </div>
      </main>
      
      {/* Avatar Customization Modal */}
      {avatarConfig && (
        <AvatarSelector
          currentConfig={avatarConfig}
          userLevel={userLevel}
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







