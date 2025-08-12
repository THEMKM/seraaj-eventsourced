'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { PxButton } from '@seraaj/ui';

export function Header() {
  const { isAuthenticated, user, logout, isLoading } = useAuth();

  return (
    <header className="bg-deepIndigo border-b-2 border-electricTeal">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-pixel text-sunBurst hover:animate-pxGlow">
              SERAAJ
            </h1>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {isAuthenticated && (
              <>
                <Link 
                  href="/dashboard" 
                  className="text-sm text-white hover:text-sunBurst font-pixel"
                >
                  DASHBOARD
                </Link>
                <Link 
                  href="/opportunities" 
                  className="text-sm text-white hover:text-sunBurst font-pixel"
                >
                  OPPORTUNITIES
                </Link>
                <Link 
                  href="/matches" 
                  className="text-sm text-white hover:text-sunBurst font-pixel"
                >
                  MATCHES
                </Link>
              </>
            )}
          </nav>

          {/* Auth Section */}
          <div className="flex items-center space-x-4">
            {isLoading ? (
              <div className="text-xs text-white font-pixel">LOADING...</div>
            ) : isAuthenticated && user ? (
              <div className="flex items-center space-x-4">
                <span className="text-xs text-white font-pixel">
                  Hello, {user.name}
                </span>
                <PxButton
                  variant="secondary"
                  size="sm"
                  onClick={logout}
                >
                  LOGOUT
                </PxButton>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link href="/auth?mode=login">
                  <PxButton variant="secondary" size="sm">
                    LOGIN
                  </PxButton>
                </Link>
                <Link href="/auth?mode=register">
                  <PxButton variant="primary" size="sm">
                    REGISTER
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