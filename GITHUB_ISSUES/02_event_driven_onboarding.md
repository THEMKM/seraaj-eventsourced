# Issue #2: Build Event-Driven Gaming Onboarding System

## 🎯 **AUTONOMOUS AGENT OBJECTIVE**
You must architect and implement a sophisticated 5-step onboarding system for a volunteer management platform with gaming aesthetics. The system must handle both volunteer ("hero") and organization ("quest giver") user types, persist all data through event sourcing, and provide a polished user experience comparable to AAA gaming onboarding flows.

## 🤖 **AGENT CONTEXT & CONSTRAINTS**
- **Platform**: Event-sourced volunteer management system with gaming theme
- **Architecture**: React + TypeScript + Event-driven backend via BFF layer
- **User Types**: Volunteers (heroes) and Organizations (quest givers)
- **Data Flow**: UI → BFF → Auth Service → Event Store → Database Projections
- **UX Standard**: Gaming-quality progressive disclosure with visual polish
- **Performance**: < 3 seconds per step transition, offline-capable forms

## 📂 **EXACT FILE STRUCTURE TO CREATE**
```
apps/web/components/onboarding/
├── OnboardingFlow.tsx              # Main coordinator component
├── OnboardingProvider.tsx          # State management context
├── steps/
│   ├── WelcomeStep.tsx             # Step 1: Welcome & introduction
│   ├── UserTypeStep.tsx            # Step 2: Hero vs Quest Giver selection
│   ├── ProfileStep.tsx             # Step 3: Basic profile information
│   ├── PreferencesStep.tsx         # Step 4: Skills, causes, availability
│   └── CompletionStep.tsx          # Step 5: Success & next actions
├── components/
│   ├── StepIndicator.tsx           # Progress visualization
│   ├── NavigationControls.tsx     # Back/Next/Skip buttons
│   ├── SkillSelector.tsx           # Multi-select skill chips
│   ├── CauseSelector.tsx           # Multi-select cause chips
│   └── LocationSelector.tsx        # Location autocomplete
├── hooks/
│   ├── useOnboardingProgress.ts    # Progress management
│   ├── useProfileValidation.ts     # Form validation
│   └── useEventPersistence.ts      # Event sourcing integration
├── utils/
│   ├── validationSchemas.ts        # Zod validation schemas
│   ├── eventMappers.ts             # Transform UI data to events
│   └── progressCalculator.ts       # Step completion logic
└── types/
    ├── onboarding.ts               # Onboarding-specific types
    └── events.ts                   # Event type definitions
```

## 🗺️ **ONBOARDING FLOW SPECIFICATIONS**

### **Step 1: Welcome Step**
```typescript
interface WelcomeStepProps {
  onNext: () => void;
  onSkip?: () => void;
}

// Required Features:
// - Gaming-themed welcome animation with particle effects
// - Platform value proposition explanation
// - Hero's journey metaphor introduction
// - Smooth entrance animations with sound effects (optional)
// - Skip option for returning users
// - Responsive design for all screen sizes
// - Accessibility: proper heading hierarchy, screen reader support
```

**Content Specifications:**
```typescript
const welcomeContent = {
  title: "Welcome to Seraaj, Future Hero! 🦸‍♀️",
  subtitle: "Your quest to change the world begins here",
  description: [
    "Join thousands of heroes making real impact in their communities",
    "Discover perfectly matched volunteer opportunities",
    "Track your heroic journey and unlock achievements",
    "Connect with organizations that need your unique powers"
  ],
  callToAction: "Begin Your Hero's Journey",
  skipOption: "I'm already a hero (skip setup)"
};
```

### **Step 2: User Type Selection**
```typescript
interface UserTypeStepProps {
  selectedType: 'volunteer' | 'organization' | null;
  onTypeSelect: (type: 'volunteer' | 'organization') => void;
  onNext: () => void;
  onBack: () => void;
}

// Required Features:
// - Large, visually distinct selection cards
// - Hover animations with gaming effects
// - Clear explanation of each path
// - Dynamic content preview based on selection
// - Gaming character avatars/icons
// - Keyboard navigation support
// - Progress indication (2/5 steps)
```

**User Type Definitions:**
```typescript
const userTypes = {
  volunteer: {
    title: "I'm a Hero 🦸‍♂️",
    subtitle: "I want to volunteer and make impact",
    description: "Join quests, gain experience points, unlock achievements",
    benefits: [
      "Discover perfect volunteer matches",
      "Track your impact and hours",
      "Connect with like-minded heroes",
      "Build your heroic reputation"
    ],
    icon: "🦸‍♂️",
    gradient: "bg-gradient-to-br from-blue-500 to-purple-600"
  },
  organization: {
    title: "I'm a Quest Giver 🏰",
    subtitle: "I represent an organization seeking heroes",
    description: "Post quests, manage heroes, track organizational impact",
    benefits: [
      "Post volunteer opportunities",
      "Find qualified heroes for your missions",
      "Manage applications and volunteers",
      "Track organizational impact"
    ],
    icon: "🏰",
    gradient: "bg-gradient-to-br from-emerald-500 to-teal-600"
  }
};
```

### **Step 3: Profile Step**
```typescript
interface ProfileStepData {
  // Personal Information
  fullName: string;
  email: string; // Pre-filled from auth
  location: string;
  bio: string;
  avatar?: File;
  
  // Organization-specific fields (conditional)
  organizationName?: string;
  organizationType?: string;
  organizationSize?: string;
  website?: string;
  
  // Additional fields
  phoneNumber?: string;
  dateOfBirth?: string; // For age verification
  preferredLanguage?: string;
}

interface ProfileStepProps {
  data: ProfileStepData;
  userType: 'volunteer' | 'organization';
  onDataUpdate: (updates: Partial<ProfileStepData>) => void;
  onNext: () => void;
  onBack: () => void;
  validationErrors: Record<string, string>;
}
```

**Validation Schema (Zod):**
```typescript
const profileValidationSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email"),
  location: z.string().min(2, "Please enter your location"),
  bio: z.string().min(10, "Please tell us a bit more about yourself"),
  organizationName: z.string().optional(),
  organizationType: z.enum([
    'nonprofit', 'ngo', 'charity', 'government', 
    'social-enterprise', 'community-group', 'other'
  ]).optional(),
  organizationSize: z.enum([
    '1-10', '11-50', '51-200', '201-1000', '1000+'
  ]).optional(),
});
```

### **Step 4: Preferences Step**
```typescript
interface PreferencesStepData {
  // Skills and Interests
  skills: string[];
  interests: string[];
  causes: string[];
  
  // Availability (for volunteers)
  availabilityType?: 'full-time' | 'part-time' | 'weekends' | 'flexible';
  timeCommitmentHours?: number; // hours per week
  preferredSchedule?: string[];
  
  // Organization preferences
  volunteerTypes?: string[]; // Types of volunteers needed
  projectTypes?: string[]; // Types of projects
  
  // Communication preferences
  notificationPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
    frequency: 'immediate' | 'daily' | 'weekly';
  };
}
```

**Predefined Options (Configurable):**
```typescript
const preferencesData = {
  skills: [
    // Technical Skills
    'Web Development', 'Graphic Design', 'Video Editing', 'Photography',
    'Social Media Management', 'Data Analysis', 'Writing & Content',
    
    // Interpersonal Skills  
    'Teaching', 'Mentoring', 'Public Speaking', 'Event Planning',
    'Project Management', 'Customer Service', 'Translation',
    
    // Specialized Skills
    'Healthcare', 'Legal Advice', 'Accounting', 'Marketing',
    'Fundraising', 'Grant Writing', 'Research'
  ],
  
  causes: [
    'Education', 'Health & Wellness', 'Environment & Sustainability',
    'Poverty & Homelessness', 'Human Rights', 'Refugees & Immigration',
    'Women Empowerment', 'Youth Development', 'Elderly Care',
    'Disability Support', 'Mental Health', 'Community Development',
    'Food Security', 'Water & Sanitation', 'Technology for Good',
    'Arts & Culture', 'Sports & Recreation', 'Animal Welfare'
  ],
  
  interests: [
    'Direct Service', 'Advocacy & Awareness', 'Research & Analysis',
    'Capacity Building', 'Emergency Response', 'Policy Work',
    'Creative Projects', 'Technology Solutions', 'Community Outreach',
    'Training & Workshops', 'Event Organization', 'Administrative Support'
  ]
};
```

### **Step 5: Completion Step**
```typescript
interface CompletionStepProps {
  userData: OnboardingStepData;
  userType: 'volunteer' | 'organization';
  onComplete: () => void;
  onEditProfile: () => void;
}

// Required Features:
// - Success animation with confetti/particle effects
// - Personalized welcome message with user's name
// - Preview of user's profile
// - Next steps recommendations
// - Direct navigation to relevant sections
// - Achievement unlocked animation (gamification)
// - Social sharing options (optional)
```

## 🔄 **EVENT SOURCING INTEGRATION**

### **Event Types to Emit**
```typescript
// Event definitions for backend integration
interface OnboardingEvents {
  UserTypeSelected: {
    userId: string;
    userType: 'volunteer' | 'organization';
    timestamp: string;
    sessionId: string;
  };
  
  ProfileInformationUpdated: {
    userId: string;
    profile: {
      fullName: string;
      location: string;
      bio: string;
      avatar?: string;
      organizationName?: string;
      organizationType?: string;
    };
    timestamp: string;
  };
  
  PreferencesSet: {
    userId: string;
    preferences: {
      skills: string[];
      interests: string[];
      causes: string[];
      availability?: {
        type: string;
        hoursPerWeek: number;
        schedule: string[];
      };
      notifications: {
        email: boolean;
        sms: boolean;
        push: boolean;
        frequency: string;
      };
    };
    timestamp: string;
  };
  
  OnboardingCompleted: {
    userId: string;
    userType: 'volunteer' | 'organization';
    completedSteps: string[];
    completionTime: number; // seconds taken
    timestamp: string;
  };
  
  OnboardingStepStarted: {
    userId: string;
    step: number;
    stepName: string;
    timestamp: string;
  };
  
  OnboardingStepCompleted: {
    userId: string;
    step: number;
    stepName: string;
    timeSpent: number;
    timestamp: string;
  };
}
```

### **BFF Integration Points**
```typescript
// Required BFF SDK methods to use/implement
interface OnboardingBFFMethods {
  // Profile management
  updateProfile(data: ProfileData): Promise<void>;
  uploadAvatar(file: File): Promise<string>; // Returns avatar URL
  
  // Preferences
  setUserPreferences(preferences: PreferencesData): Promise<void>;
  getUserPreferences(userId: string): Promise<PreferencesData>;
  
  // Location services  
  searchLocations(query: string): Promise<LocationSuggestion[]>;
  validateLocation(location: string): Promise<boolean>;
  
  // Skills and causes (dynamic data)
  getAvailableSkills(): Promise<string[]>;
  getAvailableCauses(): Promise<string[]>;
  
  // Progress tracking
  trackOnboardingProgress(step: number, data: any): Promise<void>;
  completeOnboarding(finalData: OnboardingData): Promise<void>;
}
```

## 🎨 **UI/UX SPECIFICATIONS**

### **Gaming Visual Design**
```css
/* Gaming-themed animations */
@keyframes hero-entrance {
  0% {
    opacity: 0;
    transform: translateY(50px) scale(0.9);
    filter: blur(10px);
  }
  50% {
    opacity: 0.8;
    transform: translateY(-10px) scale(1.05);
    filter: blur(2px);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@keyframes step-transition {
  0% {
    transform: translateX(100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes completion-celebration {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-30px);
  }
  60% {
    transform: translateY(-15px);
  }
}
```

### **Responsive Design Specifications**
```typescript
const responsiveBreakpoints = {
  mobile: { maxWidth: '768px' },
  tablet: { minWidth: '769px', maxWidth: '1024px' },
  desktop: { minWidth: '1025px' }
};

// Layout specifications per device
const layoutSpecs = {
  mobile: {
    maxWidth: '100%',
    padding: '1rem',
    stepCards: 'single-column',
    navigation: 'bottom-fixed'
  },
  tablet: {
    maxWidth: '600px',
    padding: '2rem',
    stepCards: 'single-column-centered',
    navigation: 'inline'
  },
  desktop: {
    maxWidth: '800px',
    padding: '3rem',
    stepCards: 'multi-column-possible',
    navigation: 'inline'
  }
};
```

## 🔄 **STATE MANAGEMENT ARCHITECTURE**

### **OnboardingProvider Context**
```typescript
interface OnboardingContextType {
  // Current state
  currentStep: number;
  isTransitioning: boolean;
  userData: OnboardingStepData;
  validationErrors: Record<string, string>;
  
  // Progress tracking
  stepsCompleted: boolean[];
  startTime: Date;
  stepStartTimes: Date[];
  
  // Navigation
  goToStep: (step: number) => Promise<void>;
  goToNextStep: () => Promise<void>;
  goToPreviousStep: () => void;
  
  // Data management
  updateStepData: (step: number, data: Partial<OnboardingStepData>) => void;
  validateCurrentStep: () => Promise<boolean>;
  persistProgress: () => Promise<void>;
  
  // Completion
  completeOnboarding: () => Promise<void>;
  
  // Utility
  canProceedToNext: boolean;
  progressPercentage: number;
  timeSpentOnCurrentStep: number;
}

const OnboardingProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  // Implementation with useReducer for complex state management
  const [state, dispatch] = useReducer(onboardingReducer, initialState);
  
  // Context value with all methods and state
  const value: OnboardingContextType = {
    // ... implementation
  };
  
  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
};
```

### **Validation & Error Handling**
```typescript
interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
  warnings?: Record<string, string>;
}

class OnboardingValidator {
  validateStep(step: number, data: any): ValidationResult {
    switch (step) {
      case 1: return this.validateWelcome(data);
      case 2: return this.validateUserType(data);
      case 3: return this.validateProfile(data);
      case 4: return this.validatePreferences(data);
      case 5: return this.validateCompletion(data);
      default: return { isValid: true, errors: {} };
    }
  }
  
  private validateProfile(data: ProfileStepData): ValidationResult {
    const result = profileValidationSchema.safeParse(data);
    if (result.success) {
      return { isValid: true, errors: {} };
    }
    
    const errors: Record<string, string> = {};
    result.error.errors.forEach(error => {
      errors[error.path[0]] = error.message;
    });
    
    return { isValid: false, errors };
  }
  
  // ... other validation methods
}
```

## 🔌 **Integration Requirements**

### **Authentication Context Integration**
```typescript
// Must integrate with existing AuthContext
interface AuthContextIntegration {
  // Get current user data for pre-filling
  getCurrentUser(): User | null;
  
  // Update user profile after onboarding
  updateUserProfile(profileData: ProfileData): Promise<void>;
  
  // Mark onboarding as completed
  setOnboardingComplete(userId: string): Promise<void>;
  
  // Check if onboarding is required
  isOnboardingRequired(user: User): boolean;
}

// Usage in onboarding flow
const { user, updateUserProfile } = useAuth();

useEffect(() => {
  if (user && !user.onboardingComplete) {
    // Pre-fill form with existing user data
    updateStepData(3, {
      fullName: user.name || '',
      email: user.email || '',
    });
  }
}, [user]);
```

### **Routing Integration**
```typescript
// Update app routing to handle onboarding flow
// Location: apps/web/app/onboarding/page.tsx

'use client';

import { OnboardingFlow } from '@/components/onboarding/OnboardingFlow';
import { OnboardingProvider } from '@/components/onboarding/OnboardingProvider';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function OnboardingPage() {
  const { user, updateUserProfile } = useAuth();
  const router = useRouter();
  
  const handleOnboardingComplete = async (data: OnboardingStepData) => {
    try {
      // Update user profile with onboarding data
      await updateUserProfile({
        ...data.profile,
        preferences: data.preferences,
        onboardingComplete: true
      });
      
      // Redirect based on user type
      if (data.userType === 'volunteer') {
        router.push('/opportunities?welcome=true');
      } else {
        router.push('/organization/dashboard?welcome=true');
      }
    } catch (error) {
      console.error('Onboarding completion failed:', error);
      // Handle error appropriately
    }
  };
  
  // Redirect if onboarding already completed
  useEffect(() => {
    if (user?.onboardingComplete) {
      router.push(user.userType === 'volunteer' ? '/opportunities' : '/organization/dashboard');
    }
  }, [user, router]);
  
  return (
    <ProtectedRoute>
      <OnboardingProvider>
        <OnboardingFlow onComplete={handleOnboardingComplete} />
      </OnboardingProvider>
    </ProtectedRoute>
  );
}
```

## 🧪 **TESTING SPECIFICATIONS**

### **Unit Testing Requirements**
```typescript
// Each component must have comprehensive tests
describe('OnboardingFlow', () => {
  it('should navigate through all steps sequentially', async () => {
    render(
      <OnboardingProvider>
        <OnboardingFlow onComplete={jest.fn()} />
      </OnboardingProvider>
    );
    
    // Test step navigation
    expect(screen.getByText('Welcome to Seraaj')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Begin Your Hero\'s Journey'));
    await waitFor(() => {
      expect(screen.getByText('Choose Your Path')).toBeInTheDocument();
    });
    
    // Continue testing all steps...
  });
  
  it('should validate form data correctly', async () => {
    // Test validation for each step
  });
  
  it('should persist data between steps', () => {
    // Test data persistence
  });
  
  it('should handle errors gracefully', () => {
    // Test error scenarios
  });
});
```

### **Integration Testing**
```typescript
describe('Onboarding Integration', () => {
  it('should complete full volunteer onboarding flow', async () => {
    // Mock BFF API calls
    const mockBFF = {
      updateProfile: jest.fn().mockResolvedValue({}),
      setUserPreferences: jest.fn().mockResolvedValue({}),
      completeOnboarding: jest.fn().mockResolvedValue({})
    };
    
    // Test complete flow with real data
    const testData = {
      userType: 'volunteer',
      profile: {
        fullName: 'Test Hero',
        location: 'Amman, Jordan',
        bio: 'I want to help my community'
      },
      preferences: {
        skills: ['Teaching', 'Mentoring'],
        causes: ['Education', 'Youth Development'],
        availability: {
          type: 'part-time',
          hoursPerWeek: 4
        }
      }
    };
    
    // Simulate user completing each step
    // Verify API calls are made with correct data
    // Verify navigation occurs correctly
  });
});
```

### **Accessibility Testing**
```typescript
describe('Onboarding Accessibility', () => {
  it('should have proper heading hierarchy', () => {
    // Test h1, h2, h3 structure
  });
  
  it('should support keyboard navigation', () => {
    // Test Tab, Enter, Space key interactions
  });
  
  it('should work with screen readers', () => {
    // Test ARIA labels, announcements
  });
  
  it('should have proper color contrast', () => {
    // Test contrast ratios meet WCAG standards
  });
});
```

## 📊 **PERFORMANCE REQUIREMENTS**

### **Loading & Transition Speeds**
- **Step Transitions**: < 300ms animation duration
- **Form Validation**: < 100ms response time
- **Data Persistence**: < 1 second for each step
- **Image Upload**: Progress indicator, < 30 seconds timeout
- **Location Autocomplete**: < 500ms API response

### **Bundle Size Optimization**
- **Code Splitting**: Each step lazy-loaded
- **Image Optimization**: WebP format with fallbacks
- **Animation Performance**: CSS transforms only (GPU accelerated)

```typescript
// Lazy loading implementation
const WelcomeStep = lazy(() => import('./steps/WelcomeStep'));
const UserTypeStep = lazy(() => import('./steps/UserTypeStep'));
const ProfileStep = lazy(() => import('./steps/ProfileStep'));
const PreferencesStep = lazy(() => import('./steps/PreferencesStep'));
const CompletionStep = lazy(() => import('./steps/CompletionStep'));

const stepComponents = [
  WelcomeStep,
  UserTypeStep,
  ProfileStep,
  PreferencesStep,
  CompletionStep
];
```

## 🎯 **SUCCESS METRICS & VALIDATION**

### **Functional Requirements**
- [ ] All 5 steps implemented with gaming visual design
- [ ] Both volunteer and organization flows work correctly
- [ ] Data persists correctly through event sourcing
- [ ] Form validation prevents invalid submissions
- [ ] Responsive design works on all screen sizes
- [ ] Accessibility compliance verified with screen readers
- [ ] Integration with AuthContext and routing works
- [ ] Error handling graceful and user-friendly

### **Performance Requirements**  
- [ ] Step transitions < 300ms
- [ ] Form validation < 100ms response
- [ ] No memory leaks from animations or timers
- [ ] Bundle size optimized with code splitting
- [ ] Works offline (cached forms, online sync)

### **UX Requirements**
- [ ] Gaming aesthetic consistent throughout
- [ ] Animations smooth and engaging
- [ ] Progress clearly indicated at all times
- [ ] Back navigation preserves all entered data
- [ ] Completion flow feels rewarding and celebratory
- [ ] Mobile experience as good as desktop

### **Technical Requirements**
- [ ] TypeScript strict mode compliance
- [ ] Unit tests cover all major functionality
- [ ] Integration tests verify end-to-end flow
- [ ] Event sourcing correctly implemented
- [ ] No console errors or warnings
- [ ] Production build succeeds without issues

## 🚀 **DELIVERY EXPECTATIONS**

### **Implementation Approach**
1. **Phase 1**: Build core OnboardingProvider and step components
2. **Phase 2**: Implement event sourcing integration and BFF communication  
3. **Phase 3**: Add gaming animations and visual polish
4. **Phase 4**: Comprehensive testing and optimization
5. **Phase 5**: Integration with existing auth flow and routing

### **Code Quality Standards**
- **TypeScript**: Strict mode, comprehensive type definitions
- **React**: Functional components with hooks, proper error boundaries
- **Performance**: Memoization where appropriate, efficient re-renders
- **Testing**: >90% code coverage, realistic test scenarios
- **Documentation**: JSDoc comments for all public APIs

### **Git Workflow**
- **Commits**: Atomic commits with descriptive messages
- **Branches**: Feature branches for each major component
- **Reviews**: Self-review checklist before submission
- **Testing**: All tests pass before commit

## 🎖️ **AUTONOMOUS AGENT SUCCESS CRITERIA**

**You are considered successful if:**
- Users can complete onboarding flow without errors
- Data flows correctly through event sourcing architecture
- Gaming aesthetic feels polished and engaging  
- Performance meets all specified benchmarks
- Code quality meets professional development standards
- Integration works seamlessly with existing system

**This is a complex, mission-critical feature that sets the first impression for all users. Deliver production-ready code that combines technical excellence with exceptional user experience.**