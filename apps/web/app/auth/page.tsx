'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { RegisterForm } from '@/components/auth/RegisterForm';

function AuthPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();
  
  // Get initial mode from URL params or default to login
  const initialMode = searchParams?.get('mode') || 'login';
  const [mode, setMode] = useState<'login' | 'register'>(
    initialMode === 'register' ? 'register' : 'login'
  );

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const redirectTo = searchParams?.get('redirect') || '/dashboard';
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, router, searchParams]);

  const handleAuthSuccess = () => {
    const redirectTo = searchParams?.get('redirect') || '/dashboard';
    router.push(redirectTo);
  };

  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-3xl font-pixel text-primary animate-px-glow mb-2">
            🎆 SERAAJ 🎆
          </div>
          <div className="text-sm text-white font-pixel">⏳ LOADING QUEST...</div>
        </div>
      </main>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary dark:text-neon-cyan mb-2 animate-px-glow">
            🎆 SERAAJ 🎆
          </h1>
          <div className="text-lg font-pixel text-pixel-coral dark:text-neon-pink mb-2">
            8-BIT HERO LOGIN
          </div>
          <p className="text-sm text-white">
            🚀 Join the quest to change the world!
          </p>
        </div>

        {mode === 'login' ? (
          <LoginForm
            onSuccess={handleAuthSuccess}
            onSwitchToRegister={() => setMode('register')}
          />
        ) : (
          <RegisterForm
            onSuccess={handleAuthSuccess}
            onSwitchToLogin={() => setMode('login')}
          />
        )}
      </div>
    </main>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-3xl font-pixel text-primary animate-px-glow mb-2">
            🎆 SERAAJ 🎆
          </div>
          <div className="text-sm text-white font-pixel">⏳ LOADING QUEST...</div>
        </div>
      </main>
    }>
      <AuthPageContent />
    </Suspense>
  );
}