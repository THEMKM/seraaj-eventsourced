'use client';

import React, { useState } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { PxSelect } from '@/components/forms/PxSelect';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { UserRole } from '@seraaj/sdk-bff';

export interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const { register, isLoading } = useAuth();
  const { showSuccess, showError } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: UserRole.VOLUNTEER as UserRole
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isAttempting, setIsAttempting] = useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Please enter your full name';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters long';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Please enter your email address';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address (e.g., hero@example.com)';
    }

    if (!formData.password) {
      newErrors.password = 'Please create a password';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters long';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter, one lowercase letter, and one number.';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsAttempting(true);
    
    if (!validateForm()) {
      setIsAttempting(false);
      return;
    }

    try {
      await register(
        formData.name.trim(), 
        formData.email.trim(), 
        formData.password, 
        formData.role as UserRole.VOLUNTEER | UserRole.ORG_ADMIN
      );
      showSuccess('🎆 Welcome to the guild, hero! Your quest begins now!');
      onSuccess?.();
    } catch (err: any) {
      console.error('Registration failed:', err);
      
      // Enhanced error handling with specific cause information
      let errorMessage = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      
      // Make validation errors more user-friendly
      if (errorMessage.includes('Validation failed:')) {
        // Transform technical validation messages to user-friendly ones
        errorMessage = errorMessage.replace('Validation failed:', 'Please fix:')
          .replace('password: String should have at least 8 characters', 'Password: Must be at least 8 characters')
          .replace('name: String should have at least 1 character', 'Name: Please enter your name')
          .replace('email: String should have at least 1 character', 'Email: Please enter your email');
      }
      
      setErrors({ general: errorMessage });
      showError(`❌ ${errorMessage}`);
    } finally {
      setIsAttempting(false);
    }
  };

  const updateFormData = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    // Clear general error when user makes changes
    if (errors.general) {
      setErrors(prev => ({ ...prev, general: '' }));
    }
  };

  return (
    <PxCard variant="default" className="w-full max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
            🎆 CREATE HERO 🎆
          </h2>
          <p className="text-sm text-ink dark:text-white">
            Begin your epic volunteering adventure!
          </p>
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
              { value: UserRole.VOLUNTEER, label: '🎆 Become a Hero (Volunteer)' },
              { value: UserRole.ORG_ADMIN, label: '🏰 Create a Guild (Organization)' }
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
            <div className="clip-px border-px border-error bg-error/10 p-3 animate-pulse">
              <p className="text-xs text-error font-pixel">❌ {errors.general}</p>
              {errors.general.toLowerCase().includes('email already') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Click "LOGIN" below to access your existing account
                </p>
              )}
              {errors.general.toLowerCase().includes('password') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Use 8+ characters with letters, numbers, or symbols
                </p>
              )}
              {errors.general.toLowerCase().includes('network') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Check your internet connection and try again
                </p>
              )}
              {errors.general.toLowerCase().includes('server') && (
                <p className="text-xs text-error/80 mt-1">
                  💡 Tip: Our servers are busy. Please wait a moment and try again
                </p>
              )}
            </div>
          )}

          {/* Form validation summary */}
          {Object.keys(errors).length > 0 && !errors.general && (
            <div className="clip-px border-px border-warning bg-warning/10 p-3">
              <p className="text-xs text-warning font-pixel">
                ⚠️ Please fix the highlighted fields above
              </p>
            </div>
          )}

          <PxButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full transition-all duration-200"
            disabled={
              isLoading || 
              isAttempting || 
              !formData.name.trim() || 
              !formData.email.trim() || 
              !formData.password || 
              !formData.confirmPassword
            }
          >
            {isLoading || isAttempting ? '⏳ SPAWNING HERO...' : '✨ CREATE HERO'}
          </PxButton>

          {(isLoading || isAttempting) && (
            <div className="text-center">
              <p className="text-xs text-ink dark:text-white font-pixel">
                🎆 Creating your hero profile...
              </p>
            </div>
          )}

          {/* Password strength indicator */}
          {formData.password && (
            <div className="space-y-1">
              <p className="text-xs font-pixel text-ink dark:text-white">
                🛡️ Password Strength:
              </p>
              <div className="flex space-x-1">
                <div className={`h-1 w-full clip-px ${formData.password.length >= 8 ? 'bg-success' : 'bg-error'}`}></div>
                <div className={`h-1 w-full clip-px ${/(?=.*[a-z])(?=.*[A-Z])/.test(formData.password) ? 'bg-success' : 'bg-error'}`}></div>
                <div className={`h-1 w-full clip-px ${/(?=.*\d)/.test(formData.password) ? 'bg-success' : 'bg-error'}`}></div>
                <div className={`h-1 w-full clip-px ${/(?=.*[@$!%*?&])/.test(formData.password) ? 'bg-success' : 'bg-warning'}`}></div>
              </div>
              <p className="text-xs text-ink/60 dark:text-white/60">
                8+ chars • Letters • Numbers • Symbols (optional)
              </p>
            </div>
          )}
        </form>

        <div className="text-center">
          <p className="text-xs text-ink dark:text-white mb-2">
            🔑 Already a hero? Continue your quest!
          </p>
          <PxButton
            variant="secondary"
            size="sm"
            onClick={onSwitchToLogin}
          >
            🚀 LOGIN
          </PxButton>
        </div>
      </div>
    </PxCard>
  );
}