# Issue #2: Migrate V2 Onboarding Flow with Event-Driven Architecture

## 🎯 **OBJECTIVE**
Port V2's sophisticated onboarding system to our event-sourced architecture while maintaining all UX features and adding proper event sourcing for user profile creation.

## 🏗️ **ARCHITECTURE CONTEXT**
- **Current**: Basic onboarding in `apps/web/components/onboarding/`
- **V2 Source**: `C:\Users\Mohamad\Documents\Claude\Seraaj\apps\web\components\onboarding\`
- **Target**: Event-driven onboarding with V2's UX polish
- **Backend**: Events flow through BFF to Auth service

## ⚠️ **CRITICAL WARNINGS - READ TWICE**
1. **DO NOT** break the existing auth flow - test thoroughly
2. **DO NOT** modify BFF or Auth service APIs without understanding them first
3. **DO NOT** remove existing onboarding until new one is fully working
4. **DO NOT** hardcode user data - everything must be event-driven
5. **DO NOT** copy V2 contexts without understanding current state management

## 📊 **CURRENT VS V2 COMPARISON**

### **Current Onboarding (Event-Sourced)**
```typescript
// Location: apps/web/components/onboarding/
// Features:
// - Basic step navigation
// - Integrated with AuthContext
// - Event-sourced profile updates via BFF
// - Gaming theme ("hero" terminology)

// Architecture:
User Registration → AuthContext → BFF → Auth Service → Database Events
```

### **V2 Onboarding (Rich UX)**
```typescript
// Location: C:\Users\Mohamad\Documents\Claude\Seraaj\apps\web\components\onboarding\
// Features:
// - 5-step progressive flow
// - Rich form validation
// - User type selection (volunteer/organization)
// - Skills/interests selection with chips
// - Progress visualization
// - Internationalization support
// - Professional form layouts

// Components:
// - OnboardingFlow.tsx (main coordinator)
// - steps/WelcomeStep.tsx
// - steps/UserTypeStep.tsx  
// - steps/ProfileStep.tsx
// - steps/PreferencesStep.tsx
// - steps/CompletionStep.tsx
```

## 🗺️ **MIGRATION STRATEGY**

### **Phase 2A: Analysis and Planning (1 hour)**
1. Map V2 onboarding data to current event schema
2. Identify missing fields in current Auth service
3. Plan event flow for each onboarding step
4. Document state management differences

### **Phase 2B: Component Structure Migration (2 hours)**
1. Create new onboarding components based on V2
2. Adapt to current event-driven architecture
3. Integrate with existing AuthContext
4. Test each step individually

### **Phase 2C: Integration and Testing (1 hour)**  
1. Wire up complete flow
2. Test event persistence
3. Verify profile creation works end-to-end

## 🔧 **DETAILED IMPLEMENTATION**

### **Step 1: Data Mapping Analysis**

#### **V2 Onboarding Data Structure**
```typescript
// From V2's OnboardingFlow.tsx
interface OnboardingData {
  userType: 'volunteer' | 'organization' | null;
  name: string;
  email: string;
  location: string;
  bio: string;
  interests: string[];
  skills: string[];
  causes: string[];
  availability: string;
  organizationName?: string;
  organizationType?: string;  
  organizationSize?: string;
}
```

#### **Current Event-Sourced Profile Events**
```typescript
// Check what events our current Auth service expects:
// Look in: services/auth/

// Document current profile event schema:
// Example: UserProfileUpdated, UserPreferencesSet, etc.

// CREATE MAPPING TABLE:
/*
V2 Field              → Current Event Field    → Event Type
userType             → userType               → UserTypeSelected  
name                 → fullName               → ProfileUpdated
email                → email                  → (handled in registration)
location             → location               → LocationSet
bio                  → bio                    → ProfileUpdated
interests            → interests              → InterestsUpdated
skills               → skills                 → SkillsUpdated
causes               → causes                 → CausesUpdated
availability         → availability           → AvailabilitySet
organizationName     → organizationName       → OrganizationProfileUpdated
*/
```

### **Step 2: Component Migration**

#### **2.1: Main Onboarding Coordinator**
```typescript
// Create: apps/web/components/onboarding/OnboardingFlow.tsx
// Based on V2 but integrated with our AuthContext

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { PxButton, PxCard, PxProgress } from '@seraaj/ui'; // Use migrated components

// Copy V2's OnboardingData interface but adapt field names
interface OnboardingData {
  // Map V2 fields to our event schema fields
  userType: 'volunteer' | 'organization' | null;
  // ... other fields mapped to our schema
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const { updateProfile } = useAuth(); // Use our existing auth context
  
  // Copy V2's step management logic
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({...});
  
  // Adapt V2's completion logic to emit events
  const handleComplete = async (finalData: OnboardingData) => {
    try {
      // Instead of V2's direct API calls, use our event-driven approach:
      await updateProfile({
        userType: finalData.userType,
        profile: {
          name: finalData.name,
          bio: finalData.bio,
          location: finalData.location,
          // ... map all fields
        },
        preferences: {
          skills: finalData.skills,
          interests: finalData.interests,
          causes: finalData.causes,
          // ... etc
        }
      });
      
      onComplete();
    } catch (error) {
      console.error('Onboarding completion failed:', error);
      // Handle error appropriately
    }
  };
  
  // Copy V2's render logic but use our components
  return (
    <div className="min-h-screen bg-primary dark:bg-dark-bg">
      {/* Copy V2's layout and progress bar */}
      <PxProgress value={progress} />
      
      {/* Render current step component */}
      <CurrentStepComponent
        data={data}
        updateData={setData}
        onNext={handleNext}
      />
    </div>
  );
};
```

#### **2.2: Individual Step Components**

##### **WelcomeStep Migration**
```typescript
// Create: apps/web/components/onboarding/steps/WelcomeStep.tsx
// Copy from V2 but remove i18n if not available

import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';

interface WelcomeStepProps {
  onNext: () => void;
}

export const WelcomeStep: React.FC<WelcomeStepProps> = ({ onNext }) => {
  return (
    <PxCard className="max-w-2xl mx-auto">
      {/* Copy V2's welcome content but adapt styling */}
      <div className="text-center space-y-6">
        <h1 className="text-2xl font-pixel text-primary">
          Welcome to Seraaj! 
        </h1>
        <p className="text-ink dark:text-white">
          Let's set up your hero profile and find the perfect quests for you.
        </p>
        
        <PxButton 
          variant="primary" 
          onClick={onNext}
          className="hover:shadow-px-glow"
        >
          Start Your Journey
        </PxButton>
      </div>
    </PxCard>
  );
};
```

##### **UserTypeStep Migration**  
```typescript
// Create: apps/web/components/onboarding/steps/UserTypeStep.tsx
// This is critical - determines volunteer vs organization flow

import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';

interface UserTypeStepProps {
  data: OnboardingData;
  updateData: (updates: Partial<OnboardingData>) => void;
  onNext: () => void;
}

export const UserTypeStep: React.FC<UserTypeStepProps> = ({ 
  data, 
  updateData, 
  onNext 
}) => {
  const selectUserType = (type: 'volunteer' | 'organization') => {
    updateData({ userType: type });
  };

  return (
    <PxCard className="max-w-2xl mx-auto">
      <div className="space-y-6">
        <h2 className="text-xl font-pixel text-center">Choose Your Path</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Volunteer Option */}
          <PxCard 
            className={`cursor-pointer border-2 ${
              data.userType === 'volunteer' 
                ? 'border-primary bg-primary/10' 
                : 'border-gray-300'
            }`}
            onClick={() => selectUserType('volunteer')}
          >
            <div className="text-center p-6">
              <div className="text-4xl mb-4">🦸‍♂️</div>
              <h3 className="font-pixel text-lg mb-2">I'm a Hero</h3>
              <p className="text-sm">I want to volunteer and help causes</p>
            </div>
          </PxCard>
          
          {/* Organization Option */}
          <PxCard 
            className={`cursor-pointer border-2 ${
              data.userType === 'organization' 
                ? 'border-primary bg-primary/10' 
                : 'border-gray-300'
            }`}
            onClick={() => selectUserType('organization')}
          >
            <div className="text-center p-6">
              <div className="text-4xl mb-4">🏰</div>
              <h3 className="font-pixel text-lg mb-2">I'm a Quest Giver</h3>
              <p className="text-sm">I represent an organization seeking volunteers</p>
            </div>
          </PxCard>
        </div>
        
        <div className="text-center">
          <PxButton
            variant="primary"
            onClick={onNext}
            disabled={!data.userType}
          >
            Continue
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
};
```

##### **ProfileStep Migration**
```typescript
// Create: apps/web/components/onboarding/steps/ProfileStep.tsx
// Copy V2's form fields but use our components

import React from 'react';
import { PxInput, PxButton, PxCard } from '@seraaj/ui';

export const ProfileStep: React.FC<ProfileStepProps> = ({
  data,
  updateData,
  onNext
}) => {
  return (
    <PxCard className="max-w-2xl mx-auto">
      <form onSubmit={(e) => { e.preventDefault(); onNext(); }}>
        <div className="space-y-6">
          <h2 className="text-xl font-pixel text-center">
            {data.userType === 'volunteer' ? 'Hero Profile' : 'Organization Profile'}
          </h2>
          
          {/* Copy V2's form fields */}
          <PxInput
            label="Full Name"
            value={data.name}
            onChange={(e) => updateData({ name: e.target.value })}
            required
          />
          
          <PxInput
            label="Location"
            value={data.location}
            onChange={(e) => updateData({ location: e.target.value })}
            required
          />
          
          <div>
            <label className="block text-sm font-pixel mb-2">Bio</label>
            <textarea
              value={data.bio}
              onChange={(e) => updateData({ bio: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg"
              rows={4}
              placeholder={
                data.userType === 'volunteer' 
                  ? "Tell us about yourself and what motivates you to volunteer..."
                  : "Describe your organization and its mission..."
              }
            />
          </div>
          
          {/* Conditional fields based on userType */}
          {data.userType === 'organization' && (
            <>
              <PxInput
                label="Organization Name"
                value={data.organizationName || ''}
                onChange={(e) => updateData({ organizationName: e.target.value })}
                required
              />
              
              <select
                value={data.organizationType || ''}
                onChange={(e) => updateData({ organizationType: e.target.value })}
                className="w-full px-4 py-3 border rounded-lg"
              >
                <option value="">Select Organization Type</option>
                <option value="nonprofit">Nonprofit</option>
                <option value="ngo">NGO</option>
                <option value="charity">Charity</option>
                <option value="government">Government</option>
                <option value="social-enterprise">Social Enterprise</option>
              </select>
            </>
          )}
          
          <PxButton
            variant="primary"
            type="submit"
            disabled={!data.name || !data.location}
            className="w-full"
          >
            Continue
          </PxButton>
        </div>
      </form>
    </PxCard>
  );
};
```

##### **PreferencesStep Migration**
```typescript
// Create: apps/web/components/onboarding/steps/PreferencesStep.tsx
// Copy V2's chip-based selection but adapt to our styling

import React from 'react';
import { PxChip, PxButton, PxCard } from '@seraaj/ui';

export const PreferencesStep: React.FC<PreferencesStepProps> = ({
  data,
  updateData,
  onNext
}) => {
  // Copy V2's predefined options
  const skills = [
    'Teaching', 'Mentoring', 'Social Media', 'Graphic Design', 'Writing',
    'Photography', 'Video Editing', 'Web Development', 'Marketing',
    // ... copy full list from V2
  ];
  
  const causes = [
    'Education', 'Health', 'Environment', 'Poverty', 'Human Rights',
    // ... copy full list from V2
  ];
  
  const toggleSkill = (skill: string) => {
    const currentSkills = data.skills || [];
    const updatedSkills = currentSkills.includes(skill)
      ? currentSkills.filter(s => s !== skill)
      : [...currentSkills, skill];
    updateData({ skills: updatedSkills });
  };
  
  const toggleCause = (cause: string) => {
    const currentCauses = data.causes || [];
    const updatedCauses = currentCauses.includes(cause)
      ? currentCauses.filter(c => c !== cause)
      : [...currentCauses, cause];
    updateData({ causes: updatedCauses });
  };
  
  return (
    <PxCard className="max-w-4xl mx-auto">
      <div className="space-y-8">
        <h2 className="text-xl font-pixel text-center">
          {data.userType === 'volunteer' ? 'Your Skills & Interests' : 'Areas of Focus'}
        </h2>
        
        {/* Skills Section */}
        <div className="space-y-4">
          <h3 className="font-pixel text-electric-teal">Skills</h3>
          <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
            {skills.map(skill => (
              <PxChip
                key={skill}
                variant={data.skills?.includes(skill) ? 'selected' : 'default'}
                onClick={() => toggleSkill(skill)}
                className="cursor-pointer"
              >
                {skill}
              </PxChip>
            ))}
          </div>
        </div>
        
        {/* Causes Section */}
        <div className="space-y-4">
          <h3 className="font-pixel text-electric-teal">Causes You Care About</h3>
          <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
            {causes.map(cause => (
              <PxChip
                key={cause}
                variant={data.causes?.includes(cause) ? 'selected' : 'default'}
                onClick={() => toggleCause(cause)}
                className="cursor-pointer"
              >
                {cause}
              </PxChip>
            ))}
          </div>
        </div>
        
        {/* Availability Section (for volunteers) */}
        {data.userType === 'volunteer' && (
          <div className="space-y-4">
            <h3 className="font-pixel text-electric-teal">Availability</h3>
            <select
              value={data.availability || ''}
              onChange={(e) => updateData({ availability: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg"
            >
              <option value="">Select your availability</option>
              <option value="1-2 hours/week">1-2 hours/week</option>
              <option value="3-5 hours/week">3-5 hours/week</option>
              <option value="6-10 hours/week">6-10 hours/week</option>
              <option value="10+ hours/week">10+ hours/week</option>
              <option value="weekends-only">Weekends only</option>
              <option value="flexible">Flexible schedule</option>
            </select>
          </div>
        )}
        
        <PxButton
          variant="primary"
          onClick={onNext}
          disabled={!data.causes?.length}
          className="w-full"
        >
          Complete Setup
        </PxButton>
      </div>
    </PxCard>
  );
};
```

##### **CompletionStep Migration**
```typescript
// Create: apps/web/components/onboarding/steps/CompletionStep.tsx
// Success screen with next steps

import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';

export const CompletionStep: React.FC<CompletionStepProps> = ({ 
  data, 
  onComplete 
}) => {
  return (
    <PxCard className="max-w-2xl mx-auto text-center">
      <div className="space-y-6">
        <div className="text-6xl mb-4">🎉</div>
        
        <h2 className="text-2xl font-pixel text-primary">
          Welcome to Seraaj, {data.name}!
        </h2>
        
        <p className="text-ink dark:text-white">
          {data.userType === 'volunteer' 
            ? "Your hero profile is complete! Let's find some amazing quests for you."
            : "Your organization profile is set up! Ready to post some quests for heroes?"
          }
        </p>
        
        <div className="bg-primary/10 border border-primary rounded-lg p-4">
          <h3 className="font-pixel text-sm mb-2">What's Next?</h3>
          <ul className="text-sm text-left space-y-1">
            {data.userType === 'volunteer' ? (
              <>
                <li>• Browse and apply to volunteer opportunities</li>
                <li>• Get matched with organizations that need your skills</li>
                <li>• Track your volunteer hours and impact</li>
              </>
            ) : (
              <>
                <li>• Post volunteer opportunities for your organization</li>
                <li>• Review and manage volunteer applications</li>
                <li>• Track volunteer engagement and impact</li>
              </>
            )}
          </ul>
        </div>
        
        <PxButton
          variant="primary"
          onClick={onComplete}
          className="hover:shadow-px-glow"
        >
          {data.userType === 'volunteer' ? 'Find Quests' : 'Post Opportunities'}
        </PxButton>
      </div>
    </PxCard>
  );
};
```

### **Step 3: Integration with Event Architecture**

#### **3.1: Update AuthContext Integration**
```typescript
// In apps/web/contexts/AuthContext.tsx
// Make sure it can handle the rich onboarding data

interface AuthContextType {
  // ... existing methods
  
  // Add method to handle onboarding completion
  completeOnboarding: (onboardingData: OnboardingData) => Promise<void>;
}

// Implementation in AuthContext:
const completeOnboarding = async (onboardingData: OnboardingData) => {
  try {
    // Transform onboarding data into events
    const profileUpdate = {
      userType: onboardingData.userType,
      profile: {
        fullName: onboardingData.name,
        bio: onboardingData.bio,
        location: onboardingData.location,
        // ... map other fields
      }
    };
    
    const preferences = {
      skills: onboardingData.skills,
      interests: onboardingData.interests,
      causes: onboardingData.causes,
      availability: onboardingData.availability,
    };
    
    // Send to BFF which will emit proper events
    await bffSdk.profiles.updateProfile(profileUpdate);
    await bffSdk.profiles.setPreferences(preferences);
    
    // Update local state
    setUser(prevUser => ({ 
      ...prevUser, 
      ...profileUpdate.profile,
      onboardingComplete: true 
    }));
    
  } catch (error) {
    console.error('Onboarding completion failed:', error);
    throw error;
  }
};
```

#### **3.2: Update Routing**
```typescript
// In apps/web/app/onboarding/page.tsx
// Replace current simple onboarding with new rich version

'use client';

import { OnboardingFlow } from '@/components/onboarding/OnboardingFlow';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function OnboardingPage() {
  const { completeOnboarding } = useAuth();
  const router = useRouter();
  
  const handleOnboardingComplete = async (data: OnboardingData) => {
    try {
      await completeOnboarding(data);
      
      // Redirect based on user type
      if (data.userType === 'volunteer') {
        router.push('/opportunities');
      } else {
        router.push('/organization/dashboard');
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      // Handle error (show toast, etc.)
    }
  };
  
  return (
    <OnboardingFlow onComplete={handleOnboardingComplete} />
  );
}
```

## 🧪 **TESTING STRATEGY**

### **Unit Tests**
```typescript
// Create: apps/web/components/onboarding/__tests__/
// Test each step component:
// - Renders correctly
// - Form validation works
// - Data updates properly
// - Navigation works

// Example test:
describe('UserTypeStep', () => {
  it('should update user type when selection made', () => {
    const mockUpdateData = jest.fn();
    render(<UserTypeStep data={{}} updateData={mockUpdateData} onNext={jest.fn()} />);
    
    fireEvent.click(screen.getByText("I'm a Hero"));
    expect(mockUpdateData).toHaveBeenCalledWith({ userType: 'volunteer' });
  });
});
```

### **Integration Tests**
```typescript
// Test complete onboarding flow:
// 1. User starts onboarding
// 2. Progresses through all steps
// 3. Data is properly saved via events
// 4. Profile is created in database
// 5. User is redirected appropriately
```

### **Manual Testing Checklist**
- [ ] Can complete volunteer onboarding flow
- [ ] Can complete organization onboarding flow  
- [ ] Data persists correctly between steps
- [ ] Back/forward navigation works
- [ ] Form validation prevents invalid submissions
- [ ] Events are emitted to backend services
- [ ] Profile data appears in database
- [ ] Redirects work after completion

## 📝 **ACCEPTANCE CRITERIA**

### **Must Have**
- [ ] All 5 onboarding steps migrated and functional
- [ ] Both volunteer and organization flows work
- [ ] Integration with current AuthContext maintained
- [ ] Events properly flow to backend services  
- [ ] Profile data persists correctly
- [ ] No breaking changes to existing auth flow

### **Should Have**
- [ ] Form validation matches V2 behavior
- [ ] Skills/causes chip selection works smoothly
- [ ] Progress indicator shows current step
- [ ] Back navigation preserves entered data
- [ ] Error handling for API failures

### **Could Have**
- [ ] Animations/transitions from V2
- [ ] Save draft functionality  
- [ ] Skip steps option for certain user types
- [ ] A/B test different onboarding flows

## 🚨 **ROLLBACK PLAN**
```bash
# If new onboarding breaks auth:
git stash  # Save work in progress
git checkout -- apps/web/components/onboarding/
git checkout -- apps/web/contexts/AuthContext.tsx
git checkout -- apps/web/app/onboarding/page.tsx

# Test that original auth flow works
# Then fix issues in new onboarding before re-applying
```

## ⏱️ **ESTIMATED TIME**
- **Analysis and Planning**: 1 hour
- **Component Migration**: 2 hours  
- **Integration Work**: 1 hour
- **Testing**: 1 hour
- **Total**: 5 hours

## 👥 **DEPENDENCIES**
- Issue #1 (Px Components) should be completed first
- Current Auth service must support profile events
- BFF SDK must expose profile update methods

## 🏁 **DEFINITION OF DONE**
- All onboarding steps work for both user types
- Events flow correctly to backend services
- Profile data persists and appears in user dashboard
- No regressions in existing authentication
- Code reviewed and tested
- Documentation updated