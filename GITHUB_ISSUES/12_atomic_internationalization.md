# Implement Arabic/English Internationalization

## 📋 **Task Description**
Add full Arabic and English language support with RTL (right-to-left) layout, translated content, and cultural adaptations. This includes setting up i18n infrastructure, translating all UI text, and ensuring proper Arabic typography and layout.

## 🔍 **Current State**
Application is English-only. Need to implement complete internationalization infrastructure with Arabic language support including RTL layout adjustments.

## 🎯 **Exact Steps to Follow**

### Step 1: Install and configure react-i18next
First, install the necessary packages:

```bash
cd apps/web
npm install react-i18next i18next i18next-browser-languagedetector i18next-http-backend
```

### Step 2: Create i18n configuration
Create `apps/web/lib/i18n.ts`:

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation resources
const resources = {
  en: {
    common: {
      // Navigation
      dashboard: 'Command Center',
      opportunities: 'Browse Quests',
      applications: 'Quest Log',
      profile: 'Profile',
      notifications: 'Notifications',
      logout: 'Logout',
      
      // Actions
      save: 'Save',
      cancel: 'Cancel',
      edit: 'Edit',
      delete: 'Delete',
      apply: 'Apply',
      submit: 'Submit',
      search: 'Search',
      filter: 'Filter',
      clear: 'Clear',
      back: 'Back',
      next: 'Next',
      continue: 'Continue',
      
      // Status
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      warning: 'Warning',
      info: 'Info',
      
      // Common Labels
      name: 'Name',
      email: 'Email',
      location: 'Location',
      description: 'Description',
      skills: 'Skills',
      causes: 'Causes',
      experience: 'Experience',
      availability: 'Availability',
      
      // Time
      hours: 'hours',
      days: 'days',
      weeks: 'weeks',
      minutes: 'minutes',
      ago: 'ago',
      
      // Gaming Terms
      hero: 'Hero',
      quest: 'Quest',
      questGiver: 'Quest Giver',
      epic: 'Epic',
      legendary: 'Legendary',
      mission: 'Mission',
      adventure: 'Adventure',
      
      // Validation
      required: 'This field is required',
      invalidEmail: 'Please enter a valid email',
      passwordTooShort: 'Password must be at least 6 characters',
      confirmPassword: 'Passwords must match'
    },
    
    dashboard: {
      title: 'Hero Command Center',
      subtitle: 'Welcome back, brave hero! Your next epic quest awaits...',
      stats: {
        totalApplications: 'Total Quests',
        activeApplications: 'Active Quests',
        completedQuests: 'Completed',
        impactHours: 'Impact Hours'
      },
      quickActions: {
        browseQuests: 'Browse All Quests',
        upgradeSkills: 'Upgrade Skills',
        questLog: 'Quest Log'
      },
      perfectMatches: 'Perfect Matches For You',
      recentActivity: 'Recent Quest Activity',
      noQuests: 'No Quests Found',
      completeProfile: 'Complete your profile to get personalized quest recommendations!'
    },
    
    opportunities: {
      title: 'Quest Browser',
      subtitle: 'Discover opportunities perfectly matched to your heroic abilities!',
      advancedSearch: 'Advanced Quest Search',
      searchPlaceholder: 'Search skills, locations, causes, or organizations...',
      filters: 'Filters',
      results: 'quests found',
      noResults: 'No Quests Match Your Search',
      adjustFilters: 'Try adjusting your search criteria or clearing filters to see more opportunities.',
      
      card: {
        viewQuest: 'View Quest',
        acceptQuest: 'Accept Quest',
        skillsNeeded: 'Skills Needed',
        causes: 'Causes',
        remote: 'Remote OK',
        perfectMatch: 'Perfect Match!',
        goodMatch: 'Good Match',
        fairMatch: 'Fair Match',
        lowMatch: 'Low Match'
      }
    },
    
    applications: {
      title: 'Quest Log',
      subtitle: 'Track all your heroic adventures and application status',
      tabs: {
        all: 'All Quests',
        pending: 'Pending',
        accepted: 'Accepted',
        completed: 'Completed'
      },
      status: {
        pending: 'Pending Review',
        reviewing: 'Under Review',
        accepted: 'Quest Accepted',
        rejected: 'Quest Declined',
        completed: 'Quest Completed'
      },
      statusDescription: {
        pending: 'Quest giver is reviewing your application',
        reviewing: 'Your heroic credentials are being evaluated',
        accepted: 'Congratulations! Your quest begins soon',
        rejected: 'This quest was not a match, but keep exploring',
        completed: 'Well done, hero! Quest successfully completed'
      },
      actions: {
        viewDetails: 'View Details',
        withdraw: 'Withdraw',
        startQuest: 'Start Quest'
      },
      empty: {
        noQuests: 'No Quests in Your Log',
        startJourney: 'Start your heroic journey by applying to opportunities!',
        findQuests: 'Find Quests'
      }
    },
    
    profile: {
      title: 'Hero Profile',
      editProfile: 'Edit Profile',
      backToCommand: 'Back to Command Center',
      profileDetails: 'Profile Details',
      abilitiesAndCauses: 'Abilities & Causes',
      personalInfo: 'Personal Info',
      
      completion: {
        title: 'Level Up Your Profile!',
        subtitle: 'Complete your profile to get better quest matches and stand out to organizations.',
        completeProfile: 'Complete Profile'
      },
      
      heroTitles: {
        legendary: 'Legendary Hero',
        veteran: 'Veteran Hero',
        rising: 'Rising Hero',
        aspiring: 'Aspiring Hero'
      },
      
      form: {
        fullName: 'Full Name',
        bio: 'Bio',
        bioPlaceholder: 'Tell other heroes about yourself...',
        experienceLevel: 'Experience Level',
        experienceLevels: {
          beginner: 'Beginner Hero',
          intermediate: 'Experienced Hero',
          advanced: 'Expert Hero',
          expert: 'Master Hero'
        },
        skillsTitle: 'Skills ({{count}} selected)',
        causesTitle: 'Causes ({{count}} selected)',
        addCustomSkill: 'Add custom skill...',
        addCustomCause: 'Add custom cause...',
        saveProfile: 'Save Profile'
      }
    },
    
    onboarding: {
      welcome: {
        title: 'Welcome to Seraaj',
        subtitle: 'Your epic volunteering adventure begins here!',
        getStarted: 'Begin Your Journey'
      },
      
      userType: {
        title: 'Choose Your Path',
        subtitle: 'Are you here to volunteer or do you represent an organization?',
        volunteer: {
          title: 'I\'m a Hero',
          description: 'I want to volunteer and help causes I care about',
          features: [
            'Find perfect volunteer matches',
            'Track your impact and hours',
            'Connect with organizations',
            'Build your heroic reputation'
          ]
        },
        organization: {
          title: 'I\'m a Quest Giver',
          description: 'I represent an organization seeking volunteers',
          features: [
            'Post volunteer opportunities',
            'Find qualified heroes',
            'Manage applications',
            'Track organizational impact'
          ]
        },
        continue: 'Continue Your Journey'
      },
      
      skillsCauses: {
        title: 'Your Heroic Abilities',
        subtitle: 'Select your skills and causes you care about (minimum 1 each)',
        skillsTitle: 'Skills ({{count}} selected)',
        causesTitle: 'Causes You Care About ({{count}} selected)',
        requirement: 'Please select at least 1 skill and 1 cause to continue',
        addSkill: 'Add custom skill...',
        addCause: 'Add custom cause...'
      },
      
      completion: {
        title: 'Welcome to the Quest, {{name}}!',
        subtitle: 'Your {{userType}} profile is ready. Time to {{action}}!',
        volunteerAction: 'find amazing quests',
        organizationAction: 'create opportunities',
        profileSummary: 'Profile Summary:',
        startJourney: 'Start My Journey!'
      }
    },
    
    auth: {
      login: {
        title: 'Hero Login',
        subtitle: 'Welcome back, brave adventurer!',
        email: 'Email',
        password: 'Password',
        loginButton: 'Enter the Realm',
        forgotPassword: 'Forgot your password?',
        noAccount: 'No account yet?',
        register: 'Create Hero Account'
      },
      
      register: {
        title: 'Create Hero Account',
        subtitle: 'Begin your legendary volunteering journey!',
        name: 'Full Name',
        email: 'Email',
        password: 'Password',
        confirmPassword: 'Confirm Password',
        registerButton: 'Join the Quest',
        hasAccount: 'Already have an account?',
        login: 'Login Here'
      }
    },
    
    notifications: {
      title: 'Quest Updates',
      markAllRead: 'Mark All Read',
      clearAll: 'Clear All',
      tabs: {
        all: 'All',
        unread: 'Unread'
      },
      empty: {
        noNotifications: 'No notifications yet',
        noUnread: 'No new notifications'
      },
      
      types: {
        questAccepted: 'Quest Accepted!',
        questCompleted: 'Quest Completed!',
        newMatch: 'Perfect Match Found!',
        applicationSubmitted: 'Application Sent!',
        message: 'Message from Quest Giver:'
      },
      
      toasts: {
        questAccepted: 'Your heroic application for "{{questTitle}}" at {{organization}} has been accepted!',
        questCompleted: 'Congratulations, hero! You completed "{{questTitle}}" and earned {{impactHours}} impact hours.',
        newMatch: 'We found a {{matchScore}}% match: "{{questTitle}}"',
        applicationSubmitted: 'Your application for "{{questTitle}}" has been submitted successfully.'
      }
    }
  },
  
  ar: {
    common: {
      // Navigation
      dashboard: 'مركز القيادة',
      opportunities: 'تصفح المهام',
      applications: 'سجل المهام',
      profile: 'الملف الشخصي',
      notifications: 'الإشعارات',
      logout: 'تسجيل الخروج',
      
      // Actions
      save: 'حفظ',
      cancel: 'إلغاء',
      edit: 'تعديل',
      delete: 'حذف',
      apply: 'تطبيق',
      submit: 'إرسال',
      search: 'بحث',
      filter: 'تصفية',
      clear: 'مسح',
      back: 'رجوع',
      next: 'التالي',
      continue: 'متابعة',
      
      // Status
      loading: 'جاري التحميل...',
      error: 'خطأ',
      success: 'نجح',
      warning: 'تحذير',
      info: 'معلومات',
      
      // Common Labels
      name: 'الاسم',
      email: 'البريد الإلكتروني',
      location: 'الموقع',
      description: 'الوصف',
      skills: 'المهارات',
      causes: 'القضايا',
      experience: 'الخبرة',
      availability: 'التوفر',
      
      // Time
      hours: 'ساعات',
      days: 'أيام',
      weeks: 'أسابيع',
      minutes: 'دقائق',
      ago: 'مضى',
      
      // Gaming Terms
      hero: 'البطل',
      quest: 'المهمة',
      questGiver: 'معطي المهام',
      epic: 'ملحمي',
      legendary: 'أسطوري',
      mission: 'مهمة',
      adventure: 'مغامرة',
      
      // Validation
      required: 'هذا الحقل مطلوب',
      invalidEmail: 'يرجى إدخال بريد إلكتروني صحيح',
      passwordTooShort: 'كلمة المرور يجب أن تكون 6 أحرف على الأقل',
      confirmPassword: 'كلمات المرور يجب أن تتطابق'
    },
    
    dashboard: {
      title: 'مركز قيادة الأبطال',
      subtitle: 'أهلاً بعودتك أيها البطل الشجاع! مهمتك الملحمية التالية في انتظارك...',
      stats: {
        totalApplications: 'إجمالي المهام',
        activeApplications: 'المهام النشطة',
        completedQuests: 'المكتملة',
        impactHours: 'ساعات التأثير'
      },
      quickActions: {
        browseQuests: 'تصفح جميع المهام',
        upgradeSkills: 'ترقية المهارات',
        questLog: 'سجل المهام'
      },
      perfectMatches: 'التطابقات المثالية لك',
      recentActivity: 'النشاط الأخير للمهام',
      noQuests: 'لم يتم العثور على مهام',
      completeProfile: 'أكمل ملفك الشخصي للحصول على توصيات مهام شخصية!'
    },
    
    opportunities: {
      title: 'متصفح المهام',
      subtitle: 'اكتشف الفرص المطابقة تماماً لقدراتك البطولية!',
      advancedSearch: 'البحث المتقدم عن المهام',
      searchPlaceholder: 'ابحث عن المهارات والمواقع والقضايا والمنظمات...',
      filters: 'المرشحات',
      results: 'مهمة موجودة',
      noResults: 'لا توجد مهام تطابق بحثك',
      adjustFilters: 'حاول تعديل معايير البحث أو مسح المرشحات لرؤية المزيد من الفرص.',
      
      card: {
        viewQuest: 'عرض المهمة',
        acceptQuest: 'قبول المهمة',
        skillsNeeded: 'المهارات المطلوبة',
        causes: 'القضايا',
        remote: 'عمل عن بعد',
        perfectMatch: 'تطابق مثالي!',
        goodMatch: 'تطابق جيد',
        fairMatch: 'تطابق عادل',
        lowMatch: 'تطابق منخفض'
      }
    },
    
    applications: {
      title: 'سجل المهام',
      subtitle: 'تتبع جميع مغامراتك البطولية وحالة الطلبات',
      tabs: {
        all: 'جميع المهام',
        pending: 'قيد الانتظار',
        accepted: 'مقبولة',
        completed: 'مكتملة'
      },
      status: {
        pending: 'قيد المراجعة',
        reviewing: 'تحت المراجعة',
        accepted: 'تم قبول المهمة',
        rejected: 'تم رفض المهمة',
        completed: 'تم إكمال المهمة'
      },
      statusDescription: {
        pending: 'معطي المهام يراجع طلبك',
        reviewing: 'يتم تقييم أوراق اعتمادك البطولية',
        accepted: 'تهانينا! مهمتك تبدأ قريباً',
        rejected: 'هذه المهمة لم تكن مطابقة، لكن استمر في الاستكشاف',
        completed: 'أحسنت أيها البطل! تم إكمال المهمة بنجاح'
      },
      actions: {
        viewDetails: 'عرض التفاصيل',
        withdraw: 'سحب',
        startQuest: 'بدء المهمة'
      },
      empty: {
        noQuests: 'لا توجد مهام في سجلك',
        startJourney: 'ابدأ رحلتك البطولية بالتقدم للفرص!',
        findQuests: 'العثور على مهام'
      }
    },
    
    profile: {
      title: 'ملف البطل الشخصي',
      editProfile: 'تعديل الملف الشخصي',
      backToCommand: 'العودة إلى مركز القيادة',
      profileDetails: 'تفاصيل الملف الشخصي',
      abilitiesAndCauses: 'القدرات والقضايا',
      personalInfo: 'المعلومات الشخصية',
      
      completion: {
        title: 'ارتقِ بملفك الشخصي!',
        subtitle: 'أكمل ملفك الشخصي للحصول على تطابقات أفضل للمهام وللبروز أمام المنظمات.',
        completeProfile: 'إكمال الملف الشخصي'
      },
      
      heroTitles: {
        legendary: 'بطل أسطوري',
        veteran: 'بطل محنك',
        rising: 'بطل صاعد',
        aspiring: 'بطل طموح'
      },
      
      form: {
        fullName: 'الاسم الكامل',
        bio: 'السيرة الذاتية',
        bioPlaceholder: 'أخبر الأبطال الآخرين عن نفسك...',
        experienceLevel: 'مستوى الخبرة',
        experienceLevels: {
          beginner: 'بطل مبتدئ',
          intermediate: 'بطل متمرس',
          advanced: 'بطل خبير',
          expert: 'بطل استاذ'
        },
        skillsTitle: 'المهارات ({{count}} محددة)',
        causesTitle: 'القضايا ({{count}} محددة)',
        addCustomSkill: 'إضافة مهارة مخصصة...',
        addCustomCause: 'إضافة قضية مخصصة...',
        saveProfile: 'حفظ الملف الشخصي'
      }
    },
    
    onboarding: {
      welcome: {
        title: 'أهلاً بك في سراج',
        subtitle: 'مغامرتك التطوعية الملحمية تبدأ هنا!',
        getStarted: 'ابدأ رحلتك'
      },
      
      userType: {
        title: 'اختر مسارك',
        subtitle: 'هل أنت هنا للتطوع أم تمثل منظمة؟',
        volunteer: {
          title: 'أنا بطل',
          description: 'أريد التطوع ومساعدة القضايا التي أهتم بها',
          features: [
            'العثور على تطابقات تطوعية مثالية',
            'تتبع تأثيرك وساعاتك',
            'التواصل مع المنظمات',
            'بناء سمعتك البطولية'
          ]
        },
        organization: {
          title: 'أنا معطي مهام',
          description: 'أمثل منظمة تبحث عن متطوعين',
          features: [
            'نشر فرص التطوع',
            'العثور على أبطال مؤهلين',
            'إدارة الطلبات',
            'تتبع التأثير التنظيمي'
          ]
        },
        continue: 'متابعة رحلتك'
      },
      
      skillsCauses: {
        title: 'قدراتك البطولية',
        subtitle: 'اختر مهاراتك والقضايا التي تهتم بها (الحد الأدنى 1 لكل منها)',
        skillsTitle: 'المهارات ({{count}} محددة)',
        causesTitle: 'القضايا التي تهتم بها ({{count}} محددة)',
        requirement: 'يرجى اختيار مهارة واحدة على الأقل وقضية واحدة للمتابعة',
        addSkill: 'إضافة مهارة مخصصة...',
        addCause: 'إضافة قضية مخصصة...'
      },
      
      completion: {
        title: 'أهلاً بك في المهمة، {{name}}!',
        subtitle: 'ملفك الشخصي {{userType}} جاهز. حان الوقت {{action}}!',
        volunteerAction: 'للعثور على مهام رائعة',
        organizationAction: 'لإنشاء فرص',
        profileSummary: 'ملخص الملف الشخصي:',
        startJourney: 'ابدأ رحلتي!'
      }
    },
    
    auth: {
      login: {
        title: 'دخول البطل',
        subtitle: 'أهلاً بعودتك أيها المغامر الشجاع!',
        email: 'البريد الإلكتروني',
        password: 'كلمة المرور',
        loginButton: 'دخول المملكة',
        forgotPassword: 'نسيت كلمة المرور؟',
        noAccount: 'لا يوجد لديك حساب بعد؟',
        register: 'إنشاء حساب بطل'
      },
      
      register: {
        title: 'إنشاء حساب بطل',
        subtitle: 'ابدأ رحلتك التطوعية الأسطورية!',
        name: 'الاسم الكامل',
        email: 'البريد الإلكتروني',
        password: 'كلمة المرور',
        confirmPassword: 'تأكيد كلمة المرور',
        registerButton: 'انضم إلى المهمة',
        hasAccount: 'لديك حساب بالفعل؟',
        login: 'تسجيل الدخول هنا'
      }
    },
    
    notifications: {
      title: 'تحديثات المهام',
      markAllRead: 'تعيين الكل كمقروء',
      clearAll: 'مسح الكل',
      tabs: {
        all: 'الكل',
        unread: 'غير مقروء'
      },
      empty: {
        noNotifications: 'لا توجد إشعارات بعد',
        noUnread: 'لا توجد إشعارات جديدة'
      },
      
      types: {
        questAccepted: 'تم قبول المهمة!',
        questCompleted: 'تم إكمال المهمة!',
        newMatch: 'تم العثور على تطابق مثالي!',
        applicationSubmitted: 'تم إرسال الطلب!',
        message: 'رسالة من معطي المهام:'
      },
      
      toasts: {
        questAccepted: 'تم قبول طلبك البطولي لـ "{{questTitle}}" في {{organization}}!',
        questCompleted: 'تهانينا أيها البطل! لقد أكملت "{{questTitle}}" وحصلت على {{impactHours}} ساعة تأثير.',
        newMatch: 'وجدنا تطابقاً بنسبة {{matchScore}}%: "{{questTitle}}"',
        applicationSubmitted: 'تم إرسال طلبك لـ "{{questTitle}}" بنجاح.'
      }
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false // React already escapes values
    },
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage']
    }
  });

export default i18n;
```

### Step 3: Create LanguageProvider context
Create `apps/web/contexts/LanguageContext.tsx`:

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface LanguageContextType {
  currentLanguage: 'en' | 'ar';
  isRTL: boolean;
  changeLanguage: (lang: 'en' | 'ar') => void;
  t: (key: string, options?: any) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const [currentLanguage, setCurrentLanguage] = useState<'en' | 'ar'>(
    (i18n.language as 'en' | 'ar') || 'en'
  );
  
  const isRTL = currentLanguage === 'ar';

  const changeLanguage = (lang: 'en' | 'ar') => {
    i18n.changeLanguage(lang);
    setCurrentLanguage(lang);
    
    // Update document direction and lang attribute
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
    
    // Update CSS custom properties for RTL
    document.documentElement.style.setProperty('--text-align', lang === 'ar' ? 'right' : 'left');
    document.documentElement.style.setProperty('--text-align-opposite', lang === 'ar' ? 'left' : 'right');
  };

  useEffect(() => {
    // Set initial direction
    changeLanguage(currentLanguage);
  }, []);

  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      setCurrentLanguage(lng as 'en' | 'ar');
      document.documentElement.dir = lng === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.lang = lng;
    };

    i18n.on('languageChanged', handleLanguageChange);
    return () => i18n.off('languageChanged', handleLanguageChange);
  }, [i18n]);

  return (
    <LanguageContext.Provider value={{
      currentLanguage,
      isRTL,
      changeLanguage,
      t
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
```

### Step 4: Create LanguageToggle component
Create `apps/web/components/i18n/LanguageToggle.tsx`:

```typescript
import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { PxButton } from '@seraaj/ui';

interface LanguageToggleProps {
  variant?: 'header' | 'mobile' | 'footer';
  size?: 'sm' | 'md' | 'lg';
}

export const LanguageToggle: React.FC<LanguageToggleProps> = ({ 
  variant = 'header',
  size = 'sm'
}) => {
  const { currentLanguage, changeLanguage } = useLanguage();

  const toggleLanguage = () => {
    changeLanguage(currentLanguage === 'en' ? 'ar' : 'en');
  };

  if (variant === 'mobile') {
    return (
      <button
        onClick={toggleLanguage}
        className="w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-colors hover:bg-primary/20 text-white"
      >
        <span className="text-lg">{currentLanguage === 'en' ? '🌐' : '🇦🇪'}</span>
        <span className="font-pixel text-sm flex-1 text-left">
          {currentLanguage === 'en' ? 'العربية' : 'English'}
        </span>
      </button>
    );
  }

  if (variant === 'footer') {
    return (
      <button
        onClick={toggleLanguage}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <span>{currentLanguage === 'en' ? '🌐' : '🇦🇪'}</span>
        <span className="font-pixel">
          {currentLanguage === 'en' ? 'العربية' : 'English'}
        </span>
      </button>
    );
  }

  // Header variant (default)
  return (
    <PxButton
      variant="secondary"
      size={size}
      onClick={toggleLanguage}
      className="flex items-center gap-2"
    >
      <span>{currentLanguage === 'en' ? '🌐' : '🇦🇪'}</span>
      <span className="font-pixel">
        {currentLanguage === 'en' ? 'ع' : 'EN'}
      </span>
    </PxButton>
  );
};
```

### Step 5: Create RTL-aware layout components
Create `apps/web/components/layout/RTLLayout.tsx`:

```typescript
import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

interface RTLLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const RTLLayout: React.FC<RTLLayoutProps> = ({ children, className = '' }) => {
  const { isRTL } = useLanguage();

  return (
    <div 
      className={`${className} ${isRTL ? 'rtl-layout' : 'ltr-layout'}`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {children}
    </div>
  );
};

// RTL-aware flex component
export const RTLFlex: React.FC<{
  children: React.ReactNode;
  className?: string;
  reverse?: boolean;
}> = ({ children, className = '', reverse = false }) => {
  const { isRTL } = useLanguage();
  
  const shouldReverse = isRTL ? !reverse : reverse;
  
  return (
    <div className={`flex ${shouldReverse ? 'flex-row-reverse' : 'flex-row'} ${className}`}>
      {children}
    </div>
  );
};

// RTL-aware text alignment
export const RTLText: React.FC<{
  children: React.ReactNode;
  className?: string;
  align?: 'start' | 'end' | 'center';
}> = ({ children, className = '', align = 'start' }) => {
  const { isRTL } = useLanguage();
  
  const getTextAlign = () => {
    if (align === 'center') return 'text-center';
    if (align === 'start') return isRTL ? 'text-right' : 'text-left';
    if (align === 'end') return isRTL ? 'text-left' : 'text-right';
    return '';
  };
  
  return (
    <div className={`${getTextAlign()} ${className}`}>
      {children}
    </div>
  );
};
```

### Step 6: Add RTL styles
Create `apps/web/styles/rtl.css`:

```css
/* RTL-specific styles */
[dir="rtl"] {
  --text-align: right;
  --text-align-opposite: left;
}

[dir="ltr"] {
  --text-align: left;
  --text-align-opposite: right;
}

/* RTL Layout Adjustments */
[dir="rtl"] .rtl-layout {
  direction: rtl;
}

[dir="rtl"] .rtl-reverse {
  flex-direction: row-reverse;
}

/* Arabic Font Optimization */
[dir="rtl"] body,
[dir="rtl"] .font-pixel {
  font-family: 'Cairo', 'Amiri', 'Noto Sans Arabic', sans-serif;
  font-weight: 400;
}

[dir="rtl"] .font-pixel {
  font-weight: 500;
  letter-spacing: 0;
}

[dir="rtl"] h1, [dir="rtl"] h2, [dir="rtl"] h3, [dir="rtl"] h4, [dir="rtl"] h5, [dir="rtl"] h6 {
  font-family: 'Cairo', 'Amiri', sans-serif;
  font-weight: 600;
}

/* RTL Form Elements */
[dir="rtl"] input,
[dir="rtl"] textarea,
[dir="rtl"] select {
  text-align: right;
  padding-left: 16px;
  padding-right: 12px;
}

[dir="rtl"] input::placeholder,
[dir="rtl"] textarea::placeholder {
  text-align: right;
}

/* RTL Navigation */
[dir="rtl"] .nav-item {
  margin-left: 0;
  margin-right: 16px;
}

[dir="rtl"] .breadcrumb::after {
  content: '\\';
  margin: 0 8px;
}

/* RTL Cards and Components */
[dir="rtl"] .card-content {
  text-align: right;
}

[dir="rtl"] .flex-row {
  flex-direction: row-reverse;
}

[dir="rtl"] .justify-start {
  justify-content: flex-end;
}

[dir="rtl"] .justify-end {
  justify-content: flex-start;
}

/* RTL Icons and Badges */
[dir="rtl"] .icon-start {
  margin-left: 8px;
  margin-right: 0;
}

[dir="rtl"] .icon-end {
  margin-right: 8px;
  margin-left: 0;
}

[dir="rtl"] .badge {
  left: -8px;
  right: auto;
}

/* RTL Tooltips and Dropdowns */
[dir="rtl"] .tooltip {
  text-align: right;
}

[dir="rtl"] .dropdown-menu {
  left: auto;
  right: 0;
}

/* RTL Animations - Reverse slide directions */
[dir="rtl"] .slide-in-left {
  animation: slideInRight 0.3s ease-out;
}

[dir="rtl"] .slide-in-right {
  animation: slideInLeft 0.3s ease-out;
}

@keyframes slideInRight {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

/* RTL Mobile Drawer */
[dir="rtl"] .mobile-drawer {
  left: 0;
  right: auto;
  border-left: none;
  border-right: 2px solid var(--electric-teal);
}

[dir="rtl"] .mobile-drawer .slide-in {
  animation: slideInLeft 0.3s ease-out;
}

/* RTL Gaming Elements */
[dir="rtl"] .quest-card {
  text-align: right;
}

[dir="rtl"] .quest-card .title {
  text-align: right;
}

[dir="rtl"] .hero-stats {
  text-align: center; /* Keep stats centered */
}

/* RTL Notification Position */
[dir="rtl"] .notification-toast {
  left: 16px;
  right: auto;
}

[dir="rtl"] .notification-center {
  left: 0;
  right: auto;
}

/* RTL Loading and Empty States */
[dir="rtl"] .empty-state {
  text-align: center;
}

[dir="rtl"] .loading-text {
  text-align: center;
}

/* RTL Button Groups */
[dir="rtl"] .button-group {
  flex-direction: row-reverse;
}

[dir="rtl"] .button-group button:first-child {
  margin-right: 0;
  margin-left: 8px;
}

[dir="rtl"] .button-group button:last-child {
  margin-left: 0;
  margin-right: 8px;
}

/* RTL Progress Bars */
[dir="rtl"] .progress-bar {
  transform: scaleX(-1);
}

[dir="rtl"] .progress-bar .progress-fill {
  transform: scaleX(-1);
}

/* Arabic Number Formatting */
[dir="rtl"] .number-format {
  font-family: 'Courier New', monospace; /* Use monospace for numbers in Arabic */
  direction: ltr;
  display: inline-block;
}

/* RTL Search and Filters */
[dir="rtl"] .search-input {
  text-align: right;
  padding-right: 40px;
  padding-left: 16px;
}

[dir="rtl"] .search-icon {
  left: 16px;
  right: auto;
}

[dir="rtl"] .filter-chip {
  margin-left: 8px;
  margin-right: 0;
}

/* RTL Tables */
[dir="rtl"] table {
  text-align: right;
}

[dir="rtl"] th:first-child {
  text-align: right;
}

[dir="rtl"] td:first-child {
  text-align: right;
}

/* Custom Scrollbar for RTL */
[dir="rtl"] ::-webkit-scrollbar {
  width: 8px;
}

[dir="rtl"] ::-webkit-scrollbar-track {
  background: var(--dark-surface);
}

[dir="rtl"] ::-webkit-scrollbar-thumb {
  background: var(--electric-teal);
  border-radius: 4px;
}

/* RTL Gaming Specific */
[dir="rtl"] .gaming-border {
  /* Keep gaming clip-paths the same for aesthetic consistency */
  clip-path: polygon(
    0 0, calc(100% - 8px) 0, 100% 8px,
    100% 100%, 8px 100%, 0 calc(100% - 8px)
  );
}

[dir="rtl"] .hero-title {
  text-align: center; /* Keep hero titles centered for impact */
}

[dir="rtl"] .quest-emoji {
  /* Keep emojis in correct orientation */
  display: inline-block;
  transform: none;
}
```

### Step 7: Update components to use translations
Update a key component as an example - `apps/web/app/dashboard/page.tsx`:

```typescript
'use client';

import React, { useEffect, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { RTLLayout, RTLText } from '@/components/layout/RTLLayout';
// ... other imports

const DashboardContent = () => {
  const { t, isRTL } = useLanguage();
  // ... existing code

  return (
    <RTLLayout className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-7xl mx-auto p-6">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary mb-4">
            🏰 {t('dashboard.title')} 🏰
          </h1>
          <RTLText className="text-white text-lg mb-6">
            {t('dashboard.subtitle')}
          </RTLText>
        </div>

        {/* Stats Dashboard */}
        <DashboardStats stats={stats} />

        {/* Quick Actions */}
        <div className={`flex gap-4 mb-8 justify-center ${isRTL ? 'flex-row-reverse' : ''}`}>
          <PxButton 
            variant="primary"
            onClick={() => router.push('/opportunities')}
            className="flex items-center gap-2"
          >
            🎯 {t('dashboard.quickActions.browseQuests')}
          </PxButton>
          <PxButton 
            variant="secondary"
            onClick={() => router.push('/profile')}
            className="flex items-center gap-2"
          >
            ⚙️ {t('dashboard.quickActions.upgradeSkills')}
          </PxButton>
          <PxButton 
            variant="secondary"
            onClick={() => router.push('/applications')}
            className="flex items-center gap-2"
          >
            📋 {t('dashboard.quickActions.questLog')}
          </PxButton>
        </div>

        {/* Personalized Matches Section */}
        <div className="mb-8">
          <div className={`flex items-center gap-4 mb-6 ${isRTL ? 'flex-row-reverse' : ''}`}>
            <RTLText className="text-2xl font-pixel text-electric-teal">
              ⚡ {t('dashboard.perfectMatches')} ⚡
            </RTLText>
            <div className="flex-1 border-b border-electric-teal/30"></div>
            <PxButton 
              variant="secondary" 
              size="sm"
              onClick={() => router.push('/opportunities')}
            >
              {t('common.next')} →
            </PxButton>
          </div>

          {/* Rest of component with translations... */}
        </div>
      </main>
    </RTLLayout>
  );
};
```

### Step 8: Update app layout for i18n
Update `apps/web/app/layout.tsx`:

```typescript
import { LanguageProvider } from '@/contexts/LanguageContext';
import '@/lib/i18n'; // Initialize i18n
import '@/styles/rtl.css'; // Import RTL styles

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <head>
        {/* Add Arabic font preloads */}
        <link 
          rel="preload" 
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap" 
          as="style" 
        />
        <link 
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap"
          as="style"
        />
        <link 
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" 
          rel="stylesheet"
        />
      </head>
      <body>
        <LanguageProvider>
          <AuthProvider>
            <NotificationProvider>
              <OpportunitiesProvider>
                {children}
              </OpportunitiesProvider>
            </NotificationProvider>
          </AuthProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
```

### Step 9: Add language toggle to navigation
Update `apps/web/components/navigation/Header.tsx`:

```typescript
import { LanguageToggle } from '@/components/i18n/LanguageToggle';
import { useLanguage } from '@/contexts/LanguageContext';

// In the Header component JSX, add language toggle:
<div className="flex items-center gap-4">
  {/* Existing navigation items */}
  <LanguageToggle variant="header" size="sm" />
  
  {/* Existing notification bell and user menu */}
</div>
```

Update mobile navigation in `apps/web/components/navigation/MobileHeader.tsx`:

```typescript
// In the mobile menu items, add:
<LanguageToggle variant="mobile" />
```

### Step 10: Add cultural adaptations
Create `apps/web/utils/culturalAdaptations.ts`:

```typescript
import { useLanguage } from '@/contexts/LanguageContext';

export const useCulturalAdaptations = () => {
  const { currentLanguage, isRTL } = useLanguage();

  const formatDate = (date: Date) => {
    if (currentLanguage === 'ar') {
      return new Intl.DateTimeFormat('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    }
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(date);
  };

  const formatNumber = (num: number) => {
    if (currentLanguage === 'ar') {
      return new Intl.NumberFormat('ar-SA').format(num);
    }
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    if (currentLanguage === 'ar') {
      // Adapt currency for Arabic regions
      const arabCurrency = currency === 'USD' ? 'SAR' : currency;
      return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: arabCurrency
      }).format(amount);
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(amount);
  };

  const getLocalizedSkills = (skills: string[]) => {
    // Map English skills to Arabic equivalents
    const skillsMap: Record<string, string> = {
      'Teaching': 'التدريس',
      'Mentoring': 'الإرشاد',
      'Programming': 'البرمجة',
      'Design': 'التصميم',
      'Marketing': 'التسويق',
      'Writing': 'الكتابة',
      'Translation': 'الترجمة'
    };

    if (currentLanguage === 'ar') {
      return skills.map(skill => skillsMap[skill] || skill);
    }
    return skills;
  };

  const getLocalizedCauses = (causes: string[]) => {
    const causesMap: Record<string, string> = {
      'Education': 'التعليم',
      'Health': 'الصحة',
      'Environment': 'البيئة',
      'Poverty': 'الفقر',
      'Human Rights': 'حقوق الإنسان',
      'Youth Development': 'تنمية الشباب'
    };

    if (currentLanguage === 'ar') {
      return causes.map(cause => causesMap[cause] || cause);
    }
    return causes;
  };

  const getGamingTerms = () => {
    if (currentLanguage === 'ar') {
      return {
        hero: 'البطل',
        quest: 'المهمة',
        mission: 'المهمة',
        adventure: 'المغامرة',
        epic: 'ملحمي',
        legendary: 'أسطوري',
        experience: 'خبرة',
        level: 'مستوى'
      };
    }
    return {
      hero: 'Hero',
      quest: 'Quest',
      mission: 'Mission',
      adventure: 'Adventure',
      epic: 'Epic',
      legendary: 'Legendary',
      experience: 'Experience',
      level: 'Level'
    };
  };

  return {
    formatDate,
    formatNumber,
    formatCurrency,
    getLocalizedSkills,
    getLocalizedCauses,
    getGamingTerms,
    isRTL
  };
};
```

### Step 11: Add translation validation script
Create `scripts/validate-translations.js`:

```javascript
const fs = require('fs');
const path = require('path');

function validateTranslations() {
  const i18nFile = path.join(__dirname, '../apps/web/lib/i18n.ts');
  const content = fs.readFileSync(i18nFile, 'utf8');
  
  // Extract English and Arabic keys
  const enMatch = content.match(/en:\s*{([\s\S]*?)ar:\s*{/);
  const arMatch = content.match(/ar:\s*{([\s\S]*?)};/);
  
  if (!enMatch || !arMatch) {
    console.error('❌ Could not parse translation files');
    process.exit(1);
  }
  
  // Simple validation - count translation keys
  const enKeys = (enMatch[1].match(/\w+:/g) || []).length;
  const arKeys = (arMatch[1].match(/\w+:/g) || []).length;
  
  console.log(`📊 Translation Statistics:`);
  console.log(`English keys: ${enKeys}`);
  console.log(`Arabic keys: ${arKeys}`);
  
  if (Math.abs(enKeys - arKeys) > 5) {
    console.warn('⚠️  Warning: Significant difference in translation key counts');
  } else {
    console.log('✅ Translation keys are balanced');
  }
  
  // Check for missing interpolation variables
  const interpolationRegex = /\{\{(\w+)\}\}/g;
  const enInterpolations = [...content.matchAll(new RegExp(interpolationRegex, 'g'))];
  console.log(`🔗 Found ${enInterpolations.length} interpolation variables`);
  
  console.log('✅ Translation validation completed');
}

validateTranslations();
```

Add to `package.json`:
```json
{
  "scripts": {
    "validate-translations": "node scripts/validate-translations.js"
  }
}
```

## ✅ **Definition of Done**
- [ ] i18next configuration with Arabic and English resources
- [ ] LanguageProvider context managing language state
- [ ] LanguageToggle component in header and mobile navigation
- [ ] RTL layout components for proper Arabic display
- [ ] RTL CSS styles for proper right-to-left rendering
- [ ] Arabic font loading (Cairo, Amiri) for proper typography
- [ ] Cultural adaptations (date, number, currency formatting)
- [ ] Gaming terms translated to Arabic with cultural context
- [ ] All major UI text translated in both languages
- [ ] RTL-aware animations and transitions
- [ ] Form inputs properly aligned for RTL
- [ ] Notification positioning adjusted for RTL
- [ ] Translation validation script
- [ ] Browser language detection working
- [ ] Local storage persistence of language preference

## 🧪 **How to Test**
1. Install Arabic fonts and verify they load correctly
2. Toggle between English and Arabic in header
3. Verify RTL layout switches properly (text alignment, navigation)
4. Test forms and inputs in both languages
5. Check gaming terminology appears correctly in Arabic
6. Verify notifications and toasts position correctly in RTL
7. Test mobile navigation with language toggle
8. Check date and number formatting in both locales
9. Verify browser language detection works
10. Test language persistence after page refresh
11. Validate all major pages have translated content
12. Test Arabic typography and readability
13. Verify RTL animations work smoothly
14. Run translation validation script
15. Test with actual Arabic speakers for cultural appropriateness

## 📝 **Translation Guidelines for Future Development**
- Always add new strings to both languages simultaneously
- Use interpolation variables ({{variable}}) for dynamic content
- Consider cultural context, not just literal translation
- Test with native Arabic speakers when possible
- Keep gaming metaphors engaging in both cultures
- Use gender-neutral language where appropriate
- Consider Arabic text expansion (typically 20-30% longer)

**This should take 6-8 hours to implement and test thoroughly across all components.**