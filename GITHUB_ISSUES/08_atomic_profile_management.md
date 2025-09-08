# Build Profile Management Interface

## 📋 **Task Description**
Create a comprehensive profile management system where users can update their skills, causes, experience, and personal information with gaming aesthetics and real-time validation.

## 🔍 **Current State**
No profile management interface exists. Need to build from scratch with gaming theme and integration with BFF profile endpoints.

## 🎯 **Exact Steps to Follow**

### Step 1: Examine existing profile context
Use Read tool to examine `apps/web/contexts/AuthContext.tsx` to understand current user profile structure.

### Step 2: Create ProfileHeader component
Create `apps/web/components/profile/ProfileHeader.tsx`:

```typescript
import React from 'react';
import { PxCard, PxBadge } from '@seraaj/ui';

interface ProfileHeaderProps {
  user: {
    name: string;
    userType: 'volunteer' | 'organization';
    email: string;
    location?: string;
    memberSince: string;
    profileComplete: number; // percentage
    totalApplications?: number;
    completedQuests?: number;
    impactHours?: number;
  };
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({ user }) => {
  const getHeroTitle = (completedQuests: number = 0, impactHours: number = 0) => {
    if (completedQuests >= 10 || impactHours >= 100) return '🏆 Legendary Hero';
    if (completedQuests >= 5 || impactHours >= 50) return '⚔️ Veteran Hero';
    if (completedQuests >= 2 || impactHours >= 20) return '🛡️ Rising Hero';
    return '🌟 Aspiring Hero';
  };

  const getProfileCompleteColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-400';
    if (percentage >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <PxCard className="p-8 mb-8 border-2 border-primary">
      <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
        {/* Avatar */}
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary to-electric-teal flex items-center justify-center text-4xl border-4 border-electric-teal">
          {user.userType === 'volunteer' ? '🦸‍♂️' : '🏰'}
        </div>

        {/* Profile Info */}
        <div className="flex-1 text-center md:text-left">
          <h1 className="text-3xl font-pixel text-primary mb-2">
            {user.name}
          </h1>
          
          {user.userType === 'volunteer' && (
            <p className="text-electric-teal font-pixel mb-3">
              {getHeroTitle(user.completedQuests, user.impactHours)}
            </p>
          )}
          
          <div className="flex flex-wrap gap-3 justify-center md:justify-start mb-4">
            <PxBadge variant="secondary" size="sm">
              {user.userType === 'volunteer' ? '🦸‍♂️ Hero' : '🏰 Quest Giver'}
            </PxBadge>
            {user.location && (
              <PxBadge variant="info" size="sm">
                📍 {user.location}
              </PxBadge>
            )}
            <PxBadge variant="secondary" size="sm">
              📅 Member since {new Date(user.memberSince).getFullYear()}
            </PxBadge>
          </div>

          {/* Profile Completion */}
          <div className="mb-4">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-pixel text-sm text-white">Profile Completion:</span>
              <span className={`font-pixel text-sm ${getProfileCompleteColor(user.profileComplete)}`}>
                {user.profileComplete}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-primary to-electric-teal h-2 rounded-full transition-all duration-500"
                style={{ width: `${user.profileComplete}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Stats */}
        {user.userType === 'volunteer' && (
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-dark-surface p-3 rounded-lg border border-electric-teal/30">
              <div className="text-lg font-pixel text-primary">
                {user.totalApplications || 0}
              </div>
              <div className="text-xs font-pixel text-electric-teal">
                APPLICATIONS
              </div>
            </div>
            <div className="bg-dark-surface p-3 rounded-lg border border-green-400/30">
              <div className="text-lg font-pixel text-green-400">
                {user.completedQuests || 0}
              </div>
              <div className="text-xs font-pixel text-green-400">
                COMPLETED
              </div>
            </div>
            <div className="bg-dark-surface p-3 rounded-lg border border-purple-400/30">
              <div className="text-lg font-pixel text-purple-400">
                {user.impactHours || 0}h
              </div>
              <div className="text-xs font-pixel text-purple-400">
                IMPACT
              </div>
            </div>
          </div>
        )}
      </div>
    </PxCard>
  );
};
```

### Step 3: Create ProfileEditForm component
Create `apps/web/components/profile/ProfileEditForm.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { PxCard, PxButton, PxInput, PxChip } from '@seraaj/ui';

const PREDEFINED_SKILLS = [
  'Teaching', 'Mentoring', 'Project Management', 'Marketing', 'Writing',
  'Translation', 'Web Development', 'Graphic Design', 'Photography',
  'Event Planning', 'Fundraising', 'Social Media', 'Research',
  'Data Analysis', 'Public Speaking', 'Customer Service', 'Leadership',
  'Accounting', 'Legal Support', 'Healthcare', 'Cooking', 'Construction'
];

const PREDEFINED_CAUSES = [
  'Education', 'Health', 'Environment', 'Poverty Alleviation', 
  'Human Rights', 'Youth Development', 'Elderly Care', 'Animal Welfare',
  'Community Development', 'Technology for Good', 'Arts & Culture',
  'Sports & Recreation', 'Disaster Relief', 'Mental Health',
  'Women Empowerment', 'Disability Rights', 'Child Protection'
];

interface ProfileData {
  name: string;
  email: string;
  location: string;
  bio: string;
  skills: string[];
  causes: string[];
  experienceLevel?: string;
  availability?: string;
  phoneNumber?: string;
  website?: string;
}

interface ProfileEditFormProps {
  initialData: ProfileData;
  userType: 'volunteer' | 'organization';
  onSave: (data: ProfileData) => void;
  onCancel: () => void;
  isSaving?: boolean;
}

export const ProfileEditForm: React.FC<ProfileEditFormProps> = ({
  initialData,
  userType,
  onSave,
  onCancel,
  isSaving = false
}) => {
  const [formData, setFormData] = useState<ProfileData>(initialData);
  const [customSkill, setCustomSkill] = useState('');
  const [customCause, setCustomCause] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (userType === 'volunteer' && formData.skills.length === 0) {
      newErrors.skills = 'Please select at least one skill';
    }

    if (formData.causes.length === 0) {
      newErrors.causes = 'Please select at least one cause you care about';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSave(formData);
    }
  };

  const toggleSkill = (skill: string) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
  };

  const toggleCause = (cause: string) => {
    setFormData(prev => ({
      ...prev,
      causes: prev.causes.includes(cause)
        ? prev.causes.filter(c => c !== cause)
        : [...prev.causes, cause]
    }));
  };

  const addCustomSkill = () => {
    if (customSkill.trim() && !formData.skills.includes(customSkill.trim())) {
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, customSkill.trim()]
      }));
      setCustomSkill('');
    }
  };

  const addCustomCause = () => {
    if (customCause.trim() && !formData.causes.includes(customCause.trim())) {
      setFormData(prev => ({
        ...prev,
        causes: [...prev.causes, customCause.trim()]
      }));
      setCustomCause('');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid md:grid-cols-2 gap-8">
        {/* Personal Information */}
        <PxCard className="p-6">
          <h3 className="text-lg font-pixel text-primary mb-6">
            👤 PERSONAL INFO
          </h3>
          
          <div className="space-y-4">
            <PxInput
              label="Full Name *"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              error={errors.name}
              required
            />
            
            <PxInput
              label="Email *"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              error={errors.email}
              required
            />
            
            <PxInput
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              placeholder="City, Country"
            />
            
            <div>
              <label className="block text-sm font-pixel text-electric-teal mb-2">
                Bio
              </label>
              <textarea
                value={formData.bio}
                onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                rows={4}
                className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg resize-none"
                placeholder={userType === 'volunteer' 
                  ? "Tell other heroes about yourself..." 
                  : "Describe your organization..."
                }
              />
            </div>

            {userType === 'volunteer' && (
              <>
                <div>
                  <label className="block text-sm font-pixel text-electric-teal mb-2">
                    Experience Level
                  </label>
                  <select
                    value={formData.experienceLevel || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, experienceLevel: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
                  >
                    <option value="">Select experience level</option>
                    <option value="beginner">🌱 Beginner Hero</option>
                    <option value="intermediate">⚔️ Experienced Hero</option>
                    <option value="advanced">🏆 Expert Hero</option>
                    <option value="expert">👑 Master Hero</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-pixel text-electric-teal mb-2">
                    Availability
                  </label>
                  <select
                    value={formData.availability || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, availability: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
                  >
                    <option value="">Select availability</option>
                    <option value="1-2">1-2 hours/week</option>
                    <option value="3-5">3-5 hours/week</option>
                    <option value="6-10">6-10 hours/week</option>
                    <option value="10+">10+ hours/week</option>
                    <option value="flexible">Flexible schedule</option>
                  </select>
                </div>
              </>
            )}
          </div>
        </PxCard>

        {/* Skills & Causes */}
        <PxCard className="p-6">
          <h3 className="text-lg font-pixel text-primary mb-6">
            ⚡ ABILITIES & CAUSES
          </h3>

          {/* Skills */}
          {userType === 'volunteer' && (
            <div className="mb-8">
              <div className="flex items-center gap-4 mb-4">
                <h4 className="font-pixel text-electric-teal">
                  🛠️ Skills ({formData.skills.length} selected) *
                </h4>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-4">
                {PREDEFINED_SKILLS.map(skill => (
                  <PxChip
                    key={skill}
                    variant={formData.skills.includes(skill) ? 'selected' : 'default'}
                    onClick={() => toggleSkill(skill)}
                    className="cursor-pointer"
                    size="sm"
                  >
                    {skill}
                  </PxChip>
                ))}
              </div>

              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  placeholder="Add custom skill..."
                  value={customSkill}
                  onChange={(e) => setCustomSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomSkill())}
                  className="flex-1 px-3 py-2 border border-electric-teal bg-dark-surface text-white rounded text-sm"
                />
                <PxButton 
                  type="button"
                  variant="secondary" 
                  size="sm"
                  onClick={addCustomSkill}
                  disabled={!customSkill.trim()}
                >
                  Add
                </PxButton>
              </div>
              
              {errors.skills && (
                <p className="text-red-400 text-sm">{errors.skills}</p>
              )}
            </div>
          )}

          {/* Causes */}
          <div>
            <div className="flex items-center gap-4 mb-4">
              <h4 className="font-pixel text-electric-teal">
                ❤️ Causes ({formData.causes.length} selected) *
              </h4>
            </div>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {PREDEFINED_CAUSES.map(cause => (
                <PxChip
                  key={cause}
                  variant={formData.causes.includes(cause) ? 'selected' : 'default'}
                  onClick={() => toggleCause(cause)}
                  className="cursor-pointer"
                  size="sm"
                >
                  {cause}
                </PxChip>
              ))}
            </div>

            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Add custom cause..."
                value={customCause}
                onChange={(e) => setCustomCause(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomCause())}
                className="flex-1 px-3 py-2 border border-electric-teal bg-dark-surface text-white rounded text-sm"
              />
              <PxButton 
                type="button"
                variant="secondary" 
                size="sm"
                onClick={addCustomCause}
                disabled={!customCause.trim()}
              >
                Add
              </PxButton>
            </div>
            
            {errors.causes && (
              <p className="text-red-400 text-sm">{errors.causes}</p>
            )}
          </div>
        </PxCard>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 mt-8 justify-end">
        <PxButton
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isSaving}
        >
          Cancel
        </PxButton>
        <PxButton
          type="submit"
          variant="primary"
          loading={isSaving}
        >
          💾 Save Profile
        </PxButton>
      </div>
    </form>
  );
};
```

### Step 4: Create main Profile page
Create `apps/web/app/profile/page.tsx`:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/navigation/Header';
import { ProfileHeader } from '@/components/profile/ProfileHeader';
import { ProfileEditForm } from '@/components/profile/ProfileEditForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PxButton, PxCard, PxLoading } from '@seraaj/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

const ProfileContent = () => {
  const { user, updateProfile } = useAuth();
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [profileStats, setProfileStats] = useState({
    totalApplications: 0,
    completedQuests: 0,
    impactHours: 0
  });

  // Calculate profile completion percentage
  const calculateProfileCompletion = (userData: any) => {
    if (!userData) return 0;
    
    const fields = [
      userData.name,
      userData.email,
      userData.location,
      userData.bio,
      userData.skills?.length > 0,
      userData.causes?.length > 0,
      userData.experienceLevel,
      userData.availability
    ];
    
    const completed = fields.filter(Boolean).length;
    return Math.round((completed / fields.length) * 100);
  };

  // Mock stats loading - replace with real API
  useEffect(() => {
    setProfileStats({
      totalApplications: 5,
      completedQuests: 3,
      impactHours: 47
    });
  }, []);

  const handleSaveProfile = async (profileData: any) => {
    setIsSaving(true);
    try {
      await updateProfile(profileData);
      setIsEditing(false);
      // Show success message or toast
    } catch (error) {
      console.error('Failed to update profile:', error);
      // Show error message
    } finally {
      setIsSaving(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
        <div className="flex justify-center items-center py-24">
          <PxLoading size="lg" variant="bright" text="Loading hero profile..." />
        </div>
      </div>
    );
  }

  const profileData = {
    ...user,
    profileComplete: calculateProfileCompletion(user),
    ...profileStats,
    memberSince: user.createdAt || new Date().toISOString()
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-6xl mx-auto p-6">
        {/* Profile Header */}
        <ProfileHeader user={profileData} />

        {/* Edit Mode Toggle */}
        {!isEditing && (
          <div className="flex gap-4 mb-8 justify-center">
            <PxButton
              variant="primary"
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-2"
            >
              ✏️ Edit Profile
            </PxButton>
            <PxButton
              variant="secondary"
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2"
            >
              🏰 Back to Command Center
            </PxButton>
          </div>
        )}

        {/* Edit Form or Profile Display */}
        {isEditing ? (
          <ProfileEditForm
            initialData={{
              name: user.name || '',
              email: user.email || '',
              location: user.location || '',
              bio: user.bio || '',
              skills: user.skills || [],
              causes: user.causes || [],
              experienceLevel: user.experienceLevel,
              availability: user.availability,
              phoneNumber: user.phoneNumber,
              website: user.website
            }}
            userType={user.userType || 'volunteer'}
            onSave={handleSaveProfile}
            onCancel={() => setIsEditing(false)}
            isSaving={isSaving}
          />
        ) : (
          <div className="grid md:grid-cols-2 gap-8">
            {/* Profile Details */}
            <PxCard className="p-6">
              <h3 className="text-lg font-pixel text-primary mb-6">
                👤 PROFILE DETAILS
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-pixel text-electric-teal mb-1">
                    Email
                  </label>
                  <p className="text-white">{user.email}</p>
                </div>
                
                {user.location && (
                  <div>
                    <label className="block text-sm font-pixel text-electric-teal mb-1">
                      Location
                    </label>
                    <p className="text-white">📍 {user.location}</p>
                  </div>
                )}
                
                {user.bio && (
                  <div>
                    <label className="block text-sm font-pixel text-electric-teal mb-1">
                      Bio
                    </label>
                    <p className="text-white">{user.bio}</p>
                  </div>
                )}
                
                {user.experienceLevel && (
                  <div>
                    <label className="block text-sm font-pixel text-electric-teal mb-1">
                      Experience Level
                    </label>
                    <p className="text-white capitalize">{user.experienceLevel}</p>
                  </div>
                )}
                
                {user.availability && (
                  <div>
                    <label className="block text-sm font-pixel text-electric-teal mb-1">
                      Availability
                    </label>
                    <p className="text-white">{user.availability} hours/week</p>
                  </div>
                )}
              </div>
            </PxCard>

            {/* Skills & Causes */}
            <PxCard className="p-6">
              <h3 className="text-lg font-pixel text-primary mb-6">
                ⚡ ABILITIES & CAUSES
              </h3>
              
              {user.skills && user.skills.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-pixel text-electric-teal mb-3">
                    🛠️ Skills
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {user.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="bg-primary/20 text-primary px-3 py-1 rounded-full text-sm font-pixel border border-primary"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {user.causes && user.causes.length > 0 && (
                <div>
                  <label className="block text-sm font-pixel text-electric-teal mb-3">
                    ❤️ Causes You Care About
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {user.causes.map((cause, index) => (
                      <span
                        key={index}
                        className="bg-electric-teal/20 text-electric-teal px-3 py-1 rounded-full text-sm font-pixel border border-electric-teal"
                      >
                        {cause}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {(!user.skills?.length && !user.causes?.length) && (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🎯</div>
                  <p className="text-gray-400 mb-4">
                    Complete your profile to unlock your full hero potential!
                  </p>
                  <PxButton variant="primary" onClick={() => setIsEditing(true)}>
                    Complete Profile
                  </PxButton>
                </div>
              )}
            </PxCard>
          </div>
        )}

        {/* Profile Completion Tips */}
        {profileData.profileComplete < 90 && !isEditing && (
          <PxCard className="mt-8 p-6 border-2 border-yellow-400/50">
            <div className="text-center">
              <div className="text-4xl mb-4">💡</div>
              <h3 className="text-lg font-pixel text-yellow-400 mb-2">
                LEVEL UP YOUR PROFILE!
              </h3>
              <p className="text-white mb-4">
                Complete your profile to get better quest matches and stand out to organizations.
              </p>
              <div className="text-sm text-gray-300 mb-4">
                Missing: {profileData.profileComplete < 100 ? 'Complete all fields to reach 100%' : ''}
              </div>
              <PxButton variant="warning" onClick={() => setIsEditing(true)}>
                🚀 Complete Profile
              </PxButton>
            </div>
          </PxCard>
        )}
      </main>
    </div>
  );
};

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
```

### Step 5: Update AuthContext to include updateProfile method
Add to the existing `apps/web/contexts/AuthContext.tsx`:

```typescript
// Add this method to the AuthContext
const updateProfile = async (profileData: any) => {
  try {
    setLoading(true);
    
    // Call BFF API to update profile
    const response = await fetch('/api/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update profile');
    }
    
    const updatedUser = await response.json();
    
    // Update local user state
    setUser(prev => ({ ...prev, ...updatedUser }));
    
    return updatedUser;
  } catch (error) {
    console.error('Profile update error:', error);
    throw error;
  } finally {
    setLoading(false);
  }
};

// Add to the context value
return (
  <AuthContext.Provider value={{
    // ... existing values
    updateProfile
  }}>
    {children}
  </AuthContext.Provider>
);
```

## ✅ **Definition of Done**
- [ ] ProfileHeader shows user info with gaming theme and stats
- [ ] Profile completion percentage calculated and displayed
- [ ] ProfileEditForm allows editing all profile fields
- [ ] Skills and causes selection with chips interface
- [ ] Form validation works for required fields
- [ ] Profile page shows read-only view when not editing
- [ ] Edit mode toggle works correctly
- [ ] Profile updates save to backend via AuthContext
- [ ] Gaming aesthetics consistent throughout
- [ ] Profile completion tips shown for incomplete profiles
- [ ] Responsive design works on mobile

## 🧪 **How to Test**
1. Navigate to `/profile` when logged in
2. Verify profile header shows correct user info and stats
3. Click "Edit Profile" to enter edit mode
4. Test skills/causes selection with chips
5. Test form validation by submitting with missing required fields
6. Fill out complete profile and save
7. Verify profile completion percentage updates
8. Test profile completion tips for incomplete profiles
9. Check responsive design on mobile
10. Verify gaming theme consistency

**This should take 4-5 hours to implement and test thoroughly.**