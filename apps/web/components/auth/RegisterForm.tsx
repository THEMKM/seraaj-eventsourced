'use client';

import React, { useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { PxSelect } from '@/components/forms/PxSelect';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@seraaj/sdk-bff';

export interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: UserRole.VOLUNTEER as UserRole
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await register(formData.name, formData.email, formData.password, formData.role as UserRole.VOLUNTEER | UserRole.ORG_ADMIN);
      onSuccess?.();
    } catch (err) {
      console.error('Registration failed:', err);
      setErrors({ 
        general: err instanceof Error ? err.message : 'Registration failed' 
      });
    }
  };

  const updateFormData = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <PxCard variant="default" className="w-full max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-pixel text-sunBurst mb-2">REGISTER</h2>
          <p className="text-sm text-white">Join the Seraaj community</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <PxInput
            label="Full Name"
            value={formData.name}
            onChange={(e) => updateFormData('name', e.target.value)}
            placeholder="John Doe"
            error={errors.name}
            required
          />

          <PxInput
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => updateFormData('email', e.target.value)}
            placeholder="volunteer@example.com"
            error={errors.email}
            required
          />

          <PxSelect
            label="I want to..."
            value={formData.role}
            onChange={(e) => updateFormData('role', e.target.value)}
            options={[
              { value: UserRole.VOLUNTEER, label: 'Find volunteer opportunities' },
              { value: UserRole.ORG_ADMIN, label: 'Manage an organization' }
            ]}
          />

          <PxInput
            label="Password"
            type="password"
            value={formData.password}
            onChange={(e) => updateFormData('password', e.target.value)}
            placeholder="Minimum 8 characters"
            error={errors.password}
            required
          />

          <PxInput
            label="Confirm Password"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => updateFormData('confirmPassword', e.target.value)}
            placeholder="Confirm your password"
            error={errors.confirmPassword}
            required
          />

          {errors.general && (
            <div className="p-3 border-2 border-error bg-error/10 rounded">
              <p className="text-xs text-error font-pixel">{errors.general}</p>
            </div>
          )}

          <PxButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
          </PxButton>
        </form>

        <div className="text-center">
          <p className="text-xs text-white mb-2">Already have an account?</p>
          <PxButton
            variant="secondary"
            size="sm"
            onClick={onSwitchToLogin}
          >
            LOGIN
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
}