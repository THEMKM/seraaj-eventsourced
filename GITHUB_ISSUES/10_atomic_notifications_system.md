# Build Real-Time Notifications System

## 📋 **Task Description**
Create a comprehensive notifications system with toast notifications, notification center, real-time updates, and gaming-themed messaging for application status changes and system updates.

## 🔍 **Current State**
No notifications system exists. Need to build from scratch with gaming aesthetics and real-time capabilities.

## 🎯 **Exact Steps to Follow**

### Step 1: Create NotificationToast component
Create `apps/web/components/notifications/NotificationToast.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import { PxCard } from '@seraaj/ui';

interface NotificationToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const getToastConfig = (type: string) => {
  switch (type) {
    case 'success':
      return {
        icon: '✅',
        bgColor: 'bg-green-500/20',
        borderColor: 'border-green-400',
        titleColor: 'text-green-400'
      };
    case 'error':
      return {
        icon: '❌',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-400',
        titleColor: 'text-red-400'
      };
    case 'warning':
      return {
        icon: '⚠️',
        bgColor: 'bg-yellow-500/20',
        borderColor: 'border-yellow-400',
        titleColor: 'text-yellow-400'
      };
    case 'info':
    default:
      return {
        icon: 'ℹ️',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-400',
        titleColor: 'text-blue-400'
      };
  }
};

export const NotificationToast: React.FC<NotificationToastProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onClose,
  action
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);
  const config = getToastConfig(type);

  useEffect(() => {
    if (duration > 0) {
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev - (100 / (duration / 100));
          return newProgress <= 0 ? 0 : newProgress;
        });
      }, 100);

      const timeoutId = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(id), 300); // Wait for animation
      }, duration);

      return () => {
        clearInterval(progressInterval);
        clearTimeout(timeoutId);
      };
    }
  }, [duration, id, onClose]);

  if (!isVisible) return null;

  return (
    <div
      className={`transform transition-all duration-300 ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
    >
      <PxCard
        className={`relative overflow-hidden ${config.bgColor} border-2 ${config.borderColor} p-4 min-w-80 max-w-md shadow-lg`}
      >
        {/* Progress Bar */}
        {duration > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
            <div 
              className="h-full bg-primary transition-all duration-100 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <div className="flex items-start gap-3">
          <div className="text-2xl">{config.icon}</div>
          <div className="flex-1">
            <h4 className={`font-pixel text-sm ${config.titleColor} mb-1`}>
              {title}
            </h4>
            <p className="text-white text-sm leading-relaxed">
              {message}
            </p>
            {action && (
              <button
                onClick={action.onClick}
                className="mt-2 text-primary hover:text-electric-teal text-sm font-pixel underline"
              >
                {action.label}
              </button>
            )}
          </div>
          <button
            onClick={() => onClose(id)}
            className="text-gray-400 hover:text-white transition-colors text-lg"
          >
            ×
          </button>
        </div>
      </PxCard>
    </div>
  );
};
```

### Step 2: Create NotificationCenter component
Create `apps/web/components/notifications/NotificationCenter.tsx`:

```typescript
import React, { useState } from 'react';
import { PxCard, PxButton, PxBadge } from '@seraaj/ui';

interface Notification {
  id: string;
  type: 'quest_accepted' | 'quest_completed' | 'new_match' | 'message' | 'system';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

interface NotificationCenterProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onClearAll: () => void;
  onNotificationClick: (notification: Notification) => void;
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'quest_accepted':
      return '🎉';
    case 'quest_completed':
      return '🏆';
    case 'new_match':
      return '⚡';
    case 'message':
      return '💬';
    case 'system':
    default:
      return '🔔';
  }
};

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'quest_accepted':
      return 'text-green-400';
    case 'quest_completed':
      return 'text-yellow-400';
    case 'new_match':
      return 'text-primary';
    case 'message':
      return 'text-blue-400';
    case 'system':
    default:
      return 'text-electric-teal';
  }
};

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  onMarkAsRead,
  onMarkAllAsRead,
  onClearAll,
  onNotificationClick
}) => {
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const filteredNotifications = notifications.filter(notification =>
    filter === 'all' || !notification.read
  );

  const unreadCount = notifications.filter(n => !n.read).length;

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const minutes = Math.floor(diffInHours * 60);
      return `${minutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return `${Math.floor(diffInHours / 24)}d ago`;
    }
  };

  return (
    <PxCard className="w-96 max-h-96 overflow-hidden border-2 border-electric-teal">
      {/* Header */}
      <div className="p-4 border-b border-electric-teal/30 bg-dark-surface">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-pixel text-primary">
            🔔 QUEST UPDATES
          </h3>
          {unreadCount > 0 && (
            <PxBadge variant="warning" size="sm">
              {unreadCount} new
            </PxBadge>
          )}
        </div>
        
        {/* Filter Tabs */}
        <div className="flex gap-2">
          <PxButton
            variant={filter === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All ({notifications.length})
          </PxButton>
          <PxButton
            variant={filter === 'unread' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('unread')}
          >
            Unread ({unreadCount})
          </PxButton>
        </div>

        {/* Actions */}
        {notifications.length > 0 && (
          <div className="flex gap-2 mt-3">
            <PxButton variant="secondary" size="sm" onClick={onMarkAllAsRead}>
              Mark All Read
            </PxButton>
            <PxButton variant="secondary" size="sm" onClick={onClearAll}>
              Clear All
            </PxButton>
          </div>
        )}
      </div>

      {/* Notifications List */}
      <div className="max-h-64 overflow-y-auto">
        {filteredNotifications.length === 0 ? (
          <div className="p-6 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-400 font-pixel text-sm">
              {filter === 'unread' ? 'No new notifications' : 'No notifications yet'}
            </p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-4 border-b border-gray-700 cursor-pointer transition-all hover:bg-dark-surface ${
                !notification.read ? 'bg-primary/5 border-l-4 border-l-primary' : ''
              }`}
              onClick={() => onNotificationClick(notification)}
            >
              <div className="flex items-start gap-3">
                <div className="text-xl">{getNotificationIcon(notification.type)}</div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <h4 className={`font-pixel text-sm ${getNotificationColor(notification.type)} mb-1`}>
                      {notification.title}
                    </h4>
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(notification.timestamp)}
                    </span>
                  </div>
                  <p className="text-white text-sm leading-relaxed">
                    {notification.message}
                  </p>
                  {!notification.read && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onMarkAsRead(notification.id);
                      }}
                      className="mt-2 text-primary hover:text-electric-teal text-xs font-pixel"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </PxCard>
  );
};
```

### Step 3: Create NotificationProvider context
Create `apps/web/contexts/NotificationContext.tsx`:

```typescript
import React, { createContext, useContext, useState, useCallback } from 'react';
import { NotificationToast } from '@/components/notifications/NotificationToast';

interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface Notification {
  id: string;
  type: 'quest_accepted' | 'quest_completed' | 'new_match' | 'message' | 'system';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

interface NotificationContextType {
  // Toast notifications
  showToast: (toast: Omit<ToastNotification, 'id'>) => void;
  
  // Persistent notifications
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAllNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastNotification[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([
    // Mock notifications for demo
    {
      id: '1',
      type: 'quest_accepted',
      title: 'Quest Accepted!',
      message: 'Your application for "Community Garden Mentor" has been accepted by Green Earth Initiative!',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
      read: false,
      actionUrl: '/applications'
    },
    {
      id: '2',
      type: 'new_match',
      title: 'Perfect Match Found!',
      message: 'We found a 95% match: "Youth Coding Workshop Assistant" at Tech for Tomorrow.',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
      read: false,
      actionUrl: '/opportunities/123'
    },
    {
      id: '3',
      type: 'quest_completed',
      title: 'Quest Completed!',
      message: 'Congratulations! You successfully completed "Food Bank Volunteer" quest and earned 8 impact hours.',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
      read: true
    }
  ]);

  const showToast = useCallback((toast: Omit<ToastNotification, 'id'>) => {
    const id = Date.now().toString();
    const newToast = { ...toast, id };
    setToasts(prev => [...prev, newToast]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString()
    };
    setNotifications(prev => [newNotification, ...prev]);
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <NotificationContext.Provider
      value={{
        showToast,
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        clearAllNotifications
      }}
    >
      {children}
      
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <NotificationToast
            key={toast.id}
            {...toast}
            onClose={removeToast}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

// Gaming-themed notification helpers
export const questNotifications = {
  questAccepted: (questTitle: string, organization: string) => ({
    type: 'success' as const,
    title: '🎉 QUEST ACCEPTED!',
    message: `Your heroic application for "${questTitle}" at ${organization} has been accepted!`
  }),
  
  questCompleted: (questTitle: string, impactHours: number) => ({
    type: 'success' as const,
    title: '🏆 QUEST COMPLETED!',
    message: `Congratulations, hero! You completed "${questTitle}" and earned ${impactHours} impact hours.`
  }),
  
  newMatch: (questTitle: string, matchScore: number) => ({
    type: 'info' as const,
    title: '⚡ PERFECT MATCH FOUND!',
    message: `We found a ${Math.round(matchScore * 100)}% match: "${questTitle}"`
  }),
  
  applicationSubmitted: (questTitle: string) => ({
    type: 'info' as const,
    title: '📝 APPLICATION SENT!',
    message: `Your application for "${questTitle}" has been submitted successfully.`
  })
};
```

### Step 4: Add NotificationBell to Header
Update `apps/web/components/navigation/Header.tsx` to include notification bell:

```typescript
// Add to existing Header component
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { useNotifications } from '@/contexts/NotificationContext';
import { useState, useRef, useEffect } from 'react';

// Add to Header component:
const { notifications, unreadCount, markAsRead, markAllAsRead, clearAllNotifications } = useNotifications();
const [showNotifications, setShowNotifications] = useState(false);
const notificationRef = useRef<HTMLDivElement>(null);

// Close notifications when clicking outside
useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
      setShowNotifications(false);
    }
  };

  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, []);

// Add this JSX to the header navigation:
<div className="relative" ref={notificationRef}>
  <button
    onClick={() => setShowNotifications(!showNotifications)}
    className="relative p-2 text-white hover:text-primary transition-colors"
  >
    <div className="text-2xl">🔔</div>
    {unreadCount > 0 && (
      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-pixel rounded-full w-5 h-5 flex items-center justify-center">
        {unreadCount}
      </span>
    )}
  </button>
  
  {showNotifications && (
    <div className="absolute top-full right-0 mt-2 z-50">
      <NotificationCenter
        notifications={notifications}
        onMarkAsRead={markAsRead}
        onMarkAllAsRead={markAllAsRead}
        onClearAll={clearAllNotifications}
        onNotificationClick={(notification) => {
          if (notification.actionUrl) {
            window.location.href = notification.actionUrl;
          }
          markAsRead(notification.id);
          setShowNotifications(false);
        }}
      />
    </div>
  )}
</div>
```

### Step 5: Integrate notifications with application workflow
Update application submission to show notifications:

```typescript
// In ApplicationForm component, use notifications:
import { useNotifications, questNotifications } from '@/contexts/NotificationContext';

const { showToast, addNotification } = useNotifications();

const handleSubmit = async (applicationData: any) => {
  try {
    // Submit application...
    
    // Show success toast
    showToast(questNotifications.applicationSubmitted(opportunityTitle));
    
    // Add persistent notification
    addNotification({
      type: 'message',
      title: 'Application Submitted',
      message: `Your application for "${opportunityTitle}" is under review.`,
      read: false
    });
    
  } catch (error) {
    showToast({
      type: 'error',
      title: 'Submission Failed',
      message: 'Failed to submit your application. Please try again.'
    });
  }
};
```

### Step 6: Add NotificationProvider to app root
Update `apps/web/app/layout.tsx`:

```typescript
import { NotificationProvider } from '@/contexts/NotificationContext';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <NotificationProvider>
            <OpportunitiesProvider>
              {children}
            </OpportunitiesProvider>
          </NotificationProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
```

## ✅ **Definition of Done**
- [ ] NotificationToast component shows temporary notifications with animations
- [ ] NotificationCenter shows persistent notifications with filtering
- [ ] Notification bell in header shows unread count
- [ ] Toast notifications auto-dismiss after specified duration
- [ ] Persistent notifications can be marked as read individually or all at once
- [ ] Gaming-themed notification messages and icons
- [ ] Notifications integrate with application workflow
- [ ] Click outside to close notification center
- [ ] Real-time notification updates
- [ ] Notification actions work correctly (links, mark as read)
- [ ] Responsive design works on mobile

## 🧪 **How to Test**
1. Submit an application and verify toast notification appears
2. Check notification bell shows unread count
3. Click notification bell to open notification center
4. Test filtering between "All" and "Unread" notifications
5. Mark individual notifications as read
6. Test "Mark All Read" functionality
7. Test "Clear All" functionality
8. Click on notification to verify action URL navigation
9. Verify toast notifications auto-dismiss
10. Test responsive design on mobile
11. Check gaming theme consistency

**This should take 6-7 hours to implement and test thoroughly.**