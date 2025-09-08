'use client';

import React, { useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { useToast } from '@/contexts/ToastContext';
import { authApi } from '@/lib/bff';

export interface ForgotPasswordFormProps {
  onBackToLogin?: () => void;
}

export function ForgotPasswordForm({ onBackToLogin }: ForgotPasswordFormProps) {
  const { showSuccess, showError } = useToast();
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('Please enter your email address');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    if (!newPassword || newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsSubmitting(true);
    try {
      // TODO(security): Temporary, insecure reset – replace with token-based flow
      await authApi.resetPassword({ email: trimmedEmail, newPassword });
      setIsSubmitted(true);
      showSuccess('Password updated. You can sign in now.');
    } catch (err: any) {
      console.error('Reset password failed:', err);
      // If BFF doesn’t have the route yet (404), fall back to Auth directly
      const status = (err as any)?.status;
      if (status === 404) {
        try {
          const base = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8004';
          const resp = await fetch(`${base}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: trimmedEmail, newPassword })
          });
          if (!resp.ok) {
            const data = await resp.json().catch(() => ({} as any));
            throw new Error(data?.detail || data?.message || `Reset failed (HTTP ${resp.status})`);
          }
          setIsSubmitted(true);
          showSuccess('Password updated. You can sign in now.');
        } catch (e: any) {
          const message = e?.message || 'Unable to reset password. Please try again.';
          setError(message);
          showError(message);
        }
      } else {
        const message = err?.message || 'Unable to reset password. Please try again.';
        setError(message);
        showError(message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <PxCard variant="default" className="w-full max-w-md mx-auto">
        <div className="space-y-6 text-center">
          <div>
            <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
              PASSWORD RESET
            </h2>
            <p className="text-sm text-ink dark:text-white mb-4">
              Success! Your password for <span className="font-pixel text-primary dark:text-neon-cyan">{email}</span> has been updated.
            </p>
          </div>

          <div className="clip-px border-px border-warning bg-warning/10 p-3">
            <p className="text-xs text-warning font-pixel mb-1">TODO(security)</p>
            <p className="text-xs text-ink dark:text-white">
              This reset method is temporary and insecure. It will be replaced with a secure, token-based flow.
            </p>
          </div>

          <div className="space-y-3">
            <PxButton
              variant="primary"
              size="lg"
              className="w-full"
              onClick={onBackToLogin}
            >
              SIGN IN
            </PxButton>
          </div>
        </div>
      </PxCard>
    );
  }

  return (
    <PxCard variant="default" className="w-full max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
            RESET PASSWORD
          </h2>
          <p className="text-sm text-ink dark:text-white">
            Set a new password for your account
          </p>
        </div>

        <div className="clip-px border-px border-warning bg-warning/10 p-3">
          <p className="text-xs text-warning font-pixel mb-1">TODO(security)</p>
          <p className="text-xs text-ink dark:text-white">
            Temporary, insecure reset (email + new password). Will be replaced with a token-based flow.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <PxInput
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="hero@example.com"
            required
          />

          <PxInput
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 8 characters"
            minLength={8}
            required
          />

          <PxInput
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter new password"
            minLength={8}
            required
          />

          {error && (
            <div className="clip-px border-px border-error bg-error/10 p-3 animate-pulse">
              <p className="text-xs text-error font-pixel">{error}</p>
            </div>
          )}

          <PxButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full transition-all duration-200"
            disabled={isSubmitting || !email?.trim() || !newPassword || !confirmPassword}
          >
            {isSubmitting ? 'RESETTING...' : 'RESET PASSWORD'}
          </PxButton>

          {isSubmitting && (
            <div className="text-center">
              <p className="text-xs text-ink dark:text-white font-pixel">
                Updating your password...
              </p>
            </div>
          )}
        </form>

        <div className="text-center">
          <p className="text-xs text-ink dark:text-white mb-2">
            Remembered your password?
          </p>
          <PxButton
            variant="secondary"
            size="sm"
            onClick={onBackToLogin}
          >
            BACK TO LOGIN
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
}
