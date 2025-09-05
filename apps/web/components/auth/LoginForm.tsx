'use client';

import React, { useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';

export interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  onForgotPassword?: () => void;
}

export function LoginForm({ onSuccess, onSwitchToRegister, onForgotPassword }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const { showSuccess, showError } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isAttempting, setIsAttempting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsAttempting(true);

    // Client-side validation
    if (!email?.trim()) {
      setError('Please enter your email address');
      setIsAttempting(false);
      return;
    }

    if (!password?.trim()) {
      setError('Please enter your password');
      setIsAttempting(false);
      return;
    }

    // Basic email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      setIsAttempting(false);
      return;
    }

    try {
      await login(email.trim(), password);
      showSuccess('🎆 Welcome back, hero! Ready for your next quest?');
      onSuccess?.();
    } catch (err) {
      console.error('Login failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.';
      setError(errorMessage);
      showError(`❌ ${errorMessage}`);
    } finally {
      setIsAttempting(false);
    }
  };

  return (
    <PxCard variant="default" className="w-full max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
            🔑 HERO LOGIN 🔑
          </h2>
          <p className="text-sm text-ink dark:text-white">
            Ready to continue your quest?
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <PxInput
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="volunteer@example.com"
            required
          />

          <PxInput
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

          {error && (
            <div className="clip-px border-px border-error bg-error/10 p-3 animate-pulse">
              <p className="text-xs text-error font-pixel">❌ {error}</p>
              {error.toLowerCase().includes('invalid') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Make sure you're using the correct email and password
                </p>
              )}
              {error.toLowerCase().includes('network') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Check your internet connection and try again
                </p>
              )}
              {error.toLowerCase().includes('server') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Our servers are having issues. Please wait a moment
                </p>
              )}
            </div>
          )}

          <PxButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full transition-all duration-200"
            disabled={isLoading || isAttempting || !email?.trim() || !password?.trim()}
          >
            {isLoading || isAttempting ? '⏳ LOGGING IN...' : '🚀 START QUEST'}
          </PxButton>

          {(isLoading || isAttempting) && (
            <div className="text-center">
              <p className="text-xs text-ink dark:text-white font-pixel">
                🎆 Checking your credentials...
              </p>
            </div>
          )}
        </form>

        <div className="text-center space-y-3">
          <p className="text-xs text-ink dark:text-white mb-2">
            🎆 New hero? Join the guild!
          </p>
          <PxButton
            variant="secondary"
            size="sm"
            onClick={onSwitchToRegister}
          >
            ✨ REGISTER
          </PxButton>
          
          <div className="border-t border-ink/20 dark:border-dark-border pt-3">
            <p className="text-xs text-ink dark:text-white mb-2">
              🔒 Forgot your quest password?
            </p>
            <PxButton
              variant="secondary"
              size="sm"
              onClick={onForgotPassword}
              className="text-xs"
            >
              🚨 RESET PASSWORD
            </PxButton>
          </div>
        </div>
      </div>
    </PxCard>
  );
}