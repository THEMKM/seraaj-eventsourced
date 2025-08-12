'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@seraaj/sdk-bff';

export interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  fallbackPath?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  fallbackPath = '/auth'
}: ProtectedRouteProps) {
  const { isAuthenticated, user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        // Redirect to auth with current path as return URL
        const redirectUrl = `${fallbackPath}?redirect=${encodeURIComponent(pathname)}`;
        router.push(redirectUrl);
        return;
      }

      if (requiredRole && user?.role !== requiredRole) {
        // User doesn't have required role, redirect to dashboard
        router.push('/dashboard');
        return;
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRole, router, pathname, fallbackPath]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-pixel text-sunBurst animate-pxGlow mb-4">
            SERAAJ
          </div>
          <div className="text-sm text-white font-pixel">LOADING...</div>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated or wrong role
  if (!isAuthenticated || (requiredRole && user?.role !== requiredRole)) {
    return null;
  }

  return <>{children}</>;
}