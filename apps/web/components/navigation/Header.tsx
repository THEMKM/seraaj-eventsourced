'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { PxButton } from '@seraaj/ui';
import { AvatarDisplay } from '@/components/avatar/AvatarSelector';
import { AvatarConfig, AvatarClass, AvatarPose, calculateAvatarClass } from '@/components/avatar/AvatarSystem';

export function Header() {
  const { isAuthenticated, user, logout, isLoading } = useAuth();

  // Create basic avatar configuration for header
  const headerAvatarConfig: AvatarConfig = {
    class: AvatarClass.HERO,
    level: 1,
    pose: AvatarPose.DEFAULT,
    accessories: []
  };

  return (
    <header className="bg-deep-indigo clip-px border-px border-electric-teal shadow-px">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-pixel text-primary dark:text-neon-cyan hover:animate-px-glow">
              🎆 SERAAJ 🎆
            </h1>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {isAuthenticated && (
              <>
                <Link 
                  href="/dashboard" 
                  className="text-sm text-white hover:text-primary font-pixel transition-colors duration-200"
                >
                  🏆 DASHBOARD
                </Link>
                <Link 
                  href="/opportunities" 
                  className="text-sm text-white hover:text-primary font-pixel transition-colors duration-200"
                >
                  🎯 OPPORTUNITIES
                </Link>
                <Link 
                  href="/feed" 
                  className="text-sm text-white hover:text-primary font-pixel transition-colors duration-200"
                >
                  🎆 QUESTS
                </Link>
                <Link 
                  href="/profile" 
                  className="text-sm text-white hover:text-primary font-pixel transition-colors duration-200"
                >
                  👤 PROFILE
                </Link>
              </>
            )}
          </nav>

          {/* Auth Section */}
          <div className="flex items-center space-x-4">
            {isLoading ? (
              <div className="text-xs text-white font-pixel">⏳ LOADING...</div>
            ) : isAuthenticated && user ? (
              <div className="flex items-center space-x-3">
                <AvatarDisplay
                  config={headerAvatarConfig}
                  size="sm"
                  showLevel={false}
                  clickable={false}
                  className="animate-pulse-slow"
                />
                <span className="text-xs text-primary font-pixel">
                  🎉 {user.name?.toUpperCase()}
                </span>
                <PxButton
                  variant="secondary"
                  size="sm"
                  onClick={logout}
                >
                  🚪 LOGOUT
                </PxButton>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link href="/auth?mode=login">
                  <PxButton variant="secondary" size="sm">
                    🔑 LOGIN
                  </PxButton>
                </Link>
                <Link href="/auth?mode=register">
                  <PxButton variant="primary" size="sm">
                    ✨ JOIN
                  </PxButton>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}