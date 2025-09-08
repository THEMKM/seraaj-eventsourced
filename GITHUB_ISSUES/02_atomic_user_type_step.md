# Add User Type Selection to Onboarding

## 📋 **Task Description**
Enhance the existing onboarding flow to include a user type selection step where users choose between being a "Hero" (volunteer) or "Quest Giver" (organization).

## 🎯 **Exact Steps to Follow**

### Step 1: Update the existing onboarding types
Modify `apps/web/components/onboarding/OnboardingFlow.tsx` to add user type:

```typescript
// Add this interface to the existing file
export interface OnboardingData {
  userType: 'volunteer' | 'organization' | null;
  name: string;
  email: string;
  location: string;
  bio: string;
  skills: string[];
  causes: string[];
  // ... keep existing fields
}
```

### Step 2: Create the UserTypeStep component
Create `apps/web/components/onboarding/steps/UserTypeStep.tsx`:

```typescript
import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';

interface UserTypeStepProps {
  selectedType: 'volunteer' | 'organization' | null;
  onTypeSelect: (type: 'volunteer' | 'organization') => void;
  onNext: () => void;
}

export const UserTypeStep: React.FC<UserTypeStepProps> = ({
  selectedType,
  onTypeSelect,
  onNext
}) => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-pixel text-primary mb-4">
          Choose Your Path
        </h2>
        <p className="text-white text-lg">
          Are you here to volunteer or do you represent an organization?
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Volunteer Option */}
        <PxCard 
          className={`cursor-pointer border-2 transition-all ${
            selectedType === 'volunteer' 
              ? 'border-primary bg-primary/10' 
              : 'border-gray-600 hover:border-primary/50'
          }`}
          onClick={() => onTypeSelect('volunteer')}
        >
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🦸‍♂️</div>
            <h3 className="text-xl font-pixel text-primary mb-2">
              I'm a Hero
            </h3>
            <p className="text-white mb-4">
              I want to volunteer and help causes I care about
            </p>
            <ul className="text-sm text-gray-300 text-left space-y-1">
              <li>• Find perfect volunteer matches</li>
              <li>• Track your impact and hours</li>
              <li>• Connect with organizations</li>
              <li>• Build your heroic reputation</li>
            </ul>
          </div>
        </PxCard>

        {/* Organization Option */}
        <PxCard 
          className={`cursor-pointer border-2 transition-all ${
            selectedType === 'organization' 
              ? 'border-primary bg-primary/10' 
              : 'border-gray-600 hover:border-primary/50'
          }`}
          onClick={() => onTypeSelect('organization')}
        >
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🏰</div>
            <h3 className="text-xl font-pixel text-primary mb-2">
              I'm a Quest Giver
            </h3>
            <p className="text-white mb-4">
              I represent an organization seeking volunteers
            </p>
            <ul className="text-sm text-gray-300 text-left space-y-1">
              <li>• Post volunteer opportunities</li>
              <li>• Find qualified heroes</li>
              <li>• Manage applications</li>
              <li>• Track organizational impact</li>
            </ul>
          </div>
        </PxCard>
      </div>

      <div className="text-center">
        <PxButton
          variant="primary"
          size="lg"
          onClick={onNext}
          disabled={!selectedType}
        >
          Continue Your Journey
        </PxButton>
      </div>
    </div>
  );
};
```

### Step 3: Update OnboardingFlow to include the new step
Modify `apps/web/components/onboarding/OnboardingFlow.tsx`:

```typescript
// Add the import
import { UserTypeStep } from './steps/UserTypeStep';

// Update the component to include user type selection
export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    userType: null, // Add this
    name: '',
    email: '',
    // ... keep existing fields
  });

  const handleUserTypeSelect = (type: 'volunteer' | 'organization') => {
    setData(prev => ({ ...prev, userType: type }));
  };

  const handleNext = () => {
    if (currentStep < 4) { // Update total steps
      setCurrentStep(currentStep + 1);
    } else {
      onComplete(data);
    }
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0:
        return <WelcomeStep onNext={handleNext} />;
      case 1:
        return (
          <UserTypeStep 
            selectedType={data.userType}
            onTypeSelect={handleUserTypeSelect}
            onNext={handleNext}
          />
        );
      case 2:
        return (
          <ProfileStep 
            userType={data.userType}
            data={data}
            onDataUpdate={(updates) => setData(prev => ({ ...prev, ...updates }))}
            onNext={handleNext}
          />
        );
      // ... handle other steps
      default:
        return <WelcomeStep onNext={handleNext} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink p-6">
      {/* Progress indicator */}
      <div className="max-w-2xl mx-auto mb-8">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-pixel text-white">
            Step {currentStep + 1} of 5
          </span>
          <span className="text-sm font-pixel text-white">
            {Math.round(((currentStep + 1) / 5) * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentStep + 1) / 5) * 100}%` }}
          ></div>
        </div>
      </div>

      {renderCurrentStep()}
    </div>
  );
};
```

### Step 4: Update ProfileStep to handle user types
Modify the existing ProfileStep to show different fields based on user type:

```typescript
// In apps/web/components/onboarding/steps/ProfileStep.tsx
interface ProfileStepProps {
  userType: 'volunteer' | 'organization' | null;
  data: OnboardingData;
  onDataUpdate: (updates: Partial<OnboardingData>) => void;
  onNext: () => void;
}

export const ProfileStep: React.FC<ProfileStepProps> = ({ 
  userType, 
  data, 
  onDataUpdate, 
  onNext 
}) => {
  return (
    <PxCard className="max-w-2xl mx-auto p-8">
      <h2 className="text-2xl font-pixel text-primary text-center mb-8">
        {userType === 'volunteer' ? 'Hero Profile' : 'Organization Profile'}
      </h2>
      
      {/* Common fields */}
      <div className="space-y-6">
        <PxInput
          label="Full Name"
          value={data.name}
          onChange={(e) => onDataUpdate({ name: e.target.value })}
          required
        />
        
        {/* Conditional fields for organizations */}
        {userType === 'organization' && (
          <>
            <PxInput
              label="Organization Name"
              value={data.organizationName || ''}
              onChange={(e) => onDataUpdate({ organizationName: e.target.value })}
              required
            />
            <select
              className="w-full px-4 py-3 border-2 border-ink rounded-lg bg-dark-surface text-white"
              value={data.organizationType || ''}
              onChange={(e) => onDataUpdate({ organizationType: e.target.value })}
            >
              <option value="">Select Organization Type</option>
              <option value="nonprofit">Nonprofit</option>
              <option value="ngo">NGO</option>
              <option value="government">Government</option>
              <option value="social-enterprise">Social Enterprise</option>
            </select>
          </>
        )}
        
        {/* Continue with existing fields */}
      </div>
    </PxCard>
  );
};
```

### Step 5: Update the AuthContext integration
Modify `apps/web/contexts/AuthContext.tsx` to handle user type in profile updates:

```typescript
// Add to the profile update method
const updateUserProfile = async (profileData: any) => {
  try {
    const updatePayload = {
      ...profileData,
      userType: profileData.userType, // Include user type
    };
    
    await bffSdk.profiles.updateProfile(updatePayload);
    
    setUser(prevUser => ({
      ...prevUser,
      ...updatePayload,
      onboardingComplete: true
    }));
  } catch (error) {
    console.error('Profile update failed:', error);
    throw error;
  }
};
```

## ✅ **Definition of Done**
- [ ] UserTypeStep component renders both options correctly
- [ ] Clicking on an option selects it visually
- [ ] Cannot proceed without selecting a type
- [ ] OnboardingFlow includes the new step as step 2
- [ ] Progress indicator shows 5 total steps
- [ ] ProfileStep shows different fields for volunteers vs organizations
- [ ] User type is saved in onboarding data
- [ ] Navigation between steps works correctly

## 🧪 **How to Test**
1. Navigate to `/onboarding` in the app
2. Complete the welcome step
3. See the user type selection screen
4. Click on both options to see selection state
5. Verify you can't proceed without selecting
6. Select "Hero" and continue - should see volunteer profile form
7. Go back and select "Quest Giver" - should see organization fields
8. Complete onboarding and verify user type is saved

**This should take 2-3 hours to implement and test.**