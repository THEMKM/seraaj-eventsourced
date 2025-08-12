'use client';

import React, { useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { useAuth } from '@/contexts/AuthContext';

export interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export function LoginForm({ onSuccess, onSwitchToRegister }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    try {
      await login(email, password);
      onSuccess?.();
    } catch (err) {
      console.error('Login failed:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <PxCard variant="default" className="w-full max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-pixel text-sunBurst mb-2">LOGIN</h2>
          <p className="text-sm text-white">Welcome back to Seraaj</p>
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
            <div className="p-3 border-2 border-error bg-error/10 rounded">
              <p className="text-xs text-error font-pixel">{error}</p>
            </div>
          )}

          <PxButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'LOGGING IN...' : 'LOGIN'}
          </PxButton>
        </form>

        <div className="text-center">
          <p className="text-xs text-white mb-2">Don&apos;t have an account?</p>
          <PxButton
            variant="secondary"
            size="sm"
            onClick={onSwitchToRegister}
          >
            REGISTER
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
}