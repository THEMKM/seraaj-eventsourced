# Complete Onboarding: Skills & Causes Selection Step

## 📋 **Task Description**
Add the skills and causes selection step to the onboarding flow. This will be step 3 in the 5-step onboarding process, allowing users to select their skills and causes with a chip-based interface.

## 🎯 **Exact Steps to Follow**

### Step 1: Create the SkillsCausesStep component
Create `apps/web/components/onboarding/steps/SkillsCausesStep.tsx`:

```typescript
import React, { useState } from 'react';
import { PxButton, PxCard, PxChip } from '@seraaj/ui';

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

interface SkillsCausesStepProps {
  userType: 'volunteer' | 'organization' | null;
  selectedSkills: string[];
  selectedCauses: string[];
  onSkillsChange: (skills: string[]) => void;
  onCausesChange: (causes: string[]) => void;
  onNext: () => void;
  onBack: () => void;
}

export const SkillsCausesStep: React.FC<SkillsCausesStepProps> = ({
  userType,
  selectedSkills,
  selectedCauses,
  onSkillsChange,
  onCausesChange,
  onNext,
  onBack
}) => {
  const [customSkill, setCustomSkill] = useState('');
  const [customCause, setCustomCause] = useState('');

  const toggleSkill = (skill: string) => {
    const newSkills = selectedSkills.includes(skill)
      ? selectedSkills.filter(s => s !== skill)
      : [...selectedSkills, skill];
    onSkillsChange(newSkills);
  };

  const toggleCause = (cause: string) => {
    const newCauses = selectedCauses.includes(cause)
      ? selectedCauses.filter(c => c !== cause)
      : [...selectedCauses, cause];
    onCausesChange(newCauses);
  };

  const addCustomSkill = () => {
    if (customSkill.trim() && !selectedSkills.includes(customSkill.trim())) {
      onSkillsChange([...selectedSkills, customSkill.trim()]);
      setCustomSkill('');
    }
  };

  const addCustomCause = () => {
    if (customCause.trim() && !selectedCauses.includes(customCause.trim())) {
      onCausesChange([...selectedCauses, customCause.trim()]);
      setCustomCause('');
    }
  };

  const canProceed = selectedSkills.length >= 1 && selectedCauses.length >= 1;

  return (
    <PxCard className="max-w-4xl mx-auto p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-pixel text-primary mb-4">
          {userType === 'volunteer' ? '⚡ Your Heroic Abilities ⚡' : '🎯 Organization Focus Areas 🎯'}
        </h2>
        <p className="text-white text-lg">
          {userType === 'volunteer' 
            ? 'Select your skills and causes you care about (minimum 1 each)'
            : 'Choose your organization\'s areas of expertise and focus'
          }
        </p>
      </div>

      <div className="space-y-8">
        {/* Skills Selection */}
        <div>
          <div className="flex items-center gap-4 mb-4">
            <h3 className="text-lg font-pixel text-electric-teal">
              🛠️ {userType === 'volunteer' ? 'Skills' : 'Expertise Areas'} ({selectedSkills.length} selected)
            </h3>
            <div className="flex-1 border-b border-electric-teal/30"></div>
          </div>
          
          {/* Predefined Skills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {PREDEFINED_SKILLS.map(skill => (
              <PxChip
                key={skill}
                variant={selectedSkills.includes(skill) ? 'selected' : 'default'}
                onClick={() => toggleSkill(skill)}
                className="cursor-pointer"
                size="sm"
              >
                {skill}
              </PxChip>
            ))}
          </div>

          {/* Custom Skill Input */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add custom skill..."
              value={customSkill}
              onChange={(e) => setCustomSkill(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addCustomSkill()}
              className="flex-1 px-4 py-2 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
            />
            <PxButton 
              variant="secondary" 
              size="sm"
              onClick={addCustomSkill}
              disabled={!customSkill.trim()}
            >
              Add
            </PxButton>
          </div>
        </div>

        {/* Causes Selection */}
        <div>
          <div className="flex items-center gap-4 mb-4">
            <h3 className="text-lg font-pixel text-electric-teal">
              ❤️ Causes You Care About ({selectedCauses.length} selected)
            </h3>
            <div className="flex-1 border-b border-electric-teal/30"></div>
          </div>
          
          {/* Predefined Causes */}
          <div className="flex flex-wrap gap-2 mb-4">
            {PREDEFINED_CAUSES.map(cause => (
              <PxChip
                key={cause}
                variant={selectedCauses.includes(cause) ? 'selected' : 'default'}
                onClick={() => toggleCause(cause)}
                className="cursor-pointer"
                size="sm"
              >
                {cause}
              </PxChip>
            ))}
          </div>

          {/* Custom Cause Input */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add custom cause..."
              value={customCause}
              onChange={(e) => setCustomCause(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addCustomCause()}
              className="flex-1 px-4 py-2 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
            />
            <PxButton 
              variant="secondary" 
              size="sm"
              onClick={addCustomCause}
              disabled={!customCause.trim()}
            >
              Add
            </PxButton>
          </div>
        </div>

        {/* Requirement Notice */}
        {(!canProceed) && (
          <div className="bg-warning/10 border border-warning rounded-lg p-4 text-center">
            <p className="text-warning text-sm">
              Please select at least 1 skill and 1 cause to continue
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-electric-teal/30">
        <PxButton variant="secondary" onClick={onBack}>
          ← Back
        </PxButton>
        <PxButton 
          variant="primary" 
          onClick={onNext}
          disabled={!canProceed}
        >
          Continue Journey →
        </PxButton>
      </div>
    </PxCard>
  );
};
```

### Step 2: Update OnboardingFlow to include the new step
Modify `apps/web/components/onboarding/OnboardingFlow.tsx`:

```typescript
// Add the import
import { SkillsCausesStep } from './steps/SkillsCausesStep';

// Update the OnboardingData interface
export interface OnboardingData {
  userType: 'volunteer' | 'organization' | null;
  name: string;
  email: string;
  location: string;
  bio: string;
  skills: string[];        // Add this
  causes: string[];        // Add this
  organizationName?: string;
  organizationType?: string;
  // ... keep existing fields
}

// Update the component
export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    userType: null,
    name: '',
    email: '',
    location: '',
    bio: '',
    skills: [],              // Initialize
    causes: [],              // Initialize
  });

  const handleSkillsChange = (skills: string[]) => {
    setData(prev => ({ ...prev, skills }));
  };

  const handleCausesChange = (causes: string[]) => {
    setData(prev => ({ ...prev, causes }));
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
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
            onTypeSelect={(type) => setData(prev => ({ ...prev, userType: type }))}
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
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <SkillsCausesStep
            userType={data.userType}
            selectedSkills={data.skills}
            selectedCauses={data.causes}
            onSkillsChange={handleSkillsChange}
            onCausesChange={handleCausesChange}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <CompletionStep 
            data={data}
            onComplete={() => onComplete(data)}
            onBack={handleBack}
          />
        );
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

### Step 3: Create PxChip component if not exists
If PxChip doesn't exist, create `packages/ui/src/components/Chip/Chip.tsx`:

```typescript
import React from 'react';
import { clsx } from 'clsx';

export interface ChipProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'selected';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

export const Chip: React.FC<ChipProps> = ({
  variant = 'default',
  size = 'md',
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={clsx(
        'inline-flex items-center px-3 py-1 rounded-full font-pixel cursor-pointer transition-all border-2',
        {
          // Default state
          'bg-gray-800 text-gray-300 border-gray-600 hover:border-electric-teal hover:text-white': variant === 'default',
          // Selected state  
          'bg-primary text-white border-primary shadow-lg transform scale-105': variant === 'selected',
          // Sizes
          'text-xs px-2 py-1': size === 'sm',
          'text-sm px-3 py-2': size === 'md',
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
```

And export it in `packages/ui/src/index.ts`:
```typescript
export { Chip as PxChip } from './components/Chip/Chip';
export type { ChipProps as PxChipProps } from './components/Chip/Chip';
```

### Step 4: Create a CompletionStep placeholder
Create `apps/web/components/onboarding/steps/CompletionStep.tsx`:

```typescript
import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { OnboardingData } from '../OnboardingFlow';

interface CompletionStepProps {
  data: OnboardingData;
  onComplete: () => void;
  onBack: () => void;
}

export const CompletionStep: React.FC<CompletionStepProps> = ({
  data,
  onComplete,
  onBack
}) => {
  return (
    <PxCard className="max-w-2xl mx-auto p-8 text-center">
      <div className="text-6xl mb-6">🎉</div>
      <h2 className="text-2xl font-pixel text-primary mb-4">
        Welcome to the Quest, {data.name}!
      </h2>
      <p className="text-white text-lg mb-8">
        Your {data.userType === 'volunteer' ? 'heroic' : 'organizational'} profile is ready. 
        Time to {data.userType === 'volunteer' ? 'find amazing quests' : 'create opportunities'}!
      </p>
      
      <div className="bg-dark-surface p-6 rounded-lg mb-8">
        <h3 className="font-pixel text-electric-teal mb-4">Profile Summary:</h3>
        <div className="text-left space-y-2 text-sm text-gray-300">
          <p><strong>Type:</strong> {data.userType === 'volunteer' ? 'Hero' : 'Quest Giver'}</p>
          <p><strong>Skills:</strong> {data.skills.join(', ')}</p>
          <p><strong>Causes:</strong> {data.causes.join(', ')}</p>
          <p><strong>Location:</strong> {data.location}</p>
        </div>
      </div>

      <div className="flex justify-between">
        <PxButton variant="secondary" onClick={onBack}>
          ← Back to Edit
        </PxButton>
        <PxButton variant="primary" size="lg" onClick={onComplete}>
          Start My Journey! 🚀
        </PxButton>
      </div>
    </PxCard>
  );
};
```

## ✅ **Definition of Done**
- [ ] SkillsCausesStep component renders predefined skills and causes as chips
- [ ] Selected chips show visual feedback (different styling)
- [ ] Custom skills/causes can be added via text input
- [ ] Minimum 1 skill and 1 cause required to proceed
- [ ] Navigation buttons work (back/next)
- [ ] OnboardingFlow includes this as step 3 of 5
- [ ] Progress bar updates correctly
- [ ] PxChip component exists and works
- [ ] CompletionStep shows profile summary

## 🧪 **How to Test**
1. Navigate to `/onboarding` and complete steps 1-2
2. Reach the Skills & Causes step
3. Click skills/causes to select them (should show visual feedback)
4. Try adding custom skills/causes
5. Verify you can't proceed without minimum selections
6. Test back/next navigation
7. Complete onboarding and see profile summary
8. Verify data is saved correctly

**This should take 3-4 hours to implement and test thoroughly.**